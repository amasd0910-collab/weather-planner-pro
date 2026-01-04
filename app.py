import streamlit as st
import requests
from datetime import datetime
import pandas as pd

st.set_page_config(
page_title="Taiwan Travel Planner",
page_icon="🗺️",
layout="wide"
)

st.markdown("""

<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
    }
</style>

""", unsafe_allow_html=True)

st.markdown("<p class='main-title'>🗺️ 台灣天氣旅遊規劃助手</p>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>根據天氣預報，為您規劃最適合的台灣旅遊行程</p>", unsafe_allow_html=True)

TAIWAN_CITIES = {
"台北": {"en": "Taipei", "lat": 25.0330, "lon": 121.5654},
"新北": {"en": "New Taipei", "lat": 25.0120, "lon": 121.4659},
"桃園": {"en": "Taoyuan", "lat": 24.9936, "lon": 121.3010},
"台中": {"en": "Taichung", "lat": 24.1477, "lon": 120.6736},
"台南": {"en": "Tainan", "lat": 22.9998, "lon": 120.2269},
"高雄": {"en": "Kaohsiung", "lat": 22.6273, "lon": 120.3014},
"基隆": {"en": "Keelung", "lat": 25.1276, "lon": 121.7392},
"新竹": {"en": "Hsinchu", "lat": 24.8138, "lon": 120.9675},
"嘉義": {"en": "Chiayi", "lat": 23.4801, "lon": 120.4491},
"宜蘭": {"en": "Yilan", "lat": 24.7022, "lon": 121.7378},
"花蓮": {"en": "Hualien", "lat": 23.9871, "lon": 121.6015},
"台東": {"en": "Taitung", "lat": 22.7583, "lon": 121.1444},
"屏東": {"en": "Pingtung", "lat": 22.6820, "lon": 120.4818},
"南投": {"en": "Nantou", "lat": 23.9609, "lon": 120.9719}
}

ACTIVITY_TYPES = {
"🏖️ 海邊活動": ["衝浪", "游泳", "海釣", "沙灘排球", "潛水"],
"⛰️ 山區健行": ["登山", "森林步道", "賞楓", "露營", "生態觀察"],
"🏛️ 文化古蹟": ["寺廟參拜", "古蹟巡禮", "博物館", "藝文中心"],
"🍜 美食探索": ["夜市小吃", "老街美食", "特色餐廳", "咖啡廳"],
"🛍️ 購物休閒": ["百貨公司", "商圈逛街", "市集", "outlet"],
"🎡 遊樂園區": ["主題樂園", "動物園", "水族館", "遊樂設施"],
"🚴 戶外運動": ["自行車", "路跑", "球類運動", "攀岩"],
"♨️ 溫泉度假": ["泡溫泉", "SPA", "度假村", "民宿體驗"],
"📸 攝影景點": ["網美景點", "日出日落", "風景攝影", "建築攝影"]
}

try:
    api_key = st.secrets["OPENWEATHER_API_KEY"]
except:
    st.error("系統設定錯誤，請確認 API Key 已正確設定")
    st.stop()

with st.sidebar:
    st.header("旅遊偏好設定")

st.subheader("目的地")
selected_city = st.selectbox(
    "選擇縣市",
    options=list(TAIWAN_CITIES.keys()),
    help="選擇您想去的台灣縣市"
)

st.subheader("規劃天數")
forecast_days = st.radio(
    "選擇預測天數",
    options=[5, 10],
    format_func=lambda x: str(x) + " 天預報",
    help="5天預報較準確，10天預報參考用"
)

st.markdown("---")

st.subheader("旅遊偏好")
selected_activities = st.multiselect(
    "喜歡的活動類型",
    options=list(ACTIVITY_TYPES.keys()),
    default=["🍜 美食探索", "🏛️ 文化古蹟"],
    help="選擇您喜歡的旅遊活動類型"
)

st.subheader("天氣偏好")
temp_options = ["怕熱", "適中", "不怕熱"]
temp_preference = st.select_slider(
    "溫度偏好",
    options=temp_options,
    value="適中"
)

rain_tolerance = st.slider(
    "降雨容忍度",
    min_value=0,
    max_value=100,
    value=30,
    help="降雨機率超過此值會降低推薦度"
)

st.markdown("---")

with st.expander("進階設定"):
    show_all_days = st.checkbox("顯示所有天數", value=False)
    sort_by_score = st.checkbox("依適合度排序", value=True)

@st.cache_data(ttl=1800)
def get_weather_forecast(lat, lon, api_key, days):
try:
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
    "lat": lat,
    "lon": lon,
    "appid": api_key,
    "units": "metric",
    "lang": "zh_tw"
    }
url = base_url + "?lat=" + str(lat) + "&lon=" + str(lon) + "&appid=" + api_key + "&units=metric&lang=zh_tw"
response = requests.get(url, timeout=10)

    if response.status_code == 200:
        return response.json()
    else:
        return None
except Exception as e:
    st.error("錯誤: " + str(e))
    return None

def parse_temp_preference(pref):
if pref == "怕熱":
return (10, 25)
elif pref == "適中":
return (20, 28)
else:
return (20, 35)

def calculate_weather_score(temp, rain_prob, wind_speed, temp_range, rain_tolerance):
score = 100

if temp < temp_range[0]:
    score = score - (temp_range[0] - temp) * 3
elif temp > temp_range[1]:
    score = score - (temp - temp_range[1]) * 3
else:
    score = score + 10

if rain_prob > rain_tolerance:
    score = score - (rain_prob - rain_tolerance) * 1.5

if wind_speed > 10:
    score = score - (wind_speed - 10) * 2

return max(0, min(100, score))

def recommend_activities(score, temp, rain_prob, wind_speed, selected_activities):
recommendations = []
reasons = []

if score >= 85:
    level = "極佳"
    base_desc = "天氣極佳！"
elif score >= 70:
    level = "良好"
    base_desc = "天氣不錯"
elif score >= 50:
    level = "普通"
    base_desc = "天氣尚可"
else:
    level = "不佳"
    base_desc = "天氣較差"

for activity_type in selected_activities:
    activities = ACTIVITY_TYPES[activity_type]
    act_str = activities[0] + ", " + activities[1] + ", " + activities[2]
    
    if activity_type == "🏖️ 海邊活動":
        if score >= 70 and temp >= 25 and wind_speed < 8:
            recommendations.append(activity_type + ": " + act_str)
            reasons.append("陽光充足、風浪適中")
    
    elif activity_type == "⛰️ 山區健行":
        if score >= 60 and temp < 30 and rain_prob < 40:
            recommendations.append(activity_type + ": " + act_str)
            reasons.append("溫度舒適、不會太熱")
    
    elif activity_type == "🏛️ 文化古蹟":
        if score >= 40:
            recommendations.append(activity_type + ": " + act_str)
            reasons.append("室內為主，較不受天氣影響")
    
    elif activity_type == "🍜 美食探索":
        if score >= 30:
            recommendations.append(activity_type + ": " + act_str)
            reasons.append("隨時都是美食時間！")
    
    elif activity_type == "🛍️ 購物休閒":
        recommendations.append(activity_type + ": " + act_str)
        reasons.append("室內活動，不受天氣限制")
    
    elif activity_type == "🎡 遊樂園區":
        if score >= 65 and rain_prob < 50:
            recommendations.append(activity_type + ": " + act_str)
            reasons.append("戶外設施較多，需好天氣")
    
    elif activity_type == "🚴 戶外運動":
        if score >= 75 and temp < 32 and wind_speed < 10:
            recommendations.append(activity_type + ": " + act_str)
            reasons.append("適合運動的天氣條件")
    
    elif activity_type == "♨️ 溫泉度假":
        if temp < 25 or rain_prob > 50:
            recommendations.append(activity_type + ": " + act_str)
            reasons.append("涼爽或雨天更適合泡湯")
    
    elif activity_type == "📸 攝影景點":
        if score >= 70 and rain_prob < 30:
            recommendations.append(activity_type + ": " + act_str)
            reasons.append("能見度佳，光線充足")

if len(recommendations) == 0:
    if rain_prob > 70:
        recommendations.append("室內活動：博物館、購物中心、美食街")
        reasons.append("下雨天建議室內活動")
    elif temp > 33:
        recommendations.append("避暑活動：游泳池、有冷氣的地方、夜間活動")
        reasons.append("天氣炎熱，注意防曬")
    else:
        recommendations.append("輕鬆活動：咖啡廳、室內景點、購物")
        reasons.append("天氣一般，建議輕鬆行程")

warnings = []
if rain_prob > 60:
    warnings.append("建議攜帶雨具")
if temp > 32:
    warnings.append("高溫警報，注意防曬補水")
if temp < 15:
    warnings.append("氣溫較低，記得保暖")
if wind_speed > 12:
    warnings.append("風速較大，戶外活動注意安全")

return level, base_desc, recommendations, reasons, warnings

def process_forecast_data(weather_data, days, temp_range, rain_tolerance, selected_activities):
daily_data = []
current_date = None
daily_records = {
"temps": [],
"rain": [],
"wind": [],
"humidity": [],
"descriptions": []
}

max_items = days * 8
item_count = 0

for item in weather_data["list"]:
    if item_count >= max_items:
        break
    item_count = item_count + 1
    
    dt = datetime.fromtimestamp(item["dt"])
    date = dt.date()
    
    if current_date != date:
        if current_date and len(daily_records["temps"]) > 0:
            avg_temp = sum(daily_records["temps"]) / len(daily_records["temps"])
            max_temp = max(daily_records["temps"])
            min_temp = min(daily_records["temps"])
            avg_rain = sum(daily_records["rain"]) / len(daily_records["rain"]) * 100
            avg_wind = sum(daily_records["wind"]) / len(daily_records["wind"])
            avg_humidity = sum(daily_records["humidity"]) / len(daily_records["humidity"])
            
            score = calculate_weather_score(avg_temp, avg_rain, avg_wind, temp_range, rain_tolerance)
            level, desc, activities, reasons, warnings = recommend_activities(score, avg_temp, avg_rain, avg_wind, selected_activities)
            
            weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
            weekday = weekdays[current_date.weekday()]
            
            desc_counts = {}
            for d in daily_records["descriptions"]:
                if d in desc_counts:
                    desc_counts[d] = desc_counts[d] + 1
                else:
                    desc_counts[d] = 1
            
            most_common_desc = max(desc_counts, key=desc_counts.get)
            
            daily_data.append({
                "date": current_date,
                "weekday": weekday,
                "temp_avg": avg_temp,
                "temp_max": max_temp,
                "temp_min": min_temp,
                "rain_prob": avg_rain,
                "wind_speed": avg_wind,
                "humidity": avg_humidity,
                "description": most_common_desc,
                "score": score,
                "level": level,
                "desc": desc,
                "activities": activities,
                "reasons": reasons,
                "warnings": warnings
            })
        
        current_date = date
        daily_records = {
            "temps": [],
            "rain": [],
            "wind": [],
            "humidity": [],
            "descriptions": []
        }
    
    daily_records["temps"].append(item["main"]["temp"])
    
    pop_value = 0
    if "pop" in item:
        pop_value = item["pop"]
    daily_records["rain"].append(pop_value)
    
    daily_records["wind"].append(item["wind"]["speed"])
    daily_records["humidity"].append(item["main"]["humidity"])
    daily_records["descriptions"].append(item["weather"][0]["description"])

if len(daily_records["temps"]) > 0:
    avg_temp = sum(daily_records["temps"]) / len(daily_records["temps"])
    max_temp = max(daily_records["temps"])
    min_temp = min(daily_records["temps"])
    avg_rain = sum(daily_records["rain"]) / len(daily_records["rain"]) * 100
    avg_wind = sum(daily_records["wind"]) / len(daily_records["wind"])
    avg_humidity = sum(daily_records["humidity"]) / len(daily_records["humidity"])
    
    score = calculate_weather_score(avg_temp, avg_rain, avg_wind, temp_range, rain_tolerance)
    level, desc, activities, reasons, warnings = recommend_activities(score, avg_temp, avg_rain, avg_wind, selected_activities)
    
    weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    weekday = weekdays[current_date.weekday()]
    
    desc_counts = {}
    for d in daily_records["descriptions"]:
        if d in desc_counts:
            desc_counts[d] = desc_counts[d] + 1
        else:
            desc_counts[d] = 1
    
    most_common_desc = max(desc_counts, key=desc_counts.get)
    
    daily_data.append({
        "date": current_date,
        "weekday": weekday,
        "temp_avg": avg_temp,
        "temp_max": max_temp,
        "temp_min": min_temp,
        "rain_prob": avg_rain,
        "wind_speed": avg_wind,
        "humidity": avg_humidity,
        "description": most_common_desc,
        "score": score,
        "level": level,
        "desc": desc,
        "activities": activities,
        "reasons": reasons,
        "warnings": warnings
    })

return daily_data[:days]

if st.button("開始規劃旅遊", type="primary", use_container_width=True):
city_info = TAIWAN_CITIES[selected_city]
temp_range = parse_temp_preference(temp_preference)

with st.spinner("正在分析 " + selected_city + " 未來 " + str(forecast_days) + " 天的天氣..."):
    weather_data = get_weather_forecast(city_info["lat"], city_info["lon"], api_key, forecast_days)
    
    if weather_data:
        forecasts = process_forecast_data(weather_data, forecast_days, temp_range, rain_tolerance, selected_activities)
        
        if sort_by_score:
            sorted_forecasts = sorted(forecasts, key=lambda x: x["score"], reverse=True)
        else:
            sorted_forecasts = forecasts
        
        if not show_all_days:
            display_forecasts = []
            for f in sorted_forecasts:
                if f["score"] >= 40:
                    display_forecasts.append(f)
        else:
            display_forecasts = sorted_forecasts
        
        st.success("已完成 " + selected_city + " 的旅遊規劃分析！")
        
        st.markdown("---")
        st.subheader("整體分析")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            best_day = sorted_forecasts[0]
            date_str = best_day["date"].strftime("%m/%d")
            st.metric("最佳出遊日", date_str + " " + best_day["weekday"], delta="評分 " + str(int(best_day["score"])))
        
        with col2:
            total_temp = 0
            for f in forecasts:
                total_temp = total_temp + f["temp_avg"]
            avg_temp = total_temp / len(forecasts)
            st.metric("平均溫度", "{:.1f}°C".format(avg_temp))
        
        with col3:
            good_days = 0
            for f in forecasts:
                if f["score"] >= 70:
                    good_days = good_days + 1
            st.metric("適合出遊天數", str(good_days) + "/" + str(forecast_days) + " 天")
        
        with col4:
            total_rain = 0
            for f in forecasts:
                total_rain = total_rain + f["rain_prob"]
            avg_rain = total_rain / len(forecasts)
            st.metric("平均降雨機率", str(int(avg_rain)) + "%")
        
        st.markdown("---")
        st.subheader(selected_city + " 旅遊推薦行程")
        
        if len(display_forecasts) == 0:
            st.warning("根據您的偏好，這段期間沒有特別推薦的日期。建議調整偏好設定或查看所有天數。")
        else:
            for i, forecast in enumerate(display_forecasts):
                rank = i + 1
                
                if forecast["score"] >= 80:
                    color = "🟢"
                elif forecast["score"] >= 60:
                    color = "🟡"
                elif forecast["score"] >= 40:
                    color = "🟠"
                else:
                    color = "🔴"
                
                date_display = forecast["date"].strftime("%m月%d日")
                score_display = str(int(forecast["score"]))
                expander_title = color + " 推薦 #" + str(rank) + "：" + date_display + " " + forecast["weekday"] + " - " + forecast["level"] + " (評分 " + score_display + ")"
                
                is_expanded = (rank <= 2)
                
                with st.expander(expander_title, expanded=is_expanded):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("溫度", "{:.1f}°C".format(forecast["temp_avg"]))
                        st.caption(str(int(forecast["temp_min"])) + "~" + str(int(forecast["temp_max"])) + "°C")
                    
                    with col2:
                        st.metric("降雨機率", str(int(forecast["rain_prob"])) + "%")
                    
                    with col3:
                        st.metric("風速", "{:.1f} m/s".format(forecast["wind_speed"]))
                    
                    with col4:
                        st.metric("濕度", str(int(forecast["humidity"])) + "%")
                    
                    st.write("**天氣：** " + forecast["description"] + " | " + forecast["desc"])
                    
                    if len(forecast["warnings"]) > 0:
                        st.warning("**注意事項**")
                        for warning in forecast["warnings"]:
                            st.write("- " + warning)
                    
                    if len(forecast["activities"]) > 0:
                        st.success("**推薦行程**")
                        for j in range(len(forecast["activities"])):
                            activity = forecast["activities"][j]
                            reason = forecast["reasons"][j]
                            st.write("**" + activity + "**")
                            st.caption(reason)
                    else:
                        st.info("建議選擇室內活動或彈性安排")
        
        st.markdown("---")
        st.subheader("匯出規劃")
        
        export_data = []
        for f in sorted_forecasts:
            activities_str = "無特別推薦"
            if len(f["activities"]) > 0:
                activities_str = " | ".join(f["activities"])
            
            export_data.append({
                "日期": f["date"].strftime("%Y-%m-%d"),
                "星期": f["weekday"],
                "評分": str(int(f["score"])),
                "等級": f["level"],
                "溫度": "{:.1f}°C".format(f["temp_avg"]),
                "降雨": str(int(f["rain_prob"])) + "%",
                "天氣": f["description"],
                "推薦活動": activities_str
            })
        
        df = pd.DataFrame(export_data)
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        csv_filename = selected_city + "_旅遊規劃_" + datetime.now().strftime("%Y%m%d") + ".csv"
        st.download_button("下載旅遊規劃表 (CSV)", csv, csv_filename, "text/csv", use_container_width=True)

st.markdown("—")
with st.expander("使用指南"):
st.markdown("""
### 如何使用

1. 選擇目的地：在左側選擇想去的台灣縣市
2. 設定天數：選擇 5 天或 10 天預報
3. 選擇偏好：勾選您喜歡的旅遊活動類型
4. 調整設定：設定您的溫度偏好和降雨容忍度
5. 開始規劃：點擊開始規劃旅遊按鈕

### 評分說明

- 極佳 (80-100分)：天氣絕佳，強烈推薦出遊
- 良好 (60-79分)：天氣不錯，適合大多數活動
- 普通 (40-59分)：天氣尚可，建議彈性安排
- 不佳 (0-39分)：天氣較差，建議改期或室內活動

### 小技巧

- 降雨機率 < 30%：通常是好天氣
- 溫度 20-28°C：最舒適的旅遊溫度
- 風速 < 8 m/s：適合戶外活動
- 勾選多種活動類型：獲得更多元的建議
""")

st.markdown("—")
st.caption("台灣天氣旅遊規劃助手 | Made with Streamlit | Powered by OpenWeatherMap")