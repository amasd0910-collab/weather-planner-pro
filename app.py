import streamlit as st
import requests
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# -----------------------
# Page
# -----------------------
st.set_page_config(page_title="台灣天氣旅遊規劃助手", page_icon="🗺️", layout="wide")

st.markdown(
    """
<style>
    .main-title {font-size: 2.2rem; font-weight: 800; text-align:center; margin: 6px 0 0 0;}
    .subtitle {text-align:center; opacity:0.75; margin: 6px 0 18px 0;}
    .pill {display:inline-block; padding:2px 10px; border-radius:999px; border:1px solid rgba(255,255,255,0.15); margin-right:6px;}
</style>
""",
    unsafe_allow_html=True,
)
st.markdown("<div class='main-title'>🗺️ 台灣天氣旅遊規劃助手</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>用天氣預報把行程拆到上半天 / 下半天，並提供雨天備案</div>", unsafe_allow_html=True)

# -----------------------
# Data (先以北台灣為主)
# -----------------------
NORTH_TW = {
    "台北": {"lat": 25.0330, "lon": 121.5654},
    "新北": {"lat": 25.0120, "lon": 121.4659},
    "基隆": {"lat": 25.1276, "lon": 121.7392},
    "桃園": {"lat": 24.9936, "lon": 121.3010},
    "宜蘭": {"lat": 24.7022, "lon": 121.7378},
    "新竹": {"lat": 24.8138, "lon": 120.9675},
}

ACTIVITY_TYPES = {
    "🍜 美食探索": ["夜市小吃", "老街美食", "特色餐廳", "咖啡廳"],
    "🏛️ 文化古蹟": ["博物館", "古蹟巡禮", "藝文中心", "寺廟參拜"],
    "🏖️ 海邊活動": ["海邊散步", "看海咖啡", "衝浪", "海釣"],
    "⛰️ 山區健行": ["森林步道", "登山健行", "觀景平台", "露營"],
    "🛍️ 購物休閒": ["百貨公司", "商圈逛街", "市集", "outlet"],
    "♨️ 溫泉度假": ["泡溫泉", "溫泉飯店", "湯屋", "SPA"],
}

# -----------------------
# Secrets
# -----------------------
try:
    OW_KEY = st.secrets["OPENWEATHER_API_KEY"]
except Exception:
    st.error("缺少 OPENWEATHER_API_KEY。請在 Streamlit secrets 設定後再試。")
    st.stop()

# -----------------------
# Sidebar (用 form 避免手機操作混亂)
# -----------------------
with st.sidebar:
    st.header("設定")

    with st.form("planner_form"):
        selected_cities = st.multiselect(
            "選擇城市（可多選）",
            options=list(NORTH_TW.keys()),
            default=["台北", "新北"],
            help="簡易版先以北台灣城市為主；多城市會輪流分配行程。",
        )

        forecast_window = st.radio(
            "預報視窗（資料限制提醒）",
            options=[5, 10],
            index=0,
            format_func=lambda x: f"{x} 天（/forecast 實際約 5 天）",
        )

        trip_days = st.number_input(
            "你要規劃幾天旅遊？",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
        )

        st.markdown("---")

        selected_activity_types = st.multiselect(
            "偏好活動類型",
            options=list(ACTIVITY_TYPES.keys()),
            default=["🍜 美食探索", "🏛️ 文化古蹟"],
        )

        rain_threshold = st.slider(
            "雨天分水嶺（降雨機率%）",
            min_value=0,
            max_value=100,
            value=40,
            help="高於此值，該半天改走雨天備案（室內為主）。",
        )

        temp_pref = st.select_slider(
            "溫度偏好",
            options=["怕熱", "適中", "不怕熱"],
            value="適中",
        )

        # 路線（不用 Google API，直接產連結）
        st.markdown("---")
        origin_text = st.text_input("路線起點（可輸入：新北市貢寮區）", value="")
        dest_text = st.text_input("路線終點（可輸入：宜蘭縣頭城鎮）", value="")
        waypoints_text = st.text_input("中途點（用逗號分隔，可留空）", value="")

        submitted = st.form_submit_button("開始規劃", use_container_width=True)

# -----------------------
# Helpers
# -----------------------
def temp_range(pref: str):
    if pref == "怕熱":
        return (10, 25)
    if pref == "適中":
        return (18, 28)
    return (18, 35)


def score_halfday(avg_temp, rain_prob, wind_speed, trange, rain_tol):
    # 先沿用你原來的思路（簡易版：好天氣+10、偏離扣分、雨太大扣分、風太大扣分）
    score = 100
    if avg_temp < trange[0]:
        score -= (trange[0] - avg_temp) * 3
    elif avg_temp > trange[1]:
        score -= (avg_temp - trange[1]) * 3
    else:
        score += 10

    if rain_prob > rain_tol:
        score -= (rain_prob - rain_tol) * 1.5

    if wind_speed > 10:
        score -= (wind_speed - 10) * 2

    return max(0, min(100, score))


@st.cache_data(ttl=1800)
def fetch_forecast(lat, lon, api_key):
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "lang": "zh_tw"}
    r = requests.get(base_url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def local_dt(item_dt_utc, tz_offset_sec):
    # OpenWeather 會給 city.timezone（秒）
    return datetime.utcfromtimestamp(item_dt_utc + tz_offset_sec)


def build_halfday_table(weather_json, days_limit=5):
    """
    取 06-12 作 AM，12-18 作 PM，聚合成半天。
    回傳：dict[date_str][period] = stats
    """
    tz = weather_json.get("city", {}).get("timezone", 0)

    buckets = {}  # date -> period -> accum
    horizon_end = datetime.utcnow() + timedelta(days=days_limit + 1)

    for it in weather_json["list"]:
        dt_local = local_dt(it["dt"], tz)
        if dt_local > horizon_end:
            continue

        hour = dt_local.hour
        if 6 <= hour < 12:
            period = "AM"
        elif 12 <= hour < 18:
            period = "PM"
        else:
            continue

        date_key = dt_local.strftime("%Y-%m-%d")
        buckets.setdefault(date_key, {})
        buckets[date_key].setdefault(period, {"temps": [], "pop": [], "wind": [], "desc": []})

        buckets[date_key][period]["temps"].append(it["main"]["temp"])
        buckets[date_key][period]["pop"].append(it.get("pop", 0) * 100)  # 0-1 -> %
        buckets[date_key][period]["wind"].append(it["wind"]["speed"])
        buckets[date_key][period]["desc"].append(it["weather"][0]["description"])

    # summarize
    out = []
    for date_key in sorted(buckets.keys()):
        for period in ["AM", "PM"]:
            if period not in buckets[date_key]:
                continue
            b = buckets[date_key][period]
            avg_temp = sum(b["temps"]) / len(b["temps"])
            rain_prob = sum(b["pop"]) / len(b["pop"])
            wind = sum(b["wind"]) / len(b["wind"])
            # most common desc
            desc_count = {}
            for d in b["desc"]:
                desc_count[d] = desc_count.get(d, 0) + 1
            desc = max(desc_count, key=desc_count.get)
            out.append(
                {
                    "date": date_key,
                    "period": period,
                    "avg_temp": avg_temp,
                    "rain_prob": rain_prob,
                    "wind": wind,
                    "desc": desc,
                }
            )
    return out


def maps_search_link(query: str):
    # 不用 API key 的 maps 搜尋
    q = quote_plus(query)
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def maps_directions_link(origin: str, destination: str, waypoints: str = ""):
    # 不用 API key 的 directions
    o = quote_plus(origin)
    d = quote_plus(destination)
    url = f"https://www.google.com/maps/dir/?api=1&origin={o}&destination={d}"
    if waypoints.strip():
        w = quote_plus(waypoints)
        url += f"&waypoints={w}"
    return url


def pick_activity(city: str, activity_types, rainy: bool, period: str):
    # 簡易版：不用外部旅遊 API，先用可點的 maps 搜尋關鍵字組合
    if rainy:
        # 雨天：室內/半室內優先
        candidates = [
            ("雨天備案：博物館/展覽", f"{city} 博物館 展覽"),
            ("雨天備案：百貨商場/美食街", f"{city} 百貨 美食街"),
            ("雨天備案：咖啡廳", f"{city} 咖啡廳"),
        ]
    else:
        # 晴天：依偏好活動給一些關鍵字
        candidates = []
        for t in activity_types:
            if t == "🏖️ 海邊活動":
                candidates.append(("海邊散步/看海點", f"{city} 海邊 看海"))
            elif t == "⛰️ 山區健行":
                candidates.append(("步道/觀景點", f"{city} 步道 觀景台"))
            elif t == "♨️ 溫泉度假":
                candidates.append(("溫泉/湯屋", f"{city} 溫泉 湯屋"))
            elif t == "🛍️ 購物休閒":
                candidates.append(("商圈/百貨", f"{city} 商圈 百貨"))
            elif t == "🏛️ 文化古蹟":
                candidates.append(("古蹟/文化館", f"{city} 古蹟 文化館"))
            elif t == "🍜 美食探索":
                candidates.append(("老街/夜市/美食", f"{city} 老街 夜市 美食"))

        if not candidates:
            candidates = [("隨機推薦：散步+美食", f"{city} 景點 美食")]

    # 小小差異：上午偏戶外、下午偏美食/逛街（簡易策略）
    if not rainy and period == "PM":
        candidates = candidates[::-1]

    title, query = candidates[0]
    return title, query


# -----------------------
# Main
# -----------------------
if submitted:
    if not selected_cities:
        st.warning("請至少選擇一個城市。")
        st.stop()

    # /forecast 實際可用天數
    available_days = 5
    if forecast_window > 5:
        st.info("提醒：你選了 10 天，但目前 /forecast 實際約 5 天資料。簡易版先用 5 天做規劃。")
    if trip_days > available_days:
        st.warning(f"你要規劃 {trip_days} 天，但目前可用預報約 {available_days} 天。先以 {available_days} 天內做建議。")
        trip_days = available_days

    tr = temp_range(temp_pref)

    with st.spinner("正在抓取天氣資料並生成上/下半天行程..."):
        # 簡易版：用第一個城市的預報做日期選擇（之後可升級成多城市各自評分再排）
        base_city = selected_cities[0]
        wjson = fetch_forecast(NORTH_TW[base_city]["lat"], NORTH_TW[base_city]["lon"], OW_KEY)

        halfdays = build_halfday_table(wjson, days_limit=available_days)

        # 加上評分
        scored = []
        for h in halfdays:
            s = score_halfday(h["avg_temp"], h["rain_prob"], h["wind"], tr, rain_threshold)
            scored.append({**h, "score": s})

        # 聚合成「天」：AM/PM 都有時取平均
        by_date = {}
        for x in scored:
            by_date.setdefault(x["date"], {})
            by_date[x["date"]][x["period"]] = x

        day_scores = []
        for d, parts in by_date.items():
            scores = [parts[p]["score"] for p in parts if p in ["AM", "PM"]]
            if not scores:
                continue
            day_scores.append({"date": d, "day_score": sum(scores) / len(scores), "parts": parts})

        # 取最適合的 trip_days 天（再按日期排序呈現）
        best_days = sorted(day_scores, key=lambda x: x["day_score"], reverse=True)[:trip_days]
        best_days = sorted(best_days, key=lambda x: x["date"])

    st.success("已完成行程草案（簡易版）。")

    # 路線連結
    if origin_text.strip() and dest_text.strip():
        wp = waypoints_text.strip()
        link = maps_directions_link(origin_text.strip(), dest_text.strip(), wp)
        st.markdown(f"🚗 **Google Maps 路線導航：** {link}")

    st.markdown("---")
    st.subheader("你的 N 天游程（上半天 / 下半天）")

    # 多城市簡易分配：輪流
    def city_for_day(idx):
        return selected_cities[idx % len(selected_cities)]

    for i, day in enumerate(best_days, start=1):
        city_today = city_for_day(i - 1)
        dstr = day["date"]
        weekday = datetime.strptime(dstr, "%Y-%m-%d").strftime("%a")

        st.markdown(f"### 第 {i} 天：{dstr} ({weekday}) · 主要區域：{city_today}")

        for period in ["AM", "PM"]:
            part = day["parts"].get(period)
            if not part:
                st.write(f"**{period}：**（資料不足，建議彈性安排）")
                continue

            rainy = part["rain_prob"] >= rain_threshold
            act_title, act_query = pick_activity(city_today, selected_activity_types, rainy, period)
            map_link = maps_search_link(act_query)

            tag = "☔ 雨天備案" if rainy else "☀️ 晴天方案"
            st.markdown(
                f"- **{period} {tag}**｜{act_title}  "
                f"<span class='pill'>評分 {int(part['score'])}</span>"
                f"<span class='pill'>溫 {part['avg_temp']:.1f}°C</span>"
                f"<span class='pill'>雨 {int(part['rain_prob'])}%</span>"
                f"<span class='pill'>風 {part['wind']:.1f}m/s</span>",
                unsafe_allow_html=True,
            )
            st.write(f"  天氣：{part['desc']}")
            st.write(f"  地圖搜尋：{map_link}")

        st.markdown("---")

    st.caption("簡易版說明：目前用第一個城市的預報挑選適合日期，多城市是用輪流分配。下一步可升級成每個城市各自評分後再排最優路線。")

else:
    st.info("先在左上角（手機）打開側邊欄設定城市與天數，再按「開始規劃」。")