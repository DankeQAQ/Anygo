"""
知识图谱构建服务
从 TripPlan 数据中提取实体(节点)和关系(边)，生成力导向图数据
"""

from typing import Dict, Any, List
from ..models.schemas import TripPlan


# ============ 节点颜色配置 ============
NODE_COLORS = {
    "city":       "#4A90D9",   # 蓝色 - 城市
    "day":        "#5B8FF9",   # 浅蓝 - 天
    "attraction": "#5AD8A6",   # 绿色 - 景点
    "hotel":      "#F6BD16",   # 金色 - 酒店
    "meal":       "#E8684A",   # 珊瑚红 - 餐饮
    "weather":    "#6DC8EC",   # 天蓝 - 天气
    "budget":     "#FF9845",   # 橙色 - 预算
    "preference": "#B37FEB",   # 紫色 - 偏好
}

NODE_SIZES = {
    "city":       70,
    "day":        45,
    "attraction": 35,
    "hotel":      35,
    "meal":       25,
    "weather":    28,
    "budget":     40,
    "preference": 30,
}

# ============ 多语言翻译表 ============
_I18N: Dict[str, Dict[str, str]] = {
    "zh": {
        # 分类名称
        "cat_city": "城市", "cat_day": "日程", "cat_attraction": "景点",
        "cat_hotel": "酒店", "cat_meal": "餐饮", "cat_weather": "天气",
        "cat_budget": "预算", "cat_preference": "偏好/建议",
        # 边标签
        "edge_itinerary": "行程", "edge_visit": "游览", "edge_next": "下一站",
        "edge_checkin": "入住", "edge_weather": "天气", "edge_budget": "预算",
        "edge_suggestion": "建议",
        # 节点文本模板
        "day_n": "第{n}天",
        "visit_duration": "游览{min}分钟", "ticket_price": "门票¥{price}",
        "hotel_cost": "{range} | ¥{cost}/晚",
        "total_budget": "总预算 ¥{total}",
        # 餐饮类型
        "breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "snack": "小吃",
        # 预算子项
        "budget_attraction": "景点", "budget_hotel": "酒店",
        "budget_meal": "餐饮", "budget_transport": "交通", "budget_inter_city": "城际交通",
    },
    "en": {
        "cat_city": "City", "cat_day": "Schedule", "cat_attraction": "Attraction",
        "cat_hotel": "Hotel", "cat_meal": "Dining", "cat_weather": "Weather",
        "cat_budget": "Budget", "cat_preference": "Tips",
        "edge_itinerary": "Itinerary", "edge_visit": "Visit", "edge_next": "Next",
        "edge_checkin": "Check-in", "edge_weather": "Weather", "edge_budget": "Budget",
        "edge_suggestion": "Tips",
        "day_n": "Day {n}",
        "visit_duration": "Visit {min} min", "ticket_price": "Ticket ¥{price}",
        "hotel_cost": "{range} | ¥{cost}/night",
        "total_budget": "Total Budget ¥{total}",
        "breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner", "snack": "Snack",
        "budget_attraction": "Attractions", "budget_hotel": "Hotels",
        "budget_meal": "Dining", "budget_transport": "Transport", "budget_inter_city": "Inter-city",
    },
    "ja": {
        "cat_city": "都市", "cat_day": "スケジュール", "cat_attraction": "観光地",
        "cat_hotel": "ホテル", "cat_meal": "グルメ", "cat_weather": "天気",
        "cat_budget": "予算", "cat_preference": "おすすめ",
        "edge_itinerary": "旅程", "edge_visit": "観光", "edge_next": "次へ",
        "edge_checkin": "宿泊", "edge_weather": "天気", "edge_budget": "予算",
        "edge_suggestion": "提案",
        "day_n": "{n}日目",
        "visit_duration": "観光{min}分", "ticket_price": "入場料¥{price}",
        "hotel_cost": "{range} | ¥{cost}/泊",
        "total_budget": "総予算 ¥{total}",
        "breakfast": "朝食", "lunch": "昼食", "dinner": "夕食", "snack": "軽食",
        "budget_attraction": "観光地", "budget_hotel": "ホテル",
        "budget_meal": "グルメ", "budget_transport": "交通", "budget_inter_city": "都市間交通",
    },
}


def _t(key: str, lang: str, **kwargs: Any) -> str:
    """从翻译表中取对应语言的文本，支持占位符替换。"""
    table = _I18N.get(lang, _I18N["zh"])
    template = table.get(key, _I18N["zh"].get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template


def build_knowledge_graph(trip_plan: TripPlan, language: str = "zh") -> Dict[str, Any]:
    """
    从 TripPlan 构建知识图谱数据

    Args:
        trip_plan: 旅行计划数据
        language: 界面语言代码 (zh/en/ja 等)

    Returns:
        {
            "nodes": [{"id", "name", "category", "symbolSize", "value", ...}],
            "edges": [{"source", "target", "label"}],
            "categories": [{"name"}]
        }
    """
    lang = (language or "zh").strip().lower().split("-")[0]
    print(f"[KG] build_knowledge_graph called with language='{language}' -> resolved lang='{lang}'")
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    node_ids = set()

    # ---- 分类定义 (ECharts graph categories) ----
    cat_keys = ["cat_city", "cat_day", "cat_attraction", "cat_hotel",
                "cat_meal", "cat_weather", "cat_budget", "cat_preference"]
    categories = [{"name": _t(k, lang)} for k in cat_keys]
    cat_map = {_t(k, lang): i for i, k in enumerate(cat_keys)}

    # 内部分类名 → 英文 key 的映射（用于颜色/尺寸查找）
    _cat_style_key = {
        _t("cat_city", lang): "city", _t("cat_day", lang): "day",
        _t("cat_attraction", lang): "attraction", _t("cat_hotel", lang): "hotel",
        _t("cat_meal", lang): "meal", _t("cat_weather", lang): "weather",
        _t("cat_budget", lang): "budget", _t("cat_preference", lang): "preference",
    }

    def add_node(nid: str, name: str, category_name: str, extra_value: str = ""):
        if nid in node_ids:
            return
        node_ids.add(nid)
        cat_key = _cat_style_key.get(category_name, "city")
        nodes.append({
            "id": nid,
            "name": name,
            "category": cat_map.get(category_name, 0),
            "symbolSize": NODE_SIZES.get(cat_key, 30),
            "itemStyle": {"color": NODE_COLORS.get(cat_key, "#999")},
            "value": extra_value,
        })

    def add_edge(source: str, target: str, label: str = ""):
        edges.append({"source": source, "target": target, "label": label})

    cat_city = _t("cat_city", lang)
    cat_day = _t("cat_day", lang)
    cat_attraction = _t("cat_attraction", lang)
    cat_hotel = _t("cat_hotel", lang)
    cat_meal = _t("cat_meal", lang)
    cat_weather = _t("cat_weather", lang)
    cat_budget = _t("cat_budget", lang)
    cat_preference = _t("cat_preference", lang)

    # ========== 1. 城市节点（支持多城市） ==========
    cities_list = trip_plan.cities or [trip_plan.city]
    city_node_ids: Dict[str, str] = {}

    if len(cities_list) > 1:
        # 多城市: 创建旅途根节点 + 各城市子节点
        root_id = "trip_root"
        root_name = " → ".join(cities_list)
        add_node(root_id, root_name, cat_city, f"{trip_plan.start_date} ~ {trip_plan.end_date}")
        for city_name in cities_list:
            cid = f"city_{city_name}"
            add_node(cid, city_name, cat_city, "")
            add_edge(root_id, cid, _t("edge_itinerary", lang))
            city_node_ids[city_name] = cid
    else:
        # 单城市: 保持原逻辑
        root_id = f"city_{trip_plan.city}"
        add_node(root_id, trip_plan.city, cat_city, f"{trip_plan.start_date} ~ {trip_plan.end_date}")
        city_node_ids[trip_plan.city] = root_id

    # ========== 2. 每日节点（挂到对应城市下） ==========
    for day in trip_plan.days:
        day_id = f"day_{day.day_index}"
        day_city = getattr(day, 'city', '') or trip_plan.city
        parent_id = city_node_ids.get(day_city, root_id)

        add_node(day_id, _t("day_n", lang, n=day.day_index + 1), cat_day, day.date)
        add_edge(parent_id, day_id, _t("edge_itinerary", lang))

        # ---- 景点 ----
        for i, attr in enumerate(day.attractions):
            attr_id = f"attr_{day.day_index}_{i}_{attr.name}"
            value_parts = []
            if attr.address:
                value_parts.append(attr.address)
            if attr.visit_duration:
                value_parts.append(_t("visit_duration", lang, min=attr.visit_duration))
            if attr.ticket_price:
                value_parts.append(_t("ticket_price", lang, price=attr.ticket_price))
            add_node(attr_id, attr.name, cat_attraction, " | ".join(value_parts))
            add_edge(day_id, attr_id, _t("edge_visit", lang))

            # 景点间顺序关系
            if i > 0:
                prev_attr = day.attractions[i - 1]
                prev_id = f"attr_{day.day_index}_{i-1}_{prev_attr.name}"
                add_edge(prev_id, attr_id, _t("edge_next", lang))

        # ---- 酒店 ----
        if day.hotel:
            hotel_id = f"hotel_{day.day_index}_{day.hotel.name}"
            hotel_value = (
                _t("hotel_cost", lang, range=day.hotel.price_range, cost=day.hotel.estimated_cost)
                if day.hotel.estimated_cost else day.hotel.price_range
            )
            add_node(hotel_id, day.hotel.name, cat_hotel, hotel_value)
            add_edge(day_id, hotel_id, _t("edge_checkin", lang))

        # ---- 餐饮 ----
        for j, meal in enumerate(day.meals):
            meal_type_label = _t(meal.type, lang) if meal.type in ("breakfast", "lunch", "dinner", "snack") else meal.type
            meal_id = f"meal_{day.day_index}_{j}_{meal.name}"
            add_node(meal_id, f"{meal_type_label}: {meal.name}", cat_meal,
                     f"¥{meal.estimated_cost}" if meal.estimated_cost else "")
            add_edge(day_id, meal_id, meal_type_label)

    # ========== 3. 天气节点 ==========
    for w in trip_plan.weather_info:
        w_id = f"weather_{w.date}"
        add_node(w_id, f"{w.day_weather} {w.day_temp}°C", cat_weather, w.date)
        # 尝试关联到对应天
        for day in trip_plan.days:
            if day.date == w.date:
                add_edge(f"day_{day.day_index}", w_id, _t("edge_weather", lang))
                break

    # ========== 4. 预算节点 ==========
    if trip_plan.budget:
        b = trip_plan.budget
        budget_id = "budget_total"
        add_node(budget_id, _t("total_budget", lang, total=b.total), cat_budget, "")
        add_edge(root_id, budget_id, _t("edge_budget", lang))

        for label_key, value in [
            ("budget_attraction", b.total_attractions),
            ("budget_hotel", b.total_hotels),
            ("budget_meal", b.total_meals),
            ("budget_transport", b.total_transportation),
            ("budget_inter_city", b.total_inter_city_transport),
        ]:
            if value:
                label = _t(label_key, lang)
                sub_id = f"budget_{label_key}"
                add_node(sub_id, f"{label} ¥{value}", cat_budget, "")
                add_edge(budget_id, sub_id, label)

    # ========== 5. 总体建议节点 ==========
    if trip_plan.overall_suggestions:
        sug_id = "suggestion_overall"
        # 截断过长文本
        sug_text = trip_plan.overall_suggestions[:30] + "..." if len(trip_plan.overall_suggestions) > 30 else trip_plan.overall_suggestions
        add_node(sug_id, sug_text, cat_preference, trip_plan.overall_suggestions)
        add_edge(root_id, sug_id, _t("edge_suggestion", lang))

    return {
        "nodes": nodes,
        "edges": edges,
        "categories": categories,
    }
