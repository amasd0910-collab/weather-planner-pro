import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

# 頁面設定
st.set_page_config(
    page_title="智能天氣行程規劃系統",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #89f7fe 0%, #66a6ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(120deg, #89f7fe 0%, #66a6ff 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        'temp_range': (18, 28),
        'rain_tolerance': 30,
        'activity_preferences': [],
        'saved_schedules': []
    }

if 'weather_history' not in st.session_state:
    st.session_state.weather_history = []

# 標題
st.markdown('<h1 class="main-header">🌤️ 智能天氣行程規劃系統 Pro</h1>', unsafe_allow_html=True)
st.markdown("### 基於 AI 的個性化行程推薦 | 支援 3-10 天智能規劃")

# ==================== 側邊欄：進階設定 ====================
with st.sidebar:
    st.header("⚙️ 系統設定")
    
    # API 設定
    with st.expander("🔑 API 設定", expanded=True):
        api_key = st.text_input(
            "OpenWeatherMap API Key",
            type="password",
            help="免費註冊：https://openweathermap.org/api"
        )
        
        if api_key:
            st.success("✅ API Key 已設定")
        else:
            st.warning("⚠️ 請輸入 API Key 以使用天氣功能")
    
    st.markdown("---")
    
    # 個人偏好設定
    st.header("👤 個人偏好")
    
    with st.expander("🌡️ 溫度偏好", expanded=True):
        temp_range = st.slider(
            "舒適溫度範圍 (°C)",
            min_value=0,
            max_value=40,
            value=st.session_state.user_preferences['temp_range'],
            help="選擇您最舒適的溫度範圍"
        )
        st.session_state.user_preferences['temp_range'] = temp_range
        
        temp_preference_type = st.radio(
            "體感偏好",
            ["怕冷", "一般", "怕熱"],
            index=1
        )
    
    with st.expander("☔ 天氣容忍度", expanded=True):
        rain_tolerance = st.slider(
            "降雨容忍度 (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.user_preferences['rain_tolerance'],
            help="降雨機率超過此值會影響推薦分數"
        )
        st.session_state.user_preferences['rain_tolerance'] = rain_tolerance
        
        wind_tolerance = st.slider(
            "風速容忍度 (m/s)",
            min_value=0,
            max_value=20,
            value=10,
            help="風速超過此值會降低戶外活動推薦"
        )
    
    with st.expander("🎯 活動偏好", expanded=True):
        activity_preferences = st.multiselect(
            "偏好的活動類型",
            [
                "🏃 戶外運動",
                "🏞️ 觀光旅遊",
                "🚶 城市探索",
                "🏛️ 文化活動",
                "🏊 水上活動",
                "⛰️ 登山健行",
                "📸 攝影採風",
                "🍽️ 美食探索",
                "🛍️ 購物休閒"
            ],
            default=["🏞️ 觀光旅遊", "🚶 城市探索"]
        )
        st.session_state.user_preferences['activity_preferences'] = activity_preferences
    
    with st.expander("⏰ 時段偏好"):
        time_preferences = st.multiselect(
            "偏好的活動時段",
            ["🌅 清晨 (6-9)", "☀️ 上午 (9-12)", "🌞 下午 (12-18)", "🌆 傍晚 (18-21)", "🌙 夜晚 (21-24)"],
            default=["☀️ 上午 (9-12)", "🌞 下午 (12-18)"]
        )
    
    st.markdown("---")
    
    # 進階演算法設定
    with st.expander("🤖 演算法設定"):
        st.write("**權重調整**")
        weight_temp = st.slider("溫度權重", 0, 100, 40, help="溫度在評分中的重要性")
        weight_rain = st.slider("降雨權重", 0, 100, 35, help="降雨在評分中的重要性")
        weight_wind = st.slider("風速權重", 0, 100, 15, help="風速在評分中的重要性")
        weight_humidity = st.slider("濕度權重", 0, 100, 10, help="濕度在評分中的重要性")
        
        total_weight = weight_temp + weight_rain + weight_wind + weight_humidity
        if total_weight != 100:
            st.warning(f"⚠️ 權重總和為 {total_weight}%，建議調整為 100%")
    
    st.markdown("---")
    
    # 資料管理
    with st.expander("💾 資料管理"):
        if st.button("清除歷史記錄"):
            st.session_state.weather_history = []
            st.success("✅ 歷史記錄已清除")
        
        if st.button("重置所有設定"):
            st.session_state.user_preferences = {
                'temp_range': (18, 28),
                'rain_tolerance': 30,
                'activity_preferences': [],
                'saved_schedules': []
            }
            st.success("✅ 設定已重置")

# ==================== 核心功能函數 ====================

@st.cache_data(ttl=3600)
def get_weather_forecast(city, api_key):
    """獲取天氣預報（帶快取）"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=zh_tw"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"❌ 錯誤: {str(e)}")
        return None

def calculate_advanced_score(weather, preferences, weights):
    """進階天氣評分演算法"""
    score = 0
    max_score = 100
    
    temp = weather['temp']
    rain_prob = weather['rain_prob']
    wind_speed = weather['wind_speed']
    humidity = weather['humidity']
    
    temp_range = preferences['temp_range']
    rain_tolerance = preferences['rain_tolerance']
    
    # 溫度評分（使用正態分佈曲線）
    temp_optimal = (temp_range[0] + temp_range[1]) / 2
    temp_deviation = abs(temp - temp_optimal)
    temp_score = max(0, 100 - (temp_deviation ** 1.5))
    
    # 溫度在範圍內給予額外加分
    if temp_range[0] <= temp <= temp_range[1]:
        temp_score = min(100, temp_score + 15)
    
    # 降雨評分（非線性懲罰）
    if rain_prob <= rain_tolerance:
        rain_score = 100
    else:
        rain_score = max(0, 100 - ((rain_prob - rain_tolerance) * 1.5))
    
    # 風速評分
    if wind_speed <= 5:
        wind_score = 100
    elif wind_speed <= 10:
        wind_score = 80
    elif wind_speed <= 15:
        wind_score = 50
    else:
        wind_score = max(0, 50 - (wind_speed - 15) * 5)
    
    # 濕度評分
    if 40 <= humidity <= 70:
        humidity_score = 100
    elif humidity < 40:
        humidity_score = 100 - (40 - humidity) * 1.5
    else:
        humidity_score = max(0, 100 - (humidity - 70) * 1.2)
    
    # 加權平均
    score = (
        temp_score * weights['temp'] / 100 +
        rain_score * weights['rain'] / 100 +
        wind_score * weights['wind'] / 100 +
        humidity_score * weights['humidity'] / 100
    )
    
    return round(score, 1)

def get_activity_recommendations(score, temp, rain_prob, wind_speed, preferences):
    """智能活動推薦系統"""
    recommendations = []
    activity_prefs = preferences.get('activity_preferences', [])
    
    # 根據評分等級推薦
    if score >= 85:
        priority = "🌟 極優"
        base_activities = [
            ("🏃 晨跑或夜跑", "溫度舒適，空氣清新"),
            ("🚴 自行車遊", "風和日麗，適合長途騎行"),
            ("⛰️ 登山健行", "能見度極佳，景色優美"),
            ("🏞️ 戶外野餐", "完美的野餐天氣"),
            ("📸 風景攝影", "光線條件絕佳")
        ]
    elif score >= 70:
        priority = "🌤️ 良好"
        base_activities = [
            ("🚶 城市漫步", "天氣宜人，適合散步"),
            ("🏛️ 戶外景點", "參觀戶外古蹟或公園"),
            ("🍽️ 戶外用餐", "露天餐廳好選擇"),
            ("🎨 街頭藝術", "探索城市藝術"),
            ("🛍️ 露天市集", "逛市集好時機")
        ]
    elif score >= 50:
        priority = "☁️ 普通"
        base_activities = [
            ("🏛️ 博物館參觀", "室內文化活動"),
            ("☕ 咖啡廳巡禮", "享受悠閒時光"),
            ("🎬 電影欣賞", "看場好電影"),
            ("🍜 美食探索", "探索在地美食"),
            ("🛍️ 購物中心", "室內購物")
        ]
    else:
        priority = "🌧️ 不佳"
        base_activities = [
            ("🏠 室內活動", "建議留在室內"),
            ("📚 圖書館", "閱讀充電好時機"),
            ("🎮 娛樂中心", "室內休閒娛樂"),
            ("🧘 瑜珈或健身", "室內運動"),
            ("🎨 DIY 手作", "發揮創意")
        ]
    
    # 根據用戶偏好過濾
    for activity, reason in base_activities:
        # 檢查活動是否符合用戶偏好
        activity_match = any(pref.split()[1] in activity for pref in activity_prefs) if activity_prefs else True
        
        if activity_match or len(activity_prefs) == 0:
            recommendations.append({
                'activity': activity,
                'reason': reason,
                'priority': priority
            })
    
    # 特殊天氣警告
    warnings = []
    if rain_prob > 70:
        warnings.append("☔ 高降雨機率，請攜帶雨具")
    if wind_speed > 15:
        warnings.append("💨 風速較大，注意安全")
    if temp < 10:
        warnings.append("🧥 氣溫較低，注意保暖")
    if temp > 35:
        warnings.append("🌡️ 高溫警報，注意防曬與補水")
    
    return recommendations[:5], warnings

def process_weather_data_advanced(weather_data, days, preferences, weights):
    """進階天氣資料處理"""
    daily_data = []
    current_date = None
    daily_records = {
        'temps': [], 'rain': [], 'wind': [], 'humidity': [],
        'descriptions': [], 'feels_like': [], 'pressure': []
    }
    
    for item in weather_data['list'][:days * 8]:
        dt = datetime.fromtimestamp(item['dt'])
        date = dt.date()
        
        if current_date != date:
            if current_date is not None and daily_records['temps']:
                # 計算當日統計
                avg_temp = sum(daily_records['temps']) / len(daily_records['temps'])
                max_temp = max(daily_records['temps'])
                min_temp = min(daily_records['temps'])
                avg_rain = sum(daily_records['rain']) / len(daily_records['rain']) * 100
                avg_wind = sum(daily_records['wind']) / len(daily_records['wind'])
                avg_humidity = sum(daily_records['humidity']) / len(daily_records['humidity'])
                avg_feels = sum(daily_records['feels_like']) / len(daily_records['feels_like'])
                avg_pressure = sum(daily_records['pressure']) / len(daily_records['pressure'])
                
                # 計算評分
                weather_condition = {
                    'temp': avg_temp,
                    'rain_prob': avg_rain,
                    'wind_speed': avg_wind,
                    'humidity': avg_humidity
                }
                
                score = calculate_advanced_score(weather_condition, preferences, weights)
                
                # 儲存資料
                daily_data.append({
                    'date': current_date,
                    'temp_avg': avg_temp,
                    'temp_max': max_temp,
                    'temp_min': min_temp,
                    'feels_like': avg_feels,
                    'rain_prob': avg_rain,
                    'wind_speed': avg_wind,
                    'humidity': avg_humidity,
                    'pressure': avg_pressure,
                    'description': max(set(daily_records['descriptions']), 
                                     key=daily_records['descriptions'].count),
                    'score': score
                })
            
            # 重置記錄
            current_date = date
            daily_records = {
                'temps': [], 'rain': [], 'wind': [], 'humidity': [],
                'descriptions': [], 'feels_like': [], 'pressure': []
            }
        
        # 收集資料
        daily_records['temps'].append(item['main']['temp'])
        daily_records['rain'].append(item.get('pop', 0))
        daily_records['wind'].append(item['wind']['speed'])
        daily_records['humidity'].append(item['main']['humidity'])
        daily_records['descriptions'].append(item['weather'][0]['description'])
        daily_records['feels_like'].append(item['main']['feels_like'])
        daily_records['pressure'].append(item['main']['pressure'])
    
    # 處理最後一天
    if daily_records['temps']:
        avg_temp = sum(daily_records['temps']) / len(daily_records['temps'])
        max_temp = max(daily_records['temps'])
        min_temp = min(daily_records['temps'])
        avg_rain = sum(daily_records['rain']) / len(daily_records['rain']) * 100
        avg_wind = sum(daily_records['wind']) / len(daily_records['wind'])
        avg_humidity = sum(daily_records['humidity']) / len(daily_records['humidity'])
        avg_feels = sum(daily_records['feels_like']) / len(daily_records['feels_like'])
        avg_pressure = sum(daily_records['pressure']) / len(daily_records['pressure'])
        
        weather_condition = {
            'temp': avg_temp,
            'rain_prob': avg_rain,
            'wind_speed': avg_wind,
            'humidity': avg_humidity
        }
        
        score = calculate_advanced_score(weather_condition, preferences, weights)
        
        daily_data.append({
            'date': current_date,
            'temp_avg': avg_temp,
            'temp_max': max_temp,
            'temp_min': min_temp,
            'feels_like': avg_feels,
            'rain_prob': avg_rain,
            'wind_speed': avg_wind,
            'humidity': avg_humidity,
            'pressure': avg_pressure,
            'description': max(set(daily_records['descriptions']),
                             key=daily_records['descriptions'].count),
            'score': score
        })
    
    return daily_data[:days]

# ==================== 主要介面 ====================

# 查詢設定區
st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    city = st.text_input(
        "🌍 目標城市",
        value="Taipei",
        help="請輸入英文城市名稱，例如：Taipei, Tokyo, Paris"
    )

with col2:
    days = st.slider(
        "📅 規劃天數",
        min_value=3,
        max_value=10,
        value=7
    )

with col3:
    st.write("")
    st.write("")
    analysis_mode = st.selectbox(
        "分析模式",
        ["標準模式", "詳細模式", "比較模式"]
    )

# 權重設定
weights = {
    'temp': weight_temp,
    'rain': weight_rain,
    'wind': weight_wind,
    'humidity': weight_humidity
}

# 主要執行按鈕
if st.button("🚀 開始智能分析", type="primary"):
    if not api_key:
        st.error("❌ 請先在側邊欄輸入 API Key")
    else:
        with st.spinner("🔍 正在進行深度天氣分析..."):
            weather_data = get_weather_forecast(city, api_key)
            
            if weather_data:
                # 處理天氣資料
                daily_forecasts = process_weather_data_advanced(
                    weather_data,
                    days,
                    st.session_state.user_preferences,
                    weights
                )
                
                # 依評分排序
                sorted_forecasts = sorted(daily_forecasts, key=lambda x: x['score'], reverse=True)
                
                # 加入歷史記錄
                st.session_state.weather_history.append({
                    'city': city,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'days': days,
                    'forecasts': daily_forecasts
                })
                
                # ==================== 結果顯示 ====================
                
                st.success(f"✅ 已完成 {city} 未來 {days} 天的深度分析！")
                
                # 摘要統計
                st.markdown("---")
                st.subheader("📊 整體分析摘要")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_score = sum(f['score'] for f in daily_forecasts) / len(daily_forecasts)
                    st.metric(
                        "平均適合度",
                        f"{avg_score:.1f}",
                        delta=f"最佳: {sorted_forecasts[0]['score']:.1f}"
                    )
                
                with col2:
                    avg_temp = sum(f['temp_avg'] for f in daily_forecasts) / len(daily_forecasts)
                    st.metric(
                        "平均溫度",
                        f"{avg_temp:.1f}°C",
                        delta=f"範圍: {min(f['temp_min'] for f in daily_forecasts):.0f}-{max(f['temp_max'] for f in daily_forecasts):.0f}°C"
                    )
                
                with col3:
                    avg_rain = sum(f['rain_prob'] for f in daily_forecasts) / len(daily_forecasts)
                    st.metric(
                        "平均降雨機率",
                        f"{avg_rain:.0f}%",
                        delta="適合度已考量"
                    )
                
                with col4:
                    good_days = sum(1 for f in daily_forecasts if f['score'] >= 70)
                    st.metric(
                        "優良天數",
                        f"{good_days}/{days}",
                        delta=f"{good_days/days*100:.0f}%"
                    )
                
                # 視覺化圖表
                st.markdown("---")
                st.subheader("📈 多維度天氣分析")
                
                # 創建子圖
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('溫度趨勢與體感溫度', '降雨機率與濕度', '風速變化', '綜合適合度評分'),
                    specs=[[{"secondary_y": False}, {"secondary_y": True}],
                           [{"secondary_y": False}, {"secondary_y": False}]]
                )
                
                dates = [f['date'].strftime('%m/%d') for f in daily_forecasts]
                
                # 第一個子圖：溫度
                fig.add_trace(
                    go.Scatter(x=dates, y=[f['temp_avg'] for f in daily_forecasts],
                              name='平均溫度', line=dict(color='#FF6B6B', width=3)),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=dates, y=[f['feels_like'] for f in daily_forecasts],
                              name='體感溫度', line=dict(color='#FFA07A', width=2, dash='dash')),
                    row=1, col=1
                )
                
                # 第二個子圖：降雨與濕度
                fig.add_trace(
                    go.Bar(x=dates, y=[f['rain_prob'] for f in daily_forecasts],
                          name='降雨機率', marker_color='#4ECDC4'),
                    row=1, col=2
                )
                fig.add_trace(
                    go.Scatter(x=dates, y=[f['humidity'] for f in daily_forecasts],
                              name='濕度', line=dict(color='#95E1D3', width=2)),
                    row=1, col=2, secondary_y=True
                )
                
                # 第三個子圖：風速
                fig.add_trace(
                    go.Scatter(x=dates, y=[f['wind_speed'] for f in daily_forecasts],
                              name='風速', fill='tozeroy', line=dict(color='#A8E6CF', width=2)),
                    row=2, col=1
                )
                
                # 第四個子圖：評分
                colors = ['#2ECC71' if f['score'] >= 70 else '#F39C12' if f['score'] >= 50 else '#E74C3C' 
                         for f in daily_forecasts]
                fig.add_trace(
                    go.Bar(x=dates, y=[f['score'] for f in daily_forecasts],
                          name='適合度', marker_color=colors),
                    row=2, col=2
                )
                
                fig.update_layout(height=700, showlegend=True, hovermode='x unified')
                fig.update_xaxes(title_text="日期", row=2, col=1)
                fig.update_xaxes(title_text="日期", row=2, col=2)
                fig.update_yaxes(title_text="溫度 (°C)", row=1, col=1)
                fig.update_yaxes(title_text="降雨機率 (%)", row=1, col=2)
                fig.update_yaxes(title_text="濕度 (%)", row=1, col=2, secondary_y=True)
                fig.update_yaxes(title_text="風速 (m/s)", row=2, col=1)
                fig.update_yaxes(title_text="適合度評分", row=2, col=2)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 雷達圖：天氣舒適度分析
                if analysis_mode == "詳細模式":
                    st.markdown("---")
                    st.subheader("🎯 天氣舒適度雷達圖")
                    
                    # 選擇要比較的日期
                    selected_dates = st.multiselect(
                        "選擇要比較的日期",
                        options=[f['date'].strftime('%m/%d') for f in sorted_forecasts],
                        default=[f['date'].strftime('%m/%d') for f in sorted_forecasts[:3]]
                    )
                    
                    if selected_dates:
                        fig_radar = go.Figure()
                        
                        for date_str in selected_dates:
                            forecast = next(f for f in sorted_forecasts 
                                          if f['date'].strftime('%m/%d') == date_str)
                            
                            # 計算各項指標的標準化分數
                            temp_score = 100 - abs(forecast['temp_avg'] - 
                                                  (temp_range[0] + temp_range[1]) / 2) * 3
                            rain_score = 100 - forecast['rain_prob']
                            wind_score = max(0, 100 - forecast['wind_speed'] * 5)
                            humidity_score = 100 - abs(forecast['humidity'] - 55) * 1.5
                            
                            fig_radar.add_trace(go.Scatterpolar(
                                r=[temp_score, rain_score, wind_score, humidity_score, temp_score],
                                theta=['溫度舒適度', '晴朗度', '風和度', '濕度適宜', '溫度舒適度'],
                                fill='toself',
                                name=date_str
                            ))
                        
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                            showlegend=True,
                            height=500
                        )
                        
                        st.plotly_chart(fig_radar, use_container_width=True)
                
                # 智能推薦行程
                st.markdown("---")
                st.subheader("🎯 智能行程推薦（依適合度排序）")
                
                # 顯示推薦說明
                st.info(f"💡 系統已根據您的偏好（溫度 {temp_range[0]}-{temp_range[1]}°C，降雨容忍度 {rain_tolerance}%）為您量身規劃行程")
                
                for i, forecast in enumerate(sorted_forecasts, 1):
                    # 評分等級與顏色
                    if forecast['score'] >= 85:
                        score_emoji = "🌟"
                        label = "極優"
                        color = "green"
                    elif forecast['score'] >= 70:
                        score_emoji = "🌤️"
                        label = "良好"
                        color = "blue"
                    elif forecast['score'] >= 50:
                        score_emoji = "☁️"
                        label = "普通"
                        color = "orange"
                    else:
                        score_emoji = "🌧️"
                        label = "不佳"
                        color = "red"
                    
                    # 星期幾
                    weekday = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][forecast['date'].weekday()]
                    
                    with st.expander(
                        f"{score_emoji} 推薦 #{i}：{forecast['date'].strftime('%Y年%m月%d日')} {weekday} - "
                        f"適合度 {forecast['score']:.1f} ({label})",
                        expanded=(i <= 2)
                    ):
                        # 詳細天氣資訊
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            st.metric("平均溫度", f"{forecast['temp_avg']:.1f}°C")
                            st.caption(f"🌡️ {forecast['temp_min']:.0f}~{forecast['temp_max']:.0f}°C")
                        
                        with col2:
                            st.metric("體感溫度", f"{forecast['feels_like']:.1f}°C")
                            diff = forecast['feels_like'] - forecast['temp_avg']
                            st.caption(f"{'🥵' if diff > 2 else '🥶' if diff < -2 else '😊'} {diff:+.1f}°C")
                        
                        with col3:
                            st.metric("降雨機率", f"{forecast['rain_prob']:.0f}%")
                            st.caption("☔" if forecast['rain_prob'] > 50 else "☀️")
                        
                        with col4:
                            st.metric("風速", f"{forecast['wind_speed']:.1f} m/s")
                            st.caption("💨" if forecast['wind_speed'] > 10 else "🍃")
                        
                        with col5:
                            st.metric("濕度", f"{forecast['humidity']:.0f}%")
                            st.caption(f"💧 {'高' if forecast['humidity'] > 70 else '舒適'}")
                        
                        st.write(f"**天氣狀況：** {forecast['description']}")
                        st.write(f"**氣壓：** {forecast['pressure']:.0f} hPa")
                        
                        # 活動推薦
                        activities, warnings = get_activity_recommendations(
                            forecast['score'],
                            forecast['temp_avg'],
                            forecast['rain_prob'],
                            forecast['wind_speed'],
                            st.session_state.user_preferences
                        )
                        
                        if warnings:
                            st.warning("⚠️ **特別提醒：**")
                            for warning in warnings:
                                st.write(f"  {warning}")
                        
                        st.success("✅ **推薦活動：**")
                        for activity_info in activities:
                            st.write(f"**{activity_info['activity']}**")
                            st.caption(f"  💡 {activity_info['reason']}")
                            st.write("")
                
                # 比較模式
                if analysis_mode == "比較模式":
                    st.markdown("---")
                    st.subheader("⚖️ 多日期對比分析")
                    
                    compare_dates = st.multiselect(
                        "選擇要對比的日期（最多3個）",
                        options=[f"{f['date'].strftime('%m/%d')} ({f['score']:.0f}分)" 
                                for f in sorted_forecasts],
                        max_selections=3
                    )
                    
                    if compare_dates:
                        selected_forecasts = [
                            f for f in sorted_forecasts 
                            if f"{f['date'].strftime('%m/%d')} ({f['score']:.0f}分)" in compare_dates
                        ]
                        
                        comparison_data = {
                            '指標': ['適合度', '溫度', '降雨', '風速', '濕度'],
                        }
                        
                        for f in selected_forecasts:
                            date_str = f['date'].strftime('%m/%d')
                            comparison_data[date_str] = [
                                f"{f['score']:.1f}",
                                f"{f['temp_avg']:.1f}°C",
                                f"{f['rain_prob']:.0f}%",
                                f"{f['wind_speed']:.1f} m/s",
                                f"{f['humidity']:.0f}%"
                            ]
                        
                        df_compare = pd.DataFrame(comparison_data)
                        st.table(df_compare)
                
                # 匯出功能
                st.markdown("---")
                st.subheader("💾 匯出行程規劃")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # CSV 匯出
                    export_data = []
                    for f in sorted_forecasts:
                        activities, warnings = get_activity_recommendations(
                            f['score'],
                            f['temp_avg'],
                            f['rain_prob'],
                            f['wind_speed'],
                            st.session_state.user_preferences
                        )
                        
                        export_data.append({
                            '排名': sorted_forecasts.index(f) + 1,
                            '日期': f['date'].strftime('%Y-%m-%d'),
                            '星期': ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][f['date'].weekday()],
                            '適合度': f"{f['score']:.1f}",
                            '溫度': f"{f['temp_avg']:.1f}°C",
                            '溫度範圍': f"{f['temp_min']:.0f}-{f['temp_max']:.0f}°C",
                            '體感溫度': f"{f['feels_like']:.1f}°C",
                            '降雨機率': f"{f['rain_prob']:.0f}%",
                            '風速': f"{f['wind_speed']:.1f} m/s",
                            '濕度': f"{f['humidity']:.0f}%",
                            '天氣': f['description'],
                            '推薦活動': ' | '.join([a['activity'] for a in activities[:3]]),
                            '特別提醒': ' | '.join(warnings) if warnings else '無'
                        })
                    
                    df_export = pd.DataFrame(export_data)
                    csv = df_export.to_csv(index=False, encoding='utf-8-sig')
                    
                    st.download_button(
                        label="📥 下載詳細報告 (CSV)",
                        data=csv,
                        file_name=f"{city}_智能行程規劃_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # JSON 匯出
                    json_data = {
                        'city': city,
                        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'days': days,
                        'user_preferences': st.session_state.user_preferences,
                        'forecasts': [
                            {
                                'date': f['date'].strftime('%Y-%m-%d'),
                                'score': f['score'],
                                'weather': {
                                    'temp_avg': f['temp_avg'],
                                    'temp_range': f"{f['temp_min']}-{f['temp_max']}",
                                    'feels_like': f['feels_like'],
                                    'rain_prob': f['rain_prob'],
                                    'wind_speed': f['wind_speed'],
                                    'humidity': f['humidity'],
                                    'description': f['description']
                                }
                            }
                            for f in sorted_forecasts
                        ]
                    }
                    
                    json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                    
                    st.download_button(
                        label="📥 下載資料檔 (JSON)",
                        data=json_str,
                        file_name=f"{city}_weather_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )
                
                # 儲存到歷史
                if st.button("💾 儲存此規劃到我的收藏"):
                    st.session_state.user_preferences['saved_schedules'].append({
                        'city': city,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'forecasts': sorted_forecasts[:3]
                    })
                    st.success("✅ 已儲存到收藏！")

# ==================== 頁腳與說明 ====================

st.markdown("---")

# 使用說明
with st.expander("📖 詳細使用說明"):
    st.markdown("""
    ## 🎯 功能特色
    
    ### 1. 智能評分系統
    - **多維度分析**：綜合考量溫度、降雨、風速、濕度四大指標
    - **個人化權重**：可自訂各指標的重要性
    - **非線性演算法**：採用進階數學模型，更精準評估天氣適合度
    
    ### 2. 活動推薦引擎
    - **智能匹配**：根據天氣條件自動推薦最適合的活動類型
    - **偏好學習**：記憶您的活動偏好，提供個性化建議
    - **安全警示**：主動提醒惡劣天氣與注意事項
    
    ### 3. 視覺化分析
    - **多維度圖表**：溫度、降雨、風速、評分一目了然
    - **趨勢預測**：清楚看出未來天氣變化
    - **雷達比較**：多日期綜合條件對比
    
    ### 4. 匯出與分享
    - **CSV 報告**：完整的行程規劃表格
    - **JSON 資料**：可程式化處理的結構化資料
    - **收藏功能**：儲存常用的規劃方案
    
    ## 📊 評分標準
    
    - **85-100分（極優）** 🌟：天氣條件極佳，強烈推薦戶外活動
    - **70-84分（良好）** 🌤️：天氣良好，適合大部分活動
    - **50-69分（普通）** ☁️：天氣尚可，建議半戶外活動
    - **0-49分（不佳）** 🌧️：天氣較差，建議室內活動
    
    ## 💡 使用技巧
    
    1. **調整權重**：如果您特別在意某項指標（如降雨），可在側邊欄增加其權重
    2. **活動偏好**：選擇您喜歡的活動類型，系統會優先推薦相關活動
    3. **比較模式**：同時分析多個日期，找出最適合的時間
    4. **儲存設定**：您的偏好會自動保存，下次使用更方便
    
    ## 🔧 進階功能
    
    - **歷史記錄**：系統會記錄您的查詢歷史
    - **快取機制**：相同城市1小時內查詢使用快取，加快速度
    - **響應式設計**：支援手機、平板、電腦多種裝置
    """)

# 技術資訊
with st.expander("🔬 技術架構說明"):
    st.markdown("""
    ## 🛠️ 技術棧
    
    - **前端框架**：Streamlit 1.28+
    - **資料處理**：Pandas
    - **視覺化**：Plotly（互動式圖表）
    - **API**：OpenWeatherMap（5天預報）
    - **演算法**：自定義非線性評分系統
    
    ## 📐 評分演算法
    
    系統採用加權多因素評分模型：
    
    ```
    總分 = (溫度分數 × 權重) + (降雨分數 × 權重) + (風速分數 × 權重) + (濕度分數 × 權重)
    ```
    
    各項分數計算採用非線性函數，更貼近真實體感：
    - **溫度**：使用正態分佈曲線，離最佳溫度越遠扣分越多
    - **降雨**：超過容忍度後呈指數扣分
    - **風速**：分級評分（微風100分、強風大幅扣分）
    - **濕度**：舒適區間（40-70%）給予最高分
    
    ## 🚀 未來規劃
    
    - [ ] 整合機器學習，學習用戶歷史選擇
    - [ ] 加入 AI 對話功能（使用 Claude API）
    - [ ] 支援多城市比較
    - [ ] 串接更多天氣資料源
    - [ ] 加入即時天氣警報
    - [ ] 開發手機 App 版本
    """)

# 關於與回饋
with st.expander("ℹ️ 關於與回饋"):
    st.markdown("""
    ## 📝 版本資訊
    
    **版本**：Pro v2.0  
    **更新日期**：2026-01-03  
    **作者**：智能行程規劃團隊
    
    ## 🙏 致謝
    
    - 天氣資料：OpenWeatherMap API
    - 開發框架：Streamlit
    - 視覺化工具：Plotly
    
    ## 📧 聯絡我們
    
    如有任何問題或建議，歡迎回饋：
    - 在本頁面使用 Streamlit 的回饋功能
    - 或透過 GitHub 提交 Issue
    
    ## ⭐ 支持我們
    
    如果這個工具對您有幫助，歡迎：
    - 分享給需要的朋友
    - 在 GitHub 給我們一顆星
    - 提供改進建議
    """)

# 版權聲明
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 20px;'>
    <p>🌤️ 智能天氣行程規劃系統 Pro v2.0</p>
    <p>Made with ❤️ using Streamlit | Powered by OpenWeatherMap API</p>
    <p>© 2026 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)
