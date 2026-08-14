<template>
  <main class="mobile-home">
    <section class="app-hero">
      <div class="hero-topbar">
        <div>
          <p class="eyebrow">ANYGO</p>
          <h1>把旅行灵感装进口袋</h1>
        </div>
        <a-select v-model:value="locale" class="locale-select" size="small">
          <a-select-option value="zh-CN">中</a-select-option>
          <a-select-option value="en-US">EN</a-select-option>
          <a-select-option value="ja-JP">日</a-select-option>
        </a-select>
      </div>
      <p class="hero-copy">输入城市、日期和偏好，Anygo 会结合小红书灵感、天气、酒店和地图信息生成一份可执行的手机行程。</p>
      <div class="hero-stats">
        <span>{{ totalDays }} 天</span>
        <span>{{ formData.cities.length }} 城市</span>
        <span>{{ formData.preferences.length || 0 }} 偏好</span>
      </div>
    </section>

    <section class="phone-panel">
      <a-form :model="formData" layout="vertical" @finish="handleSubmit">
        <div class="form-block">
          <div class="block-title">
            <span>01</span>
            <h2>目的地</h2>
          </div>

          <div class="city-stack">
            <div v-for="(cityStay, index) in formData.cities" :key="index" class="city-item">
              <a-input
                v-model:value="cityStay.city"
                size="large"
                :placeholder="index === 0 ? '想去哪座城市？例如：长沙' : '下一座城市'"
              />
              <a-input-number v-model:value="cityStay.days" :min="1" :max="15" size="large" />
              <button v-if="formData.cities.length > 1" class="icon-button" type="button" @click="removeCity(index)">×</button>
            </div>
          </div>

          <button type="button" class="ghost-button" @click="addCity">添加城市</button>
        </div>

        <div class="form-block">
          <div class="block-title">
            <span>02</span>
            <h2>时间和方式</h2>
          </div>
          <a-date-picker
            v-model:value="formData.start_date"
            size="large"
            class="full-control"
            placeholder="选择出发日期"
          />
          <div class="split-grid">
            <a-select v-model:value="formData.transportation" size="large">
              <a-select-option value="公共交通">公共交通</a-select-option>
              <a-select-option value="自驾">自驾</a-select-option>
              <a-select-option value="步行">步行</a-select-option>
              <a-select-option value="混合">混合</a-select-option>
            </a-select>
            <a-select v-model:value="formData.accommodation" size="large">
              <a-select-option value="经济型酒店">经济酒店</a-select-option>
              <a-select-option value="舒适型酒店">舒适酒店</a-select-option>
              <a-select-option value="豪华酒店">豪华酒店</a-select-option>
              <a-select-option value="民宿">民宿</a-select-option>
            </a-select>
          </div>
        </div>

        <div class="form-block">
          <div class="block-title">
            <span>03</span>
            <h2>旅行偏好</h2>
          </div>
          <div class="chips">
            <button
              v-for="item in interestOptions"
              :key="item"
              type="button"
              class="chip"
              :class="{ active: formData.preferences.includes(item) }"
              @click="togglePreference(item)"
            >
              {{ item }}
            </button>
          </div>
          <a-textarea
            v-model:value="formData.free_text_input"
            class="notes-input"
            :rows="4"
            placeholder="补充你的旅行口味，比如：不要太赶、想吃夜市、适合拍照。"
          />
        </div>

        <button class="primary-button" type="submit" :disabled="loading">
          <span v-if="!loading">生成手机行程</span>
          <span v-else>正在规划 {{ loadingProgress }}%</span>
        </button>
      </a-form>
    </section>

    <section v-if="loading" class="progress-sheet">
      <div class="progress-card">
        <div class="progress-head">
          <span>Plan {{ planCode || '...' }}</span>
          <strong>{{ loadingProgress }}%</strong>
        </div>
        <a-progress :percent="loadingProgress" :show-info="false" stroke-color="#1f8a70" />
        <p>{{ loadingStatus || '多智能体正在收集旅行素材...' }}</p>
      </div>
    </section>

    <section class="history-panel">
      <div class="section-heading">
        <h2>最近计划</h2>
        <button type="button" @click="loadHistoryPlans">刷新</button>
      </div>
      <div v-if="historyLoading" class="empty-state">正在读取...</div>
      <div v-else-if="historyPlans.length === 0" class="empty-state">还没有历史行程</div>
      <template v-else>
        <button
          v-for="item in historyPlans"
          :key="item.plan_id"
          class="history-item"
          type="button"
          @click="openHistoryPlan(item.plan_id)"
        >
          <span>{{ item.city }}</span>
          <small>{{ item.start_date }} · {{ item.travel_days }} 天</small>
        </button>
      </template>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs, { Dayjs } from 'dayjs'
import { useI18n } from 'vue-i18n'
import { generateTripPlan, getTripHistory } from '@/services/api'
import { setAppLocale, type AppLocale } from '@/i18n'
import type { CityStay, TripFormData, TripHistoryItem, TripTaskStage } from '@/types'

const router = useRouter()
const { locale } = useI18n()

const interestOptions = ['美食', '自然风景', '历史文化', '亲子', '拍照', '博物馆', '夜生活', '小众路线']

const formData = reactive({
  cities: [{ city: '', days: 3 }] as CityStay[],
  start_date: null as Dayjs | null,
  transportation: '公共交通',
  accommodation: '舒适型酒店',
  preferences: ['美食'] as string[],
  free_text_input: '',
})

const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')
const planCode = ref('')
const historyLoading = ref(false)
const historyPlans = ref<TripHistoryItem[]>([])

const totalDays = computed(() => formData.cities.reduce((sum, item) => sum + Number(item.days || 1), 0))
const computedEndDate = computed(() => {
  if (!formData.start_date) return null
  return formData.start_date.add(Math.max(totalDays.value - 1, 0), 'day')
})

watch(locale, (nextLocale) => setAppLocale(nextLocale as AppLocale), { immediate: true })

const addCity = () => {
  formData.cities.push({ city: '', days: 2 })
}

const removeCity = (index: number) => {
  formData.cities.splice(index, 1)
}

const togglePreference = (value: string) => {
  const index = formData.preferences.indexOf(value)
  if (index >= 0) formData.preferences.splice(index, 1)
  else formData.preferences.push(value)
}

const getCurrentLocale = () => {
  const current = String(locale.value || 'zh-CN').toLowerCase()
  if (current.startsWith('en')) return 'en'
  if (current.startsWith('ja')) return 'ja'
  return 'zh'
}

const getStageStatusText = (stage: TripTaskStage) => {
  const map: Record<string, string> = {
    submitted: '任务已提交',
    initializing: '正在初始化多智能体',
    attraction_search: '正在搜索景点灵感',
    weather_search: '正在查询天气',
    hotel_search: '正在查找酒店',
    planning: '正在生成行程',
    graph_building: '正在整理知识图谱',
    completed: '行程已完成',
  }
  return map[stage] || '正在规划...'
}

const openHistoryPlan = (planId: string) => {
  sessionStorage.removeItem('tripPlan')
  sessionStorage.removeItem('graphData')
  sessionStorage.setItem('planId', planId)
  router.push({ path: '/result', query: { plan_id: planId } })
}

const loadHistoryPlans = async () => {
  historyLoading.value = true
  try {
    historyPlans.value = await getTripHistory(8)
  } catch (error: any) {
    historyPlans.value = []
    message.error(error.message || '读取历史计划失败')
  } finally {
    historyLoading.value = false
  }
}

const handleSubmit = async () => {
  const citiesPayload = formData.cities
    .map((item) => ({ city: item.city.trim(), days: Number(item.days || 1) }))
    .filter((item) => item.city)

  if (citiesPayload.length === 0) {
    message.error('先告诉我你想去哪座城市')
    return
  }
  if (!formData.start_date || !computedEndDate.value) {
    message.error('请选择出发日期')
    return
  }
  if (totalDays.value > 30) {
    message.warning('行程最多支持 30 天')
    return
  }

  loading.value = true
  loadingProgress.value = 5
  loadingStatus.value = '正在提交任务...'
  planCode.value = ''

  try {
    sessionStorage.removeItem('tripPlan')
    sessionStorage.removeItem('graphData')
    sessionStorage.removeItem('planId')

    const requestData: TripFormData = {
      city: citiesPayload[0].city,
      cities: citiesPayload,
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: computedEndDate.value.format('YYYY-MM-DD'),
      travel_days: totalDays.value,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input,
      language: getCurrentLocale(),
    }

    const response = await generateTripPlan(requestData, {
      onTaskCreated: (task) => {
        planCode.value = task.plan_id || task.task_id
      },
      onTaskEvent: (event) => {
        planCode.value = event.plan_id || planCode.value
        loadingProgress.value = Math.max(0, Math.min(100, Number(event.progress || 0)))
        loadingStatus.value = event.message || getStageStatusText(event.stage)
      },
    })

    if (!response.success || !response.data) {
      throw new Error(response.message || '行程生成失败')
    }

    const planId = response.plan_id || planCode.value
    sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
    if (response.graph_data) sessionStorage.setItem('graphData', JSON.stringify(response.graph_data))
    if (planId) sessionStorage.setItem('planId', planId)
    loadingProgress.value = 100
    message.success('行程已生成')
    await router.push({ path: '/result', query: planId ? { plan_id: planId } : {} })
  } catch (error: any) {
    message.error(error.message || '生成失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  formData.start_date = dayjs().add(7, 'day')
  void loadHistoryPlans()
})
</script>

<style scoped>
.mobile-home {
  min-height: 100vh;
  padding: 18px 16px 40px;
  background:
    radial-gradient(circle at 12% 0%, rgba(98, 171, 255, 0.38), transparent 30%),
    radial-gradient(circle at 100% 8%, rgba(191, 158, 255, 0.36), transparent 28%),
    linear-gradient(180deg, rgba(250, 253, 255, 0.72) 0%, rgba(238, 245, 252, 0.76) 100%);
  color: #152033;
}

.app-hero {
  min-height: 248px;
  padding: 22px;
  border-radius: 34px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(19, 35, 62, 0.64)),
    url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80') center/cover;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid rgba(255, 255, 255, 0.58);
  box-shadow: 0 28px 70px rgba(68, 96, 128, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.62);
  overflow: hidden;
  position: relative;
}

.app-hero::after {
  content: "";
  position: absolute;
  inset: 1px;
  border-radius: 32px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.34), transparent 36%);
  pointer-events: none;
}

.hero-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  opacity: 0.8;
  position: relative;
  z-index: 1;
}

.app-hero h1 {
  max-width: 280px;
  margin: 0;
  font-size: 34px;
  line-height: 1.05;
  font-weight: 850;
  letter-spacing: -0.02em;
  position: relative;
  z-index: 1;
}

.hero-copy {
  margin: 28px 0 0;
  font-size: 15px;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.88);
  position: relative;
  z-index: 1;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 18px;
  position: relative;
  z-index: 1;
}

.hero-stats span {
  padding: 10px 8px;
  background: rgba(255, 255, 255, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.34);
  border-radius: 18px;
  backdrop-filter: blur(18px) saturate(150%);
  text-align: center;
  font-size: 13px;
  font-weight: 700;
}

.locale-select {
  width: 72px;
}

.phone-panel,
.history-panel {
  margin-top: 14px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: 30px;
  box-shadow: 0 22px 60px rgba(70, 101, 135, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.74);
  backdrop-filter: blur(28px) saturate(160%);
}

.form-block + .form-block {
  margin-top: 20px;
}

.block-title,
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.block-title span {
  color: #007aff;
  font-size: 12px;
  font-weight: 900;
}

.block-title h2,
.section-heading h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 850;
}

.city-stack {
  display: grid;
  gap: 10px;
}

.city-item {
  display: grid;
  grid-template-columns: 1fr 86px 38px;
  gap: 8px;
  align-items: center;
}

.icon-button,
.ghost-button,
.section-heading button {
  border: 1px solid rgba(255, 255, 255, 0.74);
  background: rgba(255, 255, 255, 0.56);
  color: #334155;
  height: 38px;
  font-weight: 800;
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72), 0 10px 24px rgba(64, 86, 112, 0.08);
  backdrop-filter: blur(18px);
}

.icon-button {
  font-size: 22px;
}

.ghost-button {
  width: 100%;
  margin-top: 10px;
}

.full-control {
  width: 100%;
}

.split-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 10px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.52);
  color: #334155;
  font-weight: 750;
  border-radius: 999px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(18px);
}

.chip.active {
  border-color: rgba(0, 122, 255, 0.38);
  background: rgba(0, 122, 255, 0.14);
  color: #005ecb;
}

.notes-input {
  margin-top: 12px;
}

.primary-button {
  position: sticky;
  bottom: 14px;
  z-index: 10;
  width: 100%;
  height: 54px;
  margin-top: 22px;
  border: 0;
  border-radius: 22px;
  background: linear-gradient(180deg, #2f95ff 0%, #007aff 100%);
  color: #fff;
  font-size: 16px;
  font-weight: 900;
  box-shadow: 0 18px 36px rgba(0, 122, 255, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.32);
}

.primary-button:disabled {
  opacity: 0.72;
}

.progress-sheet {
  position: fixed;
  inset: auto 12px 12px;
  z-index: 50;
}

.progress-card {
  padding: 16px;
  background: rgba(18, 30, 48, 0.72);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 26px;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(30px) saturate(170%);
}

.progress-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-card p {
  margin: 10px 0 0;
  color: rgba(255, 255, 255, 0.78);
}

.history-panel {
  margin-bottom: 24px;
}

.history-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 14px 0;
  border: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  background: transparent;
  color: #152033;
  text-align: left;
}

.history-item span {
  font-size: 16px;
  font-weight: 850;
}

.history-item small,
.empty-state {
  color: #6d7478;
}

:deep(.ant-input),
:deep(.ant-input-number),
:deep(.ant-input-number-input),
:deep(.ant-picker),
:deep(.ant-select-selector) {
  border-radius: 18px !important;
}

:deep(.ant-input),
:deep(.ant-input-number),
:deep(.ant-picker),
:deep(.ant-select-selector),
:deep(.ant-input-affix-wrapper) {
  background: rgba(255, 255, 255, 0.58) !important;
  border-color: rgba(255, 255, 255, 0.78) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72), 0 10px 24px rgba(64, 86, 112, 0.07) !important;
  backdrop-filter: blur(18px);
}

@media (min-width: 720px) {
  .mobile-home {
    max-width: 480px;
    margin: 0 auto;
  }
}
</style>
