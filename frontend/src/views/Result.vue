<template>
  <main class="mobile-result">
    <section v-if="loading" class="loading-state">
      <a-spin size="large" />
      <p>正在读取行程...</p>
    </section>

    <section v-else-if="!tripPlan" class="empty-result">
      <h1>没有找到行程</h1>
      <p>可能是缓存已清空，或者这个计划还没有生成完成。</p>
      <button type="button" @click="goHome">重新规划</button>
    </section>

    <template v-else>
      <header class="result-hero">
        <button class="back-button" type="button" @click="goHome">返回</button>
        <p class="eyebrow">ANYGO PLAN</p>
        <h1>{{ displayCity }}</h1>
        <div class="hero-meta">
          <span>{{ tripPlan.start_date }} 至 {{ tripPlan.end_date }}</span>
          <span>{{ tripPlan.days.length }} 天</span>
          <span v-if="planId">ID {{ planId }}</span>
        </div>
        <p v-if="tripPlan.overall_suggestions" class="hero-copy">{{ tripPlan.overall_suggestions }}</p>
      </header>

      <nav class="quick-tabs">
        <a href="#days">日程</a>
        <a v-if="tripPlan.budget" href="#budget">预算</a>
        <a v-if="tripPlan.weather_info?.length" href="#weather">天气</a>
      </nav>

      <section v-if="tripPlan.budget" id="budget" class="summary-card">
        <div class="section-title">
          <span>预算</span>
          <strong>¥{{ formatAmount(tripPlan.budget.total) }}</strong>
        </div>
        <div class="budget-grid">
          <div>
            <small>景点</small>
            <b>¥{{ formatAmount(tripPlan.budget.total_attractions) }}</b>
          </div>
          <div>
            <small>酒店</small>
            <b>¥{{ formatAmount(tripPlan.budget.total_hotels) }}</b>
          </div>
          <div>
            <small>餐饮</small>
            <b>¥{{ formatAmount(tripPlan.budget.total_meals) }}</b>
          </div>
          <div>
            <small>交通</small>
            <b>¥{{ formatAmount((tripPlan.budget.total_transportation || 0) + (tripPlan.budget.total_inter_city_transport || 0)) }}</b>
          </div>
        </div>
      </section>

      <section v-if="tripPlan.weather_info?.length" id="weather" class="weather-strip">
        <article v-for="weather in tripPlan.weather_info" :key="`${weather.date}-${weather.city}`">
          <small>{{ weather.date }}</small>
          <strong>{{ weather.city || tripPlan.city }}</strong>
          <span>{{ weather.day_weather }} / {{ weather.night_weather }}</span>
          <b>{{ weather.day_temp }}° / {{ weather.night_temp }}°</b>
        </article>
      </section>

      <section id="days" class="day-list">
        <article v-for="day in tripPlan.days" :key="day.day_index" class="day-card">
          <div class="day-head">
            <div>
              <small>DAY {{ day.day_index + 1 }} · {{ day.date }}</small>
              <h2>{{ day.city || tripPlan.city }}</h2>
            </div>
            <span v-if="day.is_transfer_day" class="transfer-badge">换城</span>
          </div>

          <p class="day-desc">{{ day.description }}</p>
          <p v-if="day.transfer_info" class="transfer-info">{{ day.transfer_info }}</p>

          <div class="mini-row">
            <span>{{ day.transportation }}</span>
            <span>{{ day.accommodation }}</span>
          </div>

          <div v-if="day.hotel" class="hotel-card">
            <small>今晚住宿</small>
            <strong>{{ day.hotel.name }}</strong>
            <span>{{ day.hotel.address || day.hotel.distance }}</span>
            <b v-if="day.hotel.estimated_cost">¥{{ formatAmount(day.hotel.estimated_cost) }}/晚</b>
          </div>

          <div class="stop-list">
            <div v-for="(attraction, index) in day.attractions" :key="`${day.day_index}-${attraction.name}`" class="stop-item">
              <div class="stop-index">{{ index + 1 }}</div>
              <div class="stop-body">
                <div class="stop-title">
                  <h3>{{ attraction.name }}</h3>
                  <span>{{ attraction.visit_duration }} 分钟</span>
                </div>
                <p>{{ attraction.description }}</p>
                <small>{{ attraction.address }}</small>
                <div class="stop-tags">
                  <span v-if="attraction.category">{{ attraction.category }}</span>
                  <span v-if="attraction.ticket_price">¥{{ formatAmount(attraction.ticket_price) }}</span>
                  <span v-if="attraction.reservation_required">需预约</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="day.meals?.length" class="meal-list">
            <div v-for="meal in day.meals" :key="`${day.day_index}-${meal.type}-${meal.name}`">
              <small>{{ mealLabel(meal.type) }}</small>
              <strong>{{ meal.name }}</strong>
              <span v-if="meal.estimated_cost">¥{{ formatAmount(meal.estimated_cost) }}</span>
            </div>
          </div>
        </article>
      </section>
    </template>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { pollTaskStatus } from '@/services/api'
import type { Meal, TripPlan } from '@/types'

const route = useRoute()
const router = useRouter()

const tripPlan = ref<TripPlan | null>(null)
const planId = ref('')
const loading = ref(true)

const displayCity = computed(() => {
  const cities = tripPlan.value?.cities || []
  if (cities.length > 1) return cities.join(' → ')
  return tripPlan.value?.city || '旅行计划'
})

const formatAmount = (value?: number) => Math.round(Number(value || 0)).toLocaleString('zh-CN')

const mealLabel = (type: Meal['type']) => {
  const map: Record<Meal['type'], string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '小吃',
  }
  return map[type] || type
}

const goHome = () => {
  router.push('/')
}

const applyPlan = (plan: TripPlan, nextPlanId = '') => {
  tripPlan.value = plan
  if (nextPlanId) {
    planId.value = nextPlanId
    sessionStorage.setItem('planId', nextPlanId)
  }
  sessionStorage.setItem('tripPlan', JSON.stringify(plan))
}

const loadPlan = async () => {
  loading.value = true
  planId.value = String(route.query.plan_id || sessionStorage.getItem('planId') || '')

  const cached = sessionStorage.getItem('tripPlan')
  if (cached) {
    try {
      applyPlan(JSON.parse(cached), planId.value)
      loading.value = false
      return
    } catch {
      sessionStorage.removeItem('tripPlan')
    }
  }

  if (!planId.value) {
    loading.value = false
    return
  }

  try {
    const task = await pollTaskStatus(planId.value)
    if (task.status === 'completed' && task.result?.data) {
      applyPlan(task.result.data, String(task.result.plan_id || planId.value))
      return
    }
    if (task.status === 'failed') {
      message.error(task.error || '计划生成失败')
    } else {
      message.info('计划还在生成中，请稍后刷新')
    }
  } catch (error: any) {
    message.error(error.message || '读取计划失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadPlan()
})
</script>

<style scoped>
.mobile-result {
  min-height: 100vh;
  padding: 14px 14px 38px;
  background:
    radial-gradient(circle at 15% 0%, rgba(98, 171, 255, 0.36), transparent 30%),
    radial-gradient(circle at 100% 6%, rgba(191, 158, 255, 0.34), transparent 28%),
    linear-gradient(180deg, rgba(250, 253, 255, 0.74) 0%, rgba(238, 245, 252, 0.78) 100%);
  color: #152033;
}

.loading-state,
.empty-result {
  min-height: 80vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  text-align: center;
}

.empty-result h1 {
  margin: 0;
  font-size: 28px;
}

.empty-result p {
  max-width: 280px;
  color: #697175;
}

.empty-result button,
.back-button {
  height: 40px;
  padding: 0 16px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.52);
  color: #152033;
  font-weight: 800;
  border-radius: 18px;
  backdrop-filter: blur(18px) saturate(160%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72), 0 10px 24px rgba(64, 86, 112, 0.08);
}

.result-hero {
  min-height: 270px;
  padding: 18px;
  border-radius: 34px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(17, 31, 54, 0.72)),
    url('https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1200&q=80') center/cover;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  border: 1px solid rgba(255, 255, 255, 0.58);
  box-shadow: 0 28px 70px rgba(68, 96, 128, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.62);
  overflow: hidden;
  position: relative;
}

.result-hero::after {
  content: "";
  position: absolute;
  inset: 1px;
  border-radius: 32px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.34), transparent 36%);
  pointer-events: none;
}

.back-button {
  align-self: flex-start;
  margin-bottom: auto;
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.34);
  color: #fff;
  position: relative;
  z-index: 1;
}

.eyebrow {
  margin: 18px 0 8px;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0;
  opacity: 0.82;
  position: relative;
  z-index: 1;
}

.result-hero h1 {
  margin: 0;
  font-size: 36px;
  line-height: 1.05;
  font-weight: 900;
  letter-spacing: -0.03em;
  position: relative;
  z-index: 1;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
  position: relative;
  z-index: 1;
}

.hero-meta span,
.transfer-badge,
.stop-tags span {
  padding: 6px 9px;
  background: rgba(255, 255, 255, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.34);
  border-radius: 999px;
  backdrop-filter: blur(18px) saturate(150%);
  font-size: 12px;
  font-weight: 800;
}

.hero-copy {
  margin: 16px 0 0;
  color: rgba(255, 255, 255, 0.86);
  line-height: 1.65;
  position: relative;
  z-index: 1;
}

.quick-tabs {
  position: sticky;
  top: 0;
  z-index: 20;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 10px 0;
  background: rgba(239, 246, 253, 0.72);
  backdrop-filter: blur(20px) saturate(160%);
}

.quick-tabs a {
  padding: 10px 8px;
  background: rgba(255, 255, 255, 0.56);
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 18px;
  color: #152033;
  text-align: center;
  font-weight: 850;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.summary-card,
.day-card {
  padding: 16px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: 30px;
  box-shadow: 0 22px 60px rgba(70, 101, 135, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.74);
  backdrop-filter: blur(28px) saturate(160%);
}

.section-title,
.day-head,
.stop-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-title span {
  color: #5d6669;
  font-weight: 850;
}

.section-title strong {
  font-size: 30px;
  line-height: 1;
}

.budget-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 16px;
}

.budget-grid div,
.hotel-card,
.meal-list div {
  padding: 12px;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 22px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.64);
}

.budget-grid small,
.hotel-card small,
.meal-list small,
.day-head small,
.weather-strip small,
.stop-item small {
  display: block;
  color: #697175;
  font-size: 12px;
  font-weight: 750;
}

.budget-grid b,
.hotel-card b {
  display: block;
  margin-top: 4px;
}

.weather-strip {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.weather-strip article {
  min-width: 148px;
  padding: 12px;
  background: rgba(20, 34, 56, 0.72);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 24px;
  backdrop-filter: blur(24px) saturate(160%);
  box-shadow: 0 18px 42px rgba(54, 78, 106, 0.18);
}

.weather-strip span,
.weather-strip b {
  display: block;
  margin-top: 6px;
}

.day-list {
  display: grid;
  gap: 14px;
  margin-top: 14px;
}

.day-head h2 {
  margin: 4px 0 0;
  font-size: 24px;
  font-weight: 900;
}

.transfer-badge {
  background: rgba(0, 122, 255, 0.14);
  border-color: rgba(0, 122, 255, 0.28);
  color: #005ecb;
}

.day-desc,
.transfer-info {
  margin: 14px 0 0;
  color: #4b5b6b;
  line-height: 1.6;
}

.transfer-info {
  padding: 10px;
  background: rgba(0, 122, 255, 0.1);
  color: #005ecb;
  font-weight: 750;
  border-radius: 18px;
}

.mini-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.mini-row span {
  padding: 7px 10px;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 999px;
  color: #334155;
  font-size: 12px;
  font-weight: 850;
}

.hotel-card {
  display: grid;
  gap: 4px;
  margin-top: 12px;
}

.hotel-card strong {
  font-size: 16px;
}

.hotel-card span {
  color: #5e686b;
}

.stop-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.stop-item {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
}

.stop-index {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, #2f95ff 0%, #007aff 100%);
  color: #fff;
  font-weight: 900;
  border-radius: 14px;
  box-shadow: 0 12px 24px rgba(0, 122, 255, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.stop-body {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.stop-title h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 900;
}

.stop-title span {
  color: #007aff;
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

.stop-body p {
  margin: 8px 0;
  color: #4b5b6b;
  line-height: 1.55;
}

.stop-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.stop-tags span {
  background: rgba(255, 255, 255, 0.44);
  border-color: rgba(255, 255, 255, 0.66);
  color: #334155;
}

.meal-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-top: 14px;
}

.meal-list div {
  display: grid;
  grid-template-columns: 58px 1fr auto;
  align-items: center;
  gap: 8px;
}

.meal-list strong {
  min-width: 0;
}

@media (min-width: 720px) {
  .mobile-result {
    max-width: 520px;
    margin: 0 auto;
  }
}
</style>
