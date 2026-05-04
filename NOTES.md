# CAYIN Chatbot — 操作筆記

---

## 🎯 給主管試用（不需要任何技術背景）

### 第一步：請同事先啟動伺服器
> 請負責的同事在 `D:\claude-chatbot` 資料夾雙擊 **`start.bat`**，黑色視窗出現後即代表伺服器啟動。

### 第二步：開啟 Chatbot

| 裝置 | 網址 |
|------|------|
| 同一台電腦 | http://localhost:5000 |
| 同一個辦公室網路（其他電腦/手機） | http://172.16.20.30:5000 |

> 用瀏覽器（Chrome / Edge / Safari）開啟即可，不需要安裝任何東西。

### 第三步：開始聊天
1. 輸入您的**姓名**與**Email**，點「Start Chat」
2. 直接用中文或英文提問

### 建議測試問題

| 問題 | 預期回覆 |
|------|----------|
| `SMP-2400 是什麼？` | 產品介紹 |
| `GO CAYIN 怎麼用？` | 中文教學影片連結 |
| `How to use GO CAYIN?` | 英文教學影片連結 |
| `GO CAYIN poster 多少錢？` | 台幣定價 |
| `GO CAYIN poster pricing?` | 美元定價 |
| `我想聯絡業務` | 聯絡表單連結 |
| `How do I choose between Robustie and Flexie?` | 英文產品建議 |

### 查看對話紀錄
所有訪客對話都會自動儲存：
- 開啟 http://localhost:5000/api/admin/conversations 可查看 JSON 格式
- 或下載 CSV：http://localhost:5000/api/admin/export-csv

---

## 專案資訊
- **GitHub**: https://github.com/megkcy/cayin-chatbot
- **技術**: Python 3 + Flask + Groq API (主) + Google Gemini (備援)
- **寄信通知**: press@cayintech.com

---

## 快速啟動

### Windows（目前電腦）
```
雙擊 start.bat
```
或在 CMD / PowerShell：
```
cd D:\claude-chatbot
py server.py
```

### Mac / Linux
```bash
cd ~/Desktop/claude-chatbot
python3 server.py
```

瀏覽器打開：`http://localhost:5000`

### 重啟 server（Windows — 強制）
關掉原本的視窗，再重新執行 `start.bat`。

### 重啟 server（Mac/Linux — 強制）

```bash
lsof -ti:5000 | xargs kill -9
python3 server.py
```

---

## 在新電腦上設定

```bash
# 1. 下載專案
git clone https://github.com/megkcy/cayin-chatbot.git
cd cayin-chatbot

# 2. 安裝套件
pip3 install -r requirements.txt

# 3. 建立 .env 檔（參考下方格式）
# 4. 啟動
python3 server.py
```

### .env 檔格式
```
GROQ_API_KEY=你的key
GOOGLE_API_KEY=你的key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-sender@gmail.com
SMTP_PASS=your-gmail-app-password
NOTIFY_EMAIL=press@cayintech.com
```

> `.env` 不會上傳到 GitHub，要自己手動建立或 email 給自己。

---

## 推送更新到 GitHub

```bash
git add -A
git commit -m "說明"
git push origin main
```

> GitHub token (PAT) 需要有 `repo` 權限。

---

## AI 模型備援邏輯

```
用戶發問
   ↓
嘗試 Groq (llama-3.3-70b-versatile)  ← 主要
   ↓ 失敗（rate limit / 任何錯誤）
自動切換 Google Gemini (gemini-2.5-flash)  ← 備援
   ↓ 也失敗
顯示「Service unavailable」
```

- Groq 免費額度：每日 100,000 tokens，用完自動切 Gemini
- Groq 管理：https://console.groq.com
- Gemini 管理：https://aistudio.google.com

---

## 功能清單

| 功能 | 說明 |
|------|------|
| 訪客填名字 + Email | 開始聊天前必填 |
| 多語言回覆 | 偵測語言自動回覆（中英日泰西法...） |
| 定價語言規則 | 繁體中文問 → 台幣，其他語言 → 美元 |
| 產品知識庫 | CAYIN 產品 Q&A + 系統提示 |
| GO CAYIN 定價 | 繁體中文顯示 NT$，其他語言顯示 USD |
| How-to 問題 | 自動附上 Help Center 連結 |
| 2秒後跟進 | Bot 回答後 2 秒詢問是否還有問題 |
| 4秒無回應 | 自動顯示聯絡表單連結 |
| Chat bubble | 右下角 55px 藍色圓形按鈕 |
| 連結可點擊 | 對話中所有 URL 自動變成可點擊連結，開新視窗 |
| 對話記錄 | 存到 `data/conversations.json` + `data/conversations.csv` |
| 週報寄信 | 每週一 09:00 自動寄 CSV 到 press@cayintech.com |
| 爬蟲更新 | 每隔週一 09:05 自動爬 cayintech.com 更新知識庫 |
| 爬蟲通知 | 爬完後寄信到 press@cayintech.com 確認 |
| embed.js | 可嵌入外部網站（iframe） |
| 內網部署 | 支援 NAS / 區域網路（0.0.0.0:5000） |
| AI 備援 | Groq 失敗自動切換 Google Gemini |

---

## 重要連結

| 用途 | 連結 |
|------|------|
| CAYIN 聯絡表單 | https://www.cayintech.com/contactus |
| GO CAYIN 詢價 | https://www.gocayin.com/submit-inquiry |
| GO CAYIN 定價（英） | https://www.gocayin.com/en/pricing |
| GO CAYIN 定價（中） | https://www.gocayin.com/zh-TW/pricing |
| Help Center | https://onlinehelp.cayintech.com/main.html |

---

## 管理功能

| 功能 | 網址 |
|------|------|
| 手動下載 CSV | http://localhost:5000/api/admin/export-csv |
| 手動觸發爬蟲 | http://localhost:5000/api/admin/scrape-now |
| 查看所有對話 | http://localhost:5000/api/admin/conversations |

---

## 嵌入外部網站

在網站 `</body>` 前加入：

```html
<script>
  window.CAYIN_CHAT_URL = "https://你的伺服器網址";
</script>
<script src="https://你的伺服器網址/embed.js"></script>
```

---

## GO CAYIN 定價

### poster
| 方案 | 月繳 | 年繳 |
|------|------|------|
| Basic | 免費 / Free | 免費 / Free |
| Professional | NT$400 / USD $15 | NT$4,000 / USD $150 |
| Professional Team | NT$1,900 / USD $60 | NT$19,000 / USD $600 |

### meetingPost+
| 方案 | 月繳 | 年繳 |
|------|------|------|
| Basic | 免費 / Free | 免費 / Free |
| Professional | NT$600 / USD $20 | NT$6,000 / USD $200 |
| Professional Team | NT$1,900 / USD $60 | NT$19,000 / USD $600 |

---

## 注意事項

- `.env` 有 API key，不要給其他人或上傳到任何地方
- Groq 每日 100k token 上限，用完自動切換 Gemini
- Gmail SMTP 需要用「應用程式密碼」，不是登入密碼
  - Google 帳號 → 安全性 → 兩步驟驗證 → 應用程式密碼
- Windows 電腦可以跑 chatbot（`python server.py`），但 Claude Code 需要 WSL
