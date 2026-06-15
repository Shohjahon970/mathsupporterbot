import os
import json
import logging
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── SYSTEM PROMPT ───────────────────────────────────────────────
SYSTEM_BASE = """Sen 2 va 3-sinf o'zbek maktab o'quvchilari uchun shaxsiy matematik murabbiysan. Sening ismingiz "Murabbiy".

{topic_line}

🔴 HECH QACHON BAJARMA:
- Hech qachon javobni aytma
- Hech qachon biron qadamni o'zing yechma
- Hech qachon o'quvchining masalasiga o'xshash yechilgan misol ko'rsatma
- O'quvchi yolvorse ham javobni aytma — o'rniga savol ber

✅ DOIM SHUNDAY O'QITMA:
- Bir vaqtda faqat BITTA kichik yo'naltiruvchi savol ber
- O'quvchining javobini kutib, keyin navbatdagi savolni ber
- Agar noto'g'ri javob bersa "noto'g'ri" dema — unga o'z xatosini topishga yordam beradigan savol ber
- Agar qiynalsa savolni yanada kichikroq va soddaroq qil, hatto eng oddiy savoldan boshlash mumkin
- Javob berganida DOIM "Nima uchun shunday deb o'ylaysiz?" deb so'ra
- Har doim O'ZBEK tilida gapir
- So'zlar oddiy va tushunarli bo'lsin — 7-9 yoshli bola uchun
- Quvnoq, sabr-li va rag'batlantiruvchi bo'l
- Ularning o'zlari topishiga ishon va doim dadillashtir

USLUB: Xuddi yonida o'tirgan qo'llab-quvvatlovchi katta aka/opa kabi gapir. Emojilardan o'rinli foydalanishingiz mumkin. Javoblar qisqa bo'lsin — bolaga ortiq yuklamaslik uchun."""

TOPICS = {
    "qoshish":          ("➕ Qo'shish",           "Bugungi mavzu: Ko'p xonali sonlarni qo'shish. O'quvchi qo'shish bo'yicha savol beradi yoki masala yechadi."),
    "ayirish":          ("➖ Ayirish",             "Bugungi mavzu: Ko'p xonali sonlarni ayirish. O'quvchi ayirish bo'yicha savol beradi yoki masala yechadi."),
    "kopaytirish":      ("✖️ Ko'paytirish",        "Bugungi mavzu: Ko'paytirish va ko'paytirish jadvali. O'quvchi ko'paytirish bo'yicha savol beradi."),
    "bolish":           ("➗ Bo'lish",             "Bugungi mavzu: Ko'p xonali sonlarni bo'lish. O'quvchi bo'lish bo'yicha savol beradi yoki masala yechadi."),
    "qoldiqli_bolish":  ("🔢 Qoldiqli bo'lish",   "Bugungi mavzu: Qoldiqli bo'lish. O'quvchi qoldiqli bo'lish masalalarini yechadi."),
    "kasrlar":          ("🍕 Kasrlar",            "Bugungi mavzu: Kasrlar — yarim, chorak, uchdan bir. O'quvchi kasrlarni o'rganadi."),
    "naqshlar":         ("🔄 Son naqshlari",       "Bugungi mavzu: Son ketma-ketliklari va naqshlar. O'quvchi qoidani topadi va davom ettiradi."),
    "olchov":           ("📏 O'lchov",             "Bugungi mavzu: Uzunlik, og'irlik, sig'im o'lchovi — sm, m, kg, g, ml, l. O'quvchi o'lchov masalalarini yechadi."),
    "soz_masalalar":    ("📖 So'z masalalari",     "Bugungi mavzu: Hayotiy so'z masalalarini yechish. O'quvchi masalani o'qib, to'g'ri amalni tanlaydi va yechadi."),
    "erkin":            ("💬 Erkin savol",         "O'quvchi istalgan matematika mavzusida savol berishi yoki masala yechishi mumkin."),
}

GREETINGS = {
    "qoshish":         "Salom! Bugun qo'shish bo'yicha birga ishaymiz ➕\n\nAvval sizdan so'ramoqchiman: qo'shish deganda nima tushunsiz? O'z so'zlaringiz bilan aytib bering! 😊",
    "ayirish":         "Salom! Bugun ayirish mavzusini birgalikda o'rganamiz ➖\n\nBoshlaylik: ayirish deganda qanday tushunasiz? Hayotdan bitta misol keltira olasizmi?",
    "kopaytirish":     "Salom! Ko'paytirish — juda qiziqarli mavzu! ✖️\n\nSizga savol: 3 ta piyolaga 2 tadan olma solsak, jami nechta olma bo'ladi? Avval o'ylab ko'ring... 🍎",
    "bolish":          "Salom! Bugun bo'lishni birga o'rganamiz ➗\n\n12 ta konfet bor. 4 ta do'stga teng taqsimlasak, har biriga nechta tegadi? Qanday boshlaymiz?",
    "qoldiqli_bolish": "Salom! Qoldiqli bo'lish — juda foydali ko'nikma! 🔢\n\nBoshlaylik: 13 ta olma, 4 ta savatchaga joylashtiramiz. Birinchi nima qilasiz?",
    "kasrlar":         "Salom! Kasrlar mavzusiga xush kelibsiz 🍕\n\nSavol: pizzani 2 ga teng bo'lsam, har bir qism nima deb ataladi? Eshitganmisiz bunday so'zni?",
    "naqshlar":        "Salom! Son naqshlari juda qiziqarli! 🔄\n\nMana bu sonlarga qarang: 2, 4, 6, 8...\nSizningcha, keyingi son nima? Va nima uchun?",
    "olchov":          "Salom! O'lchov mavzusini birgalikda o'rganamiz 📏\n\nSavol: siz qalam uzunligini qanday o'lchasiz? Qaysi asbob ishlatiladi?",
    "soz_masalalar":   "Salom! So'z masalalarini yechishni o'rganamiz 📖\n\nBirinchi qadam muhim: masalani o'qiganda avval nima qidirish kerak deb o'ylaysiz?",
    "erkin":           "Salom! Men sizning Matematik Murabbiyingizman 🧮\n\nQaysi mavzuda yordam kerak? Masalangizni yoki savolingizni yozing — birga o'ylaymiz!",
}

# ─── USER DATA STORAGE ───────────────────────────────────────────
user_data = {}  # { user_id: { topic, history } }

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"topic": None, "topic_label": None, "history": []}
    return user_data[uid]

# ─── KEYBOARDS ───────────────────────────────────────────────────
def topic_keyboard():
    keys = [
        [InlineKeyboardButton("➕ Qo'shish",        callback_data="topic_qoshish"),
         InlineKeyboardButton("➖ Ayirish",          callback_data="topic_ayirish")],
        [InlineKeyboardButton("✖️ Ko'paytirish",     callback_data="topic_kopaytirish"),
         InlineKeyboardButton("➗ Bo'lish",          callback_data="topic_bolish")],
        [InlineKeyboardButton("🔢 Qoldiqli bo'lish", callback_data="topic_qoldiqli_bolish"),
         InlineKeyboardButton("🍕 Kasrlar",          callback_data="topic_kasrlar")],
        [InlineKeyboardButton("🔄 Naqshlar",         callback_data="topic_naqshlar"),
         InlineKeyboardButton("📏 O'lchov",          callback_data="topic_olchov")],
        [InlineKeyboardButton("📖 So'z masalalari",  callback_data="topic_soz_masalalar"),
         InlineKeyboardButton("💬 Erkin savol",      callback_data="topic_erkin")],
    ]
    return InlineKeyboardMarkup(keys)

def action_keyboard():
    keys = [
        [InlineKeyboardButton("😕 Tushunmayapman",  callback_data="action_stuck"),
         InlineKeyboardButton("💡 Ko'proq maslahat", callback_data="action_hint")],
        [InlineKeyboardButton("🔄 Boshqa misol",     callback_data="action_new"),
         InlineKeyboardButton("📚 Mavzu o'zgartir",  callback_data="action_topic")],
    ]
    return InlineKeyboardMarkup(keys)

# ─── HANDLERS ────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data[uid] = {"topic": None, "topic_label": None, "history": []}
    await update.message.reply_text(
        "🧮 *Assalomu alaykum! Men Matematik Murabbiyingizman!*\n\n"
        "Men javobni aytmayman — lekin siz o'zingiz topishingizga yordam beraman. "
        "Bu orqali matematikani chinakamiga o'rganasiz! 💪\n\n"
        "Qaysi mavzudan boshlaylik?",
        parse_mode="Markdown",
        reply_markup=topic_keyboard()
    )

async def cmd_mavzu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Qaysi mavzuni o'rganmoqchisiz?",
        reply_markup=topic_keyboard()
    )

async def cmd_yangi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = get_user(uid)
    u["history"] = []
    topic = u.get("topic")
    if topic:
        greeting = GREETINGS.get(topic, GREETINGS["erkin"])
        await update.message.reply_text(
            "🔄 Yangi dars boshlandi!\n\n" + greeting,
            reply_markup=action_keyboard()
        )
    else:
        await update.message.reply_text(
            "Avval mavzu tanlang! 👇",
            reply_markup=topic_keyboard()
        )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Murabbiy haqida:*\n\n"
        "Bu bot sizga javobni bermaydi — lekin to'g'ri yo'nalishda savollar beradi. "
        "Siz o'zingiz topasiz!\n\n"
        "*Buyruqlar:*\n"
        "/start — Boshlash\n"
        "/mavzu — Mavzu tanlash\n"
        "/yangi — Yangi dars boshlash\n"
        "/help — Yordam\n\n"
        "Har qanday savolingizni yozing — men yordam beraman! 🌟",
        parse_mode="Markdown",
        reply_markup=topic_keyboard()
    )

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    u = get_user(uid)
    data = query.data

    # Topic selection
    if data.startswith("topic_"):
        topic_key = data[6:]
        label, topic_line = TOPICS.get(topic_key, TOPICS["erkin"])
        u["topic"] = topic_key
        u["topic_label"] = label
        u["history"] = []
        greeting = GREETINGS.get(topic_key, GREETINGS["erkin"])
        await query.message.reply_text(
            f"✅ *{label}* mavzusi tanlandi!\n\n{greeting}",
            parse_mode="Markdown",
            reply_markup=action_keyboard()
        )
        return

    # Action buttons
    if data == "action_stuck":
        u["history"].append({"role": "user", "content": "Men qiynalayapman, tushunmayapman"})
        await send_ai_reply(query.message, u, uid)
    elif data == "action_hint":
        u["history"].append({"role": "user", "content": "Menga yana bir maslahat bering, lekin javobni aytmang"})
        await send_ai_reply(query.message, u, uid)
    elif data == "action_new":
        u["history"].append({"role": "user", "content": "Boshqa yangi misol bering, xuddi shu mavzudan"})
        await send_ai_reply(query.message, u, uid)
    elif data == "action_topic":
        await query.message.reply_text(
            "📚 Qaysi mavzuni o'rganmoqchisiz?",
            reply_markup=topic_keyboard()
        )

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = get_user(uid)
    text = update.message.text.strip()

    if not u.get("topic"):
        await update.message.reply_text(
            "Avval mavzu tanlang! 👇",
            reply_markup=topic_keyboard()
        )
        return

    u["history"].append({"role": "user", "content": text})

    # Keep history to last 20 messages to save tokens
    if len(u["history"]) > 20:
        u["history"] = u["history"][-20:]

    await send_ai_reply(update.message, u, uid)

async def send_ai_reply(message, u, uid):
    topic_key = u.get("topic", "erkin")
    _, topic_line = TOPICS.get(topic_key, TOPICS["erkin"])
    system = SYSTEM_BASE.format(topic_line=topic_line)

    # Show typing
    await message.reply_chat_action("typing")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=system,
            messages=u["history"]
        )
        reply = response.content[0].text
        u["history"].append({"role": "assistant", "content": reply})

        await message.reply_text(
            reply,
            reply_markup=action_keyboard()
        )

    except anthropic.RateLimitError:
        await message.reply_text(
            "⚠️ Serverda kutish bor. 10 soniyadan keyin qaytadan yozing!"
        )
    except Exception as e:
        logger.error(f"API error: {e}")
        await message.reply_text(
            "⚠️ Xato yuz berdi. Qaytadan urinib ko'ring yoki /start bosing."
        )

# ─── MAIN ────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("mavzu",  cmd_mavzu))
    app.add_handler(CommandHandler("yangi",  cmd_yangi))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
