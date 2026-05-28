# Wordle Progressive Learning System

這是一個用 Python Flask + SQLite 製作的英文單字 Wordle 漸進式學習網站。

## 功能

- 使用者名稱註冊與唯一性檢查
- UUID / User_ID 登入
- C1-C6 初始難度設定
- 學測日期倒數與每日學習量規劃
- Wordle 模式，含詞性與字數提示
- 遺忘曲線複習排程
- 動態難度適應
- 失敗後復活賽 MCQ
- 錯題本與錯題特訓
- 使用者資訊與各級進度
- 全服排行榜

## 啟動

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

接著打開：

```text
http://127.0.0.1:5000
```

資料庫會自動建立在 `instance/wordle_learning.db`。

## Render 部署

1. 將整個專案上傳到 GitHub。
2. 到 Render 建立新的 Web Service，連接這個 GitHub repository。
3. Render 若讀到 `render.yaml`，會自動使用以下設定：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. 部署完成後，Render 會提供固定網址，例如：

```text
https://wordle-learning-system.onrender.com
```

注意：目前使用 SQLite，適合課堂展示與小型測試。Render 免費環境重啟或重新部署時，資料可能不保證永久保存；若要長期保存使用者資料，建議改用 PostgreSQL。
