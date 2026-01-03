import streamlit as st
import requests
from datetime import datetime

st.title("🌤️ 天氣行程規劃")

# 側邊欄
api_key = st.sidebar.text_input("API Key", type="password")
city = st.text_input("城市", "Taipei")

if st.button("查詢天氣"):
    if api_key:
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                st.success(f"✅ {city} 的天氣")
                st.write(f"溫度: {data['main']['temp']}°C")
                st.write(f"天氣: {data['weather'][0]['description']}")
            else:
                st.error("查詢失敗")
        except Exception as e:
            st.error(f"錯誤: {e}")
    else:
        st.warning("請輸入 API Key")
```

這只有 25 行，**一定能跑**。先確認能啟動後，再慢慢加功能。

---

## 📋 完整操作步驟

### 在 GitHub 上：

1. **進入你的 `weather-planner-app` 儲存庫**

2. **編輯 app.py**：
   - 點擊 `app.py`
   - 點右上角的鉛筆圖示 ✏️
   - **全選刪除舊內容**（Ctrl+A，Delete）
   - **貼上上面 25 行的程式碼**
   - 點擊 "Commit changes"

3. **檢查 requirements.txt**：
   - 點擊 `requirements.txt`
   - 確認只有三行：
```
     streamlit
     requests
     pandas
