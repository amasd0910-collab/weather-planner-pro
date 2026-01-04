import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# 頁面設定

st.set_page_config(
page_title=“台灣天氣旅遊規劃”,
page_icon=“🗺️”,
layout=“wide”
)

# 自定義樣式

st.markdown(”””

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

“””, unsafe_allow_html=True)

st.markdown(’<p class="main-title">🗺️ 台灣天氣旅遊規劃助手</p>’, unsafe_allow_html=True)
st.markdown(’<p class="subtitle">根據天氣預報，為您規劃最適合的台灣旅遊行程</p>’, unsafe_allow_html=True)

# 台灣主要城市資料

TAIWAN_CITIES = {
“台北”: {“en”: “Taipei”, “lat”: 25.0330, “lon”: 121.5654},
“新北”: {“en”: “New Taipei”, “lat”: 25.0120, “lon”: 121.4659},
“桃園”: {“en”: “Taoyuan”, “lat”: 24.9936, “lon”: 121.3010},
“台中”: {“en”: “Taichung”, “lat”: 24.1477, “lon”: 120.6736},
“台南”: {“en”: “Tainan”, “lat”: 22.9998, “lon”: 120.2269},
“高雄”: {“en”: “Kaohsiung”, “lat”: 22.6273, “lon”: 120.3014},
“基隆”: {“en”: “Keelung”, “lat”: 25.1276, “lon”: 121.7392},
“新竹”: {“en”: “Hsinchu”, “lat”: 24.8138, “lon”: 120.9675},
“嘉義”: {“en”: “Chiayi”, “lat”: 23.4801, “lon”: 120.4491},
“宜蘭”: {“en”: “Yilan”, “lat”: 24.7022, “lon”: 121.7378},
“花蓮”: {“en”: “Hualien”, “lat”: 23.9871, “lon”: 121.6015},
“台東”: {“en”: “Taitung”, “lat”: 22.7583, “lon”: 121.1444},
“屏東”: {“en”: “Pingtung”, “lat”: 22.6820, “lon”: 120.4818},
“南投”: {“en”: “Nantou”, “lat”: 23.9609, “lon”: 120.9719}
}

# 旅遊活動類型

ACTIVITY_TYPES = {
“🏖️ 海邊活動”: [“衝浪”, “游泳”, “海釣”, “沙灘排球”, “潛水”],
“⛰️ 山區健行”: [“登山”, “森林步道”, “賞楓”, “露營”, “生態觀察”],
“🏛️ 文化古蹟”: [“寺廟參拜”, “古蹟巡禮”, “博物館”, “藝文中心”],
“🍜 美食探索”: [“夜市小吃”, “老街美食”, “特色餐廳”, “咖啡廳”],
“🛍️ 購物休閒”: [“百貨公司”, “商圈逛街”, “市集”, “outlet”],
“🎡 遊樂園區”: [“主題樂園”, “動物園”, “水族館”, “遊樂設施”],
“🚴 戶外運動”: [“自行車”, “路跑”, “球類運動”, “攀岩”],
“♨️ 溫泉度假”: [“泡溫泉”, “SPA”, “度假村”, “民宿體驗”],
“📸 攝影景點”: [“網美景點”, “日出日落”, “風景攝影”, “建築攝影”]
}

# 安全地讀取 API Key

try:
api_key = st.secrets[“OPENWEATHER_API_KEY”]
except:
st.error(“❌ 系統設定錯誤，請確認 API Key 已正確設定”)
st.stop()

# ==================== 側邊欄設定 ====================

with st.sidebar:
st.header(“⚙️ 旅遊偏好設定”)

```
# 地區選擇
st.subheader("📍 目的地")
selected_city = st.selectbox(
    "選擇縣市",
    options=list(TAIWAN_CITIES.keys()),
    help="選擇您想去的台灣縣市"
)

# 預測天數
st.subheader("📅 規劃天數")
forecast_days = st.radio(
    "選擇預測天數",
    options=[5, 10],
    format_func=lambda x: f"{x} 天預報",
    help="5天預報較準確，10天預報參考用"
)

st.markdown("---")

# 旅遊偏好
st.subheader("🎯 旅遊偏好")

selected_activities = st.multiselect(
    "喜歡的活動類型（可複選）",
    options=list(ACTIVITY_TYPES.keys()),
    default=["🍜 美食探索", "🏛️ 文化古蹟"],
    help="選擇您喜歡的旅遊活動類型"
)

# 天氣偏好
st.subheader("🌡️ 天氣偏好")

temp_preference = st.select_slider(
    "溫度偏好",
    options=["怕熱（<25°C）", "適中（20-28°C）", "不怕熱（>20°C）"],
    value="適中（20-28°C）"
)

rain_tolerance = st.slider(
    "降雨容忍度",
    min_value=0,
    max_value=100,
    value=30,
    help="降雨機率超過此值會降低推薦度"
)

st.markdown("---")

# 進階設定
with st.expander("🔧 進階設定"):
    show_all_days = st.checkbox("顯示所有天數（包含不推薦）", value=False)
    sort_by_score = st.checkbox("依適合度排序", value=True)
```

# ==================== 核心功能函數 ====================

@st.cache_data(ttl=1800)  # 快取30分鐘
def get_weather_forecast(lat, lon, api_key, days):
“”“使用經緯度獲取天氣預報”””
try:
# 使用 One Call API 3.0（需要付費）或 5 day forecast（免費）
# 這裡使用免費的 5 day forecast
url = f”http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=zh_tw”
response = requests.get(url, timeout=10)

```
    if response.status_code == 200:
        return response.json()
    else:
        return None
except Exception as e:
    st.error(f"錯誤: {str(e)}")
    return None
```

def parse_temp_preference(pref):
“”“解析溫度偏好”””
if “怕熱” in pref:
return (10, 25)
elif “適中” in pref:
return (20, 28)
else:  # 不怕熱
return (20, 35)

def calculate_weather_score(temp, rain_prob, wind_speed, temp_range, rain_tolerance):
“”“計算天氣適合度評分”””
score = 100

```
# 溫度評分（40%權重）
if temp < temp_range[0]:
    score -= (temp_range[0] - temp) * 3
elif temp > temp_range[1]:
    score -= (temp - temp_range[1]) * 3
else:
    score += 10  # 在範圍內加分

# 降雨評分（40%權重）
if rain_prob > rain_tolerance:
    score -= (rain_prob - rain_tolerance) * 1.5

# 風速評分（20%權重）
if wind_speed > 10:
    score -= (wind_speed - 10) * 2

return max(0, min(100, score))
```

def recommend_activities(score, temp, rain_prob, wind_speed, selected_activities):
“”“根據天氣和偏好推薦活動”””
recommendations = []
reasons = []

```
# 根據天氣評分給予建議
if score >= 85:
    level = "🌟 極佳"
    base_desc = "天氣極佳！"
elif score >= 70:
    level = "😊 良好"
    base_desc = "天氣不錯"
elif score >= 50:
    level = "😐 普通"
    base_desc = "天氣尚可"
else:
    level = "😔 不佳"
    base_desc = "天氣較差"

# 根據用戶偏好和天氣條件推薦
for activity_type in selected_activities:
    if activity_type == "🏖️ 海邊活動":
        if score >= 70 and temp >= 25 and wind_speed < 8:
            recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
            reasons.append("陽光充足、風浪適中")
    
    elif activity_type == "⛰️ 山區健行":
        if score >= 60 and temp < 30 and rain_prob < 40:
            recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
            reasons.append("溫度舒適、不會太熱")
    
    elif activity_type == "🏛️ 文化古蹟":
        if score >= 40:
            recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
            reasons.append("室內為主，較不受天氣影響")
    
    elif activity_type == "🍜 美食探索":
        if score >= 30:
            recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
            reasons.append("隨時都是美食時間！")
    
    elif activity_type == "🛍️ 購物休閒":
        recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
        reasons.append("室內活動，不受天氣限制")
    
    elif activity_type == "🎡 遊樂園區":
        if score >= 65 and rain_prob < 50:
            recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
            reasons.append("戶外設施較多，需好天氣")
    
    elif activity_type == "🚴 戶外運動":
        if score >= 75 and temp < 32 and wind_speed < 10:
            recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
            reasons.append("適合運動的天氣條件")
    
    elif activity_type == "♨️ 溫泉度假":
        if temp < 25 or rain_prob > 50:
            recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
            reasons.append("涼爽或雨天更適合泡湯")
    
    elif activity_type == "📸 攝影景點":
        if score >= 70 and rain_prob < 30:
            recommendations.append(f"{activity_type}：{', '.join(ACTIVITY_TYPES[activity_type][:3])}")
            reasons.append("能見度佳，光線充足")

# 如果沒有符合的推薦，給予替代方案
if not recommendations:
    if rain_prob > 70:
        recommendations.append("🏛️ 室內活動：博物館、購物中心、美食街")
        reasons.append("下雨天建議室內活動")
    elif temp > 33:
        recommendations.append("♨️ 避暑活動：游泳池、有冷氣的地方、夜間活動")
        reasons.append("天氣炎熱，注意防曬")
    else:
        recommendations.append("🚶 輕鬆活動：咖啡廳、室內景點、購物")
        reasons.append("天氣一般，建議輕鬆行程")

# 特別提醒
warnings = []
if rain_prob > 60:
    warnings.append("☔ 建議攜帶雨具")
if temp > 32:
    warnings.append("🌡️ 高溫警報，注意防曬補水")
if temp < 15:
    warnings.append("🧥 氣溫較低，記得保暖")
if wind_speed > 12:
    warnings.append("💨 風速較大，戶外活動注意安全")

return level, base_desc, recommendations, reasons, warnings
```

def process_forecast_data(weather_data, days, temp_range, rain_tolerance, selected_activities):
“”“處理天氣預報資料”””
daily_data = []
current_date = None
daily_records = {
‘temps’: [], ‘rain’: [], ‘wind’: [],
‘humidity’: [], ‘descriptions’: []
}

```
for item in weather_data['list'][:days * 8]:
    dt = datetime.fromtimestamp(item['dt'])
    date = dt.date()
    
    if current_date != date:
        if current_date and daily_records['temps']:
            # 計算當日平均
            avg_temp = sum(daily_records['temps']) / len(daily_records['temps'])
            max_temp = max(daily_records['temps'])
            min_temp = min(daily_records['temps'])
            avg_rain = sum(daily_records['rain']) / len(daily_records['rain']) * 100
            avg_wind = sum(daily_records['wind']) / len(daily_records['wind'])
            avg_humidity = sum(daily_records['humidity']) / len(daily_records['humidity'])
            
            # 計算評分
            score = calculate_weather_score(
                avg_temp, avg_rain, avg_wind,
                temp_range, rain_tolerance
            )
            
            # 推薦活動
            level, desc, activities, reasons, warnings = recommend_activities(
                score, avg_temp, avg_rain, avg_wind, selected_activities
            )
            
            daily_data.append({
                'date': current_date,
                'weekday': ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][current_date.weekday()],
                'temp_avg': avg_temp,
                'temp_max': max_temp,
                'temp_min': min_temp,
                'rain_prob': avg_rain,
                'wind_speed': avg_wind,
                'humidity': avg_humidity,
                'description': max(set(daily_records['descriptions']), 
                                 key=daily_records['descriptions'].count),
                'score': score,
                'level': level,
                'desc': desc,
                'activities': activities,
                'reasons': reasons,
                'warnings': warnings
            })
        
        # 重置
        current_date = date
        daily_records = {
            'temps': [], 'rain': [], 'wind': [],
            'humidity': [], 'descriptions': []
        }
    
    # 收集資料
    daily_records['temps'].append(item['main']['temp'])
    daily_records['rain'].append(item.get('pop', 0))
    daily_records['wind'].append(item['wind']['speed'])
    daily_records['humidity'].append(item['main']['humidity'])
    daily_records['descriptions'].append(item['weather'][0]['description'])

# 處理最後一天
if daily_records['temps']:
    avg_temp = sum(daily_records['temps']) / len(daily_records['temps'])
    max_temp = max(daily_records['temps'])
    min_temp = min(daily_records['temps'])
    avg_rain = sum(daily_records['rain']) / len(daily_records['rain']) * 100
    avg_wind = sum(daily_records['wind']) / len(daily_records['wind'])
    avg_humidity = sum(daily_records['humidity']) / len(daily_records['humidity'])
    
    score = calculate_weather_score(
        avg_temp, avg_rain, avg_wind,
        temp_range, rain_tolerance
    )
    
    level, desc, activities, reasons, warnings = recommend_activities(
        score, avg_temp, avg_rain, avg_wind, selected_activities
    )
    
    daily_data.append({
        'date': current_date,
        'weekday': ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][current_date.weekday()],
        'temp_avg': avg_temp,
        'temp_max': max_temp,
        'temp_min': min_temp,
        'rain_prob': avg_rain,
        'wind_speed': avg_wind,
        'humidity': avg_humidity,
        'description': max(set(daily_records['descriptions']),
                         key=daily_records['descriptions'].count),
        'score': score,
        'level': level,
        'desc': desc,
        'activities': activities,
        'reasons': reasons,
        'warnings': warnings
    })

return daily_data[:days]
```

# ==================== 主要執行 ====================

if st.button(“🚀 開始規劃旅遊”, type=“primary”, use_container_width=True):
city_info = TAIWAN_CITIES[selected_city]
temp_range = parse_temp_preference(temp_preference)

```
with st.spinner(f"正在分析 {selected_city} 未來 {forecast_days} 天的天氣..."):
    weather_data = get_weather_forecast(
        city_info['lat'],
        city_info['lon'],
        api_key,
        forecast_days
    )
    
    if weather_data:
        forecasts = process_forecast_data(
            weather_data,
            forecast_days,
            temp_range,
            rain_tolerance,
            selected_activities
        )
        
        # 排序
        if sort_by_score:
            sorted_forecasts = sorted(forecasts, key=lambda x: x['score'], reverse=True)
        else:
            sorted_forecasts = forecasts
        
        # 過濾
        if not show_all_days:
            display_forecasts = [f for f in sorted_forecasts if f['score'] >= 40]
        else:
            display_forecasts = sorted_forecasts
        
        # ==================== 顯示結果 ====================
        
        st.success(f"✅ 已完成 {selected_city} 的旅遊規劃分析！")
        
        # 摘要統計
        st.markdown("---")
        st.subheader("📊 整體分析")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            best_day = sorted_forecasts[0]
            st.metric(
                "最佳出遊日",
                f"{best_day['date'].strftime('%m/%d')} {best_day['weekday']}",
                delta=f"評分 {best_day['score']:.0f}"
            )
        
        with col2:
            avg_temp = sum(f['temp_avg'] for f in forecasts) / len(forecasts)
            st.metric(
                "平均溫度",
                f"{avg_temp:.1f}°C"
            )
        
        with col3:
            good_days = sum(1 for f in forecasts if f['score'] >= 70)
            st.metric(
                "適合出遊天數",
                f"{good_days}/{forecast_days} 天"
            )
        
        with col4:
            avg_rain = sum(f['rain_prob'] for f in forecasts) / len(forecasts)
            st.metric(
                "平均降雨機率",
                f"{avg_rain:.0f}%"
            )
        
        # 詳細推薦
        st.markdown("---")
        st.subheader(f"🎯 {selected_city} 旅遊推薦行程")
        
        if not display_forecasts:
            st.warning("😔 根據您的偏好，這段期間沒有特別推薦的日期。建議調整偏好設定或查看所有天數。")
        else:
            for i, forecast in enumerate(display_forecasts, 1):
                # 評分顏色
                if forecast['score'] >= 80:
                    color = "🟢"
                elif forecast['score'] >= 60:
                    color = "🟡"
                elif forecast['score'] >= 40:
                    color = "🟠"
                else:
                    color = "🔴"
                
                with st.expander(
                    f"{color} 推薦 #{i}：{forecast['date'].strftime('%m月%d日')} {forecast['weekday']} - "
                    f"{forecast['level']} (評分 {forecast['score']:.0f})",
                    expanded=(i <= 2)
                ):
                    # 天氣資訊
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🌡️ 溫度", f"{forecast['temp_avg']:.1f}°C")
                        st.caption(f"{forecast['temp_min']:.0f}~{forecast['temp_max']:.0f}°C")
                    
                    with col2:
                        st.metric("☔ 降雨機率", f"{forecast['rain_prob']:.0f}%")
                    
                    with col3:
                        st.metric("💨 風速", f"{forecast['wind_speed']:.1f} m/s")
                    
                    with col4:
                        st.metric("💧 濕度", f"{forecast['humidity']:.0f}%")
                    
                    st.write(f"**天氣：** {forecast['description']} | {forecast['desc']}")
                    
                    # 警告
                    if forecast['warnings']:
                        st.warning("⚠️ **注意事項**")
                        for warning in forecast['warnings']:
                            st.write(f"- {warning}")
                    
                    # 推薦活動
                    if forecast['activities']:
                        st.success("✨ **推薦行程**")
                        for activity, reason in zip(forecast['activities'], forecast['reasons']):
                            st.write(f"**{activity}**")
                            st.caption(f"💡 {reason}")
                    else:
                        st.info("💡 建議選擇室內活動或彈性安排")
        
        # 資料匯出
        st.markdown("---")
        st.subheader("💾 匯出規劃")
        
        export_data = []
        for f in sorted_forecasts:
            export_data.append({
                '日期': f['date'].strftime('%Y-%m-%d'),
                '星期': f['weekday'],
                '評分': f"{f['score']:.0f}",
                '等級': f['level'],
                '溫度': f"{f['temp_avg']:.1f}°C",
                '降雨': f"{f['rain_prob']:.0f}%",
                '天氣': f['description'],
                '推薦活動': ' | '.join(f['activities']) if f['activities'] else '無特別推薦'
            })
        
        df = pd.DataFrame(export_data)
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 下載旅遊規劃表 (CSV)",
            csv,
            f"{selected_city}_旅遊規劃_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )
```

# 使用說明

st.markdown(”—”)
with st.expander(“📖 使用指南”):
st.markdown(”””
### 🎯 如何使用

```
1. **選擇目的地**：在左側選擇想去的台灣縣市
2. **設定天數**：選擇 5 天或 10 天預報（5天較準確）
3. **選擇偏好**：勾選您喜歡的旅遊活動類型
4. **調整設定**：設定您的溫度偏好和降雨容忍度
5. **開始規劃**：點擊「開始規劃旅遊」按鈕

### 📊 評分說明

- **🌟 極佳 (80-100分)**：天氣絕佳，強烈推薦出遊
- **😊 良好 (60-79分)**：天氣不錯，適合大多數活動
- **😐 普通 (40-59分)**：天氣尚可，建議彈性安排
- **😔 不佳 (0-39分)**：天氣較差，建議改期或室內活動

### 💡 小技巧

- 降雨機率 < 30%：通常是好天氣
- 溫度 20-28°C：最舒適的旅遊溫度
- 風速 < 8 m/s：適合戶外活動
- 勾選多種活動類型：獲得更多元的建議

### 🌤️ 天氣資料來源

- 資料來源：OpenWeatherMap
- 更新頻率：每小時更新
- 5天預報：較準確
- 10天預報：僅供參考
""")
```

st.markdown(”—”)
st.caption(“🗺️ 台灣天氣旅遊規劃助手 | Made with ❤️ using Streamlit | Powered by OpenWeatherMap”)