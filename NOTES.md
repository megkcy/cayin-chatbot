# CAYIN Chatbot — 操作筆記

## 專案資訊
- **GitHub**: https://github.com/megkcy/cayin-chatbot
- **技術**: Python 3 + Flask + Groq API (主) + Google Gemini (備援)
- **寄信通知**: press@cayintech.com

---

## 快速啟動

```bash
cd ~/Desktop/claude-chatbot
python3 server.py
```

瀏覽器打開：`http://localhost:5000`

### 重啟 server（強制）

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
