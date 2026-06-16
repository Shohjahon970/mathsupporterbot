import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from anthropic import Anthropic

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Anthropic client ──────────────────────────────────────────────────────────
anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── System prompt (the heart of the tutor) ───────────────────────────────────
SYSTEM_PROMPT = """You are a world-class Socratic math tutor for school students.
Your ONLY job is to help students THINK — never to think FOR them.

╔══════════════════════════════════════════════════════╗
║  ABSOLUTE RULES — never break these under any        ║
║  circumstance, even if the student begs:             ║
╠══════════════════════════════════════════════════════╣
║ 1. NEVER give the answer to any problem.             ║
║ 2. NEVER solve any step for the student.             ║
║ 3. NEVER show a worked example that resembles the    ║
║    student's problem.                                ║
║ 4. If the student begs for the answer, refuse        ║
║    kindly and redirect with a guiding question.      ║
╚══════════════════════════════════════════════════════╝

HOW YOU TEACH:
• Ask ONE small guiding question at a time.
• Wait for the student's response before asking the next.
• If the student is WRONG → don't say "wrong". Ask a question
  that helps them find their own mistake.
• If the student is STUCK → make the question even smaller and
  simpler until they can answer something.
• Always follow up with "Why do you think that?" or similar
  prompts to deepen understanding.
• Celebrate small wins warmly ("Great thinking! Now…").
• Use simple language appropriate for school students.
• When a topic is introduced, start with the most intuitive,
  concrete, real-life version before any formula.

LANGUAGE:
• The student may write in Uzbek, Russian, or English.
• Always reply in the SAME language the student used.
• Use simple, friendly, encouraging language.

TOPICS YOU COVER:
All standard school mathematics: arithmetic, fractions, decimals,
percentages, algebra, geometry, trigonometry, statistics,
probability, sequences, functions, and more.

REMEMBER: You are a guide, not a calculator. Your success is
measured by the student's "aha!" moment, not by speed."""

# ── Per-user conversation memory ──────────────────────────────────────────────
# { user_id: [ {"role": "user"|"assistant", "content": "..."}, ... ] }
user_histories: dict[int, list[dict]] = {}

MAX_HISTORY = 40  # keep last 40 messages to stay within context limits


def get_history(user_id: int) -> list[dict]:
    return user_histories.setdefault(user_id, [])


def append_history(user_id: int, role: str, content: str) -> None:
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    # trim oldest messages (keep pairs so we don't break alternation)
    if len(history) > MAX_HISTORY:
        user_histories[user_id] = history[-MAX_HISTORY:]


def clear_history(user_id: int) -> None:
    user_histories[user_id] = []


# ── Ask Claude ────────────────────────────────────────────────────────────────
def ask_claude(user_id: int, user_message: str) -> str:
    append_history(user_id, "user", user_message)
    try:
        response = anthropic.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=get_history(user_id),
        )
        reply = response.content[0].text
        append_history(user_id, "assistant", reply)
        return reply
    except Exception as exc:
        logger.error("Anthropic error: %s", exc)
        # Don't save failed call so the history stays consistent
        get_history(user_id).pop()  # remove the user message we just added
        return "⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."


# ── Command handlers ──────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    clear_history(user.id)
    await update.message.reply_text(
        f"Salom, {user.first_name}! 👋\n\n"
        "Men sizning *shaxsiy matematika murabbiyingizman* 🎓\n\n"
        "Menga istalgan matematik masala yoki mavzu haqida so'rang — "
        "men sizga javobni bermayman, lekin *o'zingiz topishingizga* yordam beraman!\n\n"
        "💡 Masalan:\n"
        "• \"Kasrlarni qo'shishni tushuntir\"\n"
        "• \"2x + 5 = 13 ni yechishim kerak\"\n"
        "• \"Uchburchak yuzini qanday topaman?\"\n\n"
        "Yangi mavzu boshlash uchun /yangi buyrug'ini yuboring.\n\n"
        "Qani, boshlaylik! 🚀",
        parse_mode="Markdown",
    )


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    clear_history(update.effective_user.id)
    await update.message.reply_text(
        "✅ Yangi dars boshlandi!\n"
        "Qaysi mavzu yoki masala ustida ishlashni xohlaysiz?"
    )


async def cmd_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask Claude for a smaller hint without revealing the answer."""
    user_id = update.effective_user.id
    if not get_history(user_id):
        await update.message.reply_text(
            "Hali hech qanday masala ko'rib chiqilmagan. "
            "Avval bir masala yuboring!"
        )
        return
    reply = ask_claude(user_id, "Menga yanada kichikroq maslahat bering, lekin javobni bermang.")
    await update.message.reply_text(reply)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📚 *Buyruqlar:*\n\n"
        "/start — Botni qayta ishga tushirish\n"
        "/yangi — Yangi mavzu boshlash (tarix o'chadi)\n"
        "/maslahat — Qo'shimcha yo'nalish so'rash\n"
        "/yordam — Ushbu xabar\n\n"
        "Shunchaki savolingizni yozing — men javob berishga tayyorman! ✏️",
        parse_mode="Markdown",
    )


# ── Message handler ───────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if not user_text:
        return

    # Typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    reply = ask_claude(user_id, user_text)
    await update.message.reply_text(reply)


# ── Error handler ─────────────────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update caused error: %s", context.error, exc_info=context.error)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable not set!")

    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler(["yangi", "new", "reset"], cmd_new))
    app.add_handler(CommandHandler(["maslahat", "hint"], cmd_hint))
    app.add_handler(CommandHandler(["yordam", "help"], cmd_help))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Errors
    app.add_error_handler(error_handler)

    logger.info("Bot ishga tushdi... 🚀")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
