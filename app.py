import streamlit as st
import requests
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="台灣旅遊規劃", page_icon="🗺️", layout="wide")

st.title("🗺️ 台灣天氣旅遊規劃助手")
st.write("根據天氣預報，為您規劃最適合的台灣旅遊行程")

TAIWAN_CITIES = {
    "台北": {"lat": 25.0330, "lon": 121.5654},
    "台中": {"lat": 24.1477, "lon": 120.6736},
    "台南": {"lat": 22.9998, "lon": 120.2269},
    "高雄": {"lat": 22.6273, "lon": 120.3014}
}

try:
    api_key = st.secrets["OPENWEATHER_API_KEY"]
except:
    st.error("請設定 API Key")
    st.stop()

with st.sidebar:
    st.header("設定")
    selected_city = st.selectbox("選擇城市", list(TAIWAN_CITIES.keys()))
    forecast_days = st.radio("預測天數", [5, 10])

if st.button("開始規劃", type="primary"):
    city_info = TAIWAN_CITIES[selected_city]
    
    with st.spinner("查詢中..."):
        try:
            url = f"http://api.openweathermap.org/data/2.5/forecast?lat={city_info['lat']}&lon={city_info['lon']}&appid={api_key}&units=metric&lang=zh_tw"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                st.success(f"查詢成功！{selected_city} 未來 {forecast_days} 天天氣")
                
                for i, item in enumerate(data['list'][:5]):
                    dt = datetime.fromtimestamp(item['dt'])
                    temp = item['main']['temp']
                    desc = item['weather'][0]['description']
                    
                    st.write(f"{dt.strftime('%m/%d %H:%M')} - {temp}°C - {desc}")
            else:
                st.error("查詢失敗")
        except Exception as e:
            st.error(f"錯誤: {e}")

st.caption("台灣天氣旅遊規劃助手")
