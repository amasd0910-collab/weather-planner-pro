import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# 頁面設定
st.set_page_config(
    page_title="天氣行程規劃",
    page_icon="🌤️",
    layout="wide"
)

# 標題
st.title("🌤️ 天氣行程規劃助手")
st.write("根據天氣預報規劃最適合的行程")

# 側邊欄設定
st.sidebar.header("⚙️ 設定")

api_key = st.sidebar.text_input(
    "OpenWeatherMap API Key",
    type="password",
    help="到 https://openweathermap.org/api 註冊"
)

temp_range = st.sidebar.slider(
    "舒適溫度範圍 (°C)",
    0, 40, (18, 28)
)

rain_tolerance = st.sidebar.slider(
    "降雨容忍度 (%)",
    0, 100, 30
)

# 主要輸入
col1, col2 = st.columns(2)
with col1:
    city = st.text_input("城市名稱", "Taipei")
with col2:
    days = st.slider("規劃天數", 3, 7, 5)

# 獲取天氣
def get_weather(city, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"錯誤代碼: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"錯誤: {str(e)}")
        return None

# 計算評分
def calculate_score(temp, rain_prob, temp_range, rain_tolerance):
    score = 100
    
    # 溫度評分
    if temp < temp_range[0]:
        score -= (temp_range[0] - temp) * 2
    elif temp > temp_range[1]:
        score -= (temp - temp_range[1]) * 2
    
    # 降雨評分
    if rain_prob > rain_tolerance:
        score -= (rain_prob - rain_tolerance) * 0.8
    
    return max(0, min(100, score))

# 推薦活動
def recommend_activity(score):
    if score >= 80:
        return "🌟 極佳", "戶外運動、觀光旅遊"
    elif score >= 60:
        return "🌤️ 良好", "城市漫步、咖啡廳"
    elif score >= 40:
        return "☁️ 普通", "博物館、美食探索"
    else:
        return "🌧️ 不佳", "室內活動、購物"

# 處理天氣資料
def process_weather(data, days, temp_range, rain_tolerance):
    daily_data = []
    current_date = None
    daily_temps = []
    daily_rain = []
    
    for item in data['list'][:days * 8]:
        dt = datetime.fromtimestamp(item['dt'])
        date = dt.date()
        
        if current_date != date:
            if current_date and daily_temps:
                avg_temp = sum(daily_temps) / len(daily_temps)
                avg_rain = sum(daily_rain) / len(daily_rain) * 100
                score = calculate_score(avg_temp, avg_rain, temp_range, rain_tolerance)
                
                daily_data.append({
                    'date': current_date,
                    'temp': avg_temp,
                    'rain': avg_rain,
                    'score': score
                })
            
            current_date = date
            daily_temps = []
            daily_rain = []
        
        daily_temps.append(item['main']['temp'])
        daily_rain.append(item.get('pop', 0))
    
    # 最後一天
    if daily_temps:
        avg_temp = sum(daily_temps) / len(daily_temps)
        avg_rain = sum(daily_rain) / len(daily_rain) * 100
        score = calculate_score(avg_temp, avg_rain, temp_range, rain_tolerance)
        
        daily_data.append({
            'date': current_date,
            'temp': avg_temp,
            'rain': avg_rain,
            'score': score
        })
    
    return daily_data[:days]

# 執行按鈕
if st.button("🔍 開始分析", type="primary"):
    if not api_key:
        st.warning("⚠️ 請先輸入 API Key")
    else:
        with st.spinner("分析中..."):
            weather_data = get_weather(city, api_key)
            
            if weather_data:
                forecasts = process_weather(weather_data, days, temp_range, rain_tolerance)
                sorted_forecasts = sorted(forecasts, key=lambda x: x['score'], reverse=True)
                
                st.success(f"✅ 已完成 {city} 的分析！")
                
                # 顯示結果
                st.subheader("📊 推薦行程")
                
                for i, f in enumerate(sorted_forecasts, 1):
                    level, activity = recommend_activity(f['score'])
                    
                    with st.expander(
                        f"推薦 #{i}: {f['date'].strftime('%m月%d日')} - {level} ({f['score']:.0f}分)",
                        expanded=(i <= 2)
                    ):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("溫度", f"{f['temp']:.1f}°C")
                        with col2:
                            st.metric("降雨機率", f"{f['rain']:.0f}%")
                        with col3:
                            st.metric("評分", f"{f['score']:.0f}")
                        
                        st.write(f"**推薦活動**: {activity}")
                
                # 資料表
                st.subheader("📋 完整資料")
                df = pd.DataFrame([{
                    '日期': f['date'].strftime('%Y-%m-%d'),
                    '溫度': f"{f['temp']:.1f}°C",
                    '降雨': f"{f['rain']:.0f}%",
                    '評分': f"{f['score']:.0f}"
                } for f in sorted_forecasts])
                st.dataframe(df, use_container_width=True)
                
                # 下載
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "💾 下載 CSV",
                    csv,
                    f"{city}_weather_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )

# 說明
with st.expander("📖 使用說明"):
    st.markdown("""
    ### 如何使用
    1. 到 [OpenWeatherMap](https://openweathermap.org/api) 註冊並取得免費 API Key
    2. 在左側欄位輸入 API Key
    3. 設定您的溫度偏好和降雨容忍度
    4. 輸入城市名稱（英文）
    5. 點擊「開始分析」
    
    ### 評分標準
    - 80-100分：極佳天氣
    - 60-79分：良好天氣
    - 40-59分：普通天氣
    - 0-39分：不佳天氣
    """)

st.markdown("---")
st.caption("Made with ❤️ using Streamlit | Powered by OpenWeatherMap")
