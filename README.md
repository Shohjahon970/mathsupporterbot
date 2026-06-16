# 🎓 AI Math Tutor Telegram Bot

A Socratic math tutor bot for students — it **never gives answers**, only asks guiding questions until the student finds the answer themselves.

---

## ✨ How it works

The bot follows strict Socratic teaching rules:
- ❌ Never gives the answer
- ❌ Never solves steps for the student
- ✅ Asks one small guiding question at a time
- ✅ If the student is wrong → asks a question to help them find the mistake
- ✅ If the student is stuck → breaks the problem into even smaller pieces
- ✅ Responds in the student's language (Uzbek 🇺🇿, Russian 🇷🇺, or English 🇬🇧)

---

## 🚀 Setup (Step by step)

### Step 1 — Create your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Give it a name (e.g. `Matematika Murabbiy`)
4. Give it a username (e.g. `my_math_tutor_bot`)
5. Copy the **token** BotFather gives you (looks like `7123456789:AAF...`)

---

### Step 2 — Get your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account / log in
3. Go to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`)

---

### Step 3 — Install Python dependencies

```bash
# Make sure Python 3.10+ is installed
python --version

# Install dependencies
pip install -r requirements.txt
```

---

### Step 4 — Set environment variables

**On Linux / Mac:**
```bash
export TELEGRAM_BOT_TOKEN="7123456789:AAF..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

**On Windows (Command Prompt):**
```cmd
set TELEGRAM_BOT_TOKEN=7123456789:AAF...
set ANTHROPIC_API_KEY=sk-ant-...
```

**On Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN = "7123456789:AAF..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

---

### Step 5 — Run the bot

```bash
python bot.py
```

You should see:
```
Bot ishga tushdi... 🚀
```

Now open Telegram and send `/start` to your bot!

---

## 📱 Student Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot, get welcome message |
| `/yangi` | Start a new topic (clears history) |
| `/maslahat` | Ask for a smaller hint |
| `/yordam` | Show help |

---

## 🌐 Running 24/7 (Deployment)

To keep the bot running always, deploy it to a free server:

### Option A — Railway.app (Recommended, Free)
1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables in Railway dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `ANTHROPIC_API_KEY`
4. Done! Bot runs 24/7 for free.

### Option B — Render.com (Free)
1. Go to [render.com](https://render.com)
2. New → Background Worker → Connect GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Add environment variables

### Option C — VPS / Your own server
```bash
# Install screen to keep it running
sudo apt install screen
screen -S mathbot
python bot.py
# Press Ctrl+A then D to detach
```

---

## 💡 Example Conversation

```
Student: 2x + 5 = 13 ni yechishim kerak

Bot: Yaxshi! Birinchi savol: tenglamaning maqsadi nima?
     Ya'ni, x ni topish uchun nimani qilishimiz kerak?

Student: x ni topish kerak

Bot: To'g'ri! Endi ayting: tenglamaning chap tomonida x dan boshqa
     yana nima bor?

Student: +5 bor

Bot: Ajoyib! Agar biz chap tomonda faqat x ni qoldirishni
     istasak, bu +5 bilan nima qilishimiz mumkin?

Student: 5 ni olib tashlash kerak

Bot: Fikringiz to'g'ri yo'nalishda! Lekin matematikada
     "olib tashlash" uchun ikkala tomonga ham bir xil
     amal bajaramiz. Ikkala tomonga ham -5 qo'shsak
     nima bo'ladi?
```

---

## 🛠 Customization

Edit `SYSTEM_PROMPT` in `bot.py` to:
- Add more languages
- Change the teaching style
- Focus on specific topics (e.g. only algebra)
- Adjust difficulty level

---

## 📊 Cost Estimate

- Each message uses ~500-1000 tokens
- Claude Sonnet: ~$3 per million tokens
- 100 students × 20 messages/day = ~$0.30/day

Very affordable for a school! 🎉
