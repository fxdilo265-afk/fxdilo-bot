import os
import json
import asyncio
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import pytz

# ═══════════════════════════════════════════
#  ТАНЗИМОТ — ТАНҲО ИНРО ИВАЗ КУН
# ═══════════════════════════════════════════
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "8181219792:AAEH1MHHNG-YmjP4ccL-g23Bk7z9M7ZtJq4")
CHANNEL     = os.environ.get("CHANNEL", "@xdilo1")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "fxdilo2024")
# ═══════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_flask = Flask(__name__)

# Обунашудагон — ҳар нафар ва ҷуфтҳояш
subscribers = {}  # {user_id: {"pairs": ["XAUUSD", "EURUSD", ...], "name": "..."}}

# ═══════════════════════════════════════════
#  ЁРДАМЧИ ФУНКСИЯҲО
# ═══════════════════════════════════════════

def format_signal(data):
    """Сигналро ба паём табдил медиҳад"""
    direction = data.get("direction", "").upper()
    symbol    = data.get("symbol", "UNKNOWN").upper()
    entry     = data.get("entry", "—")
    sl        = data.get("sl", "—")
    tp1       = data.get("tp1", "—")
    tp2       = data.get("tp2", "—")
    tp3       = data.get("tp3", "—")
    tf        = data.get("timeframe", "1M")
    now       = datetime.now(pytz.timezone("Asia/Dushanbe")).strftime("%H:%M — %d.%m.%Y")

    if direction == "LONG":
        emoji = "🟢"
        action = "LONG — BUY"
    elif direction == "SHORT":
        emoji = "🔴"
        action = "SHORT — SELL"
    else:
        emoji = "⚪"
        action = direction

    msg = (
        f"{emoji} <b>{symbol}</b> — {action}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Entry:</b>  {entry}\n"
        f"🛑 <b>Stop Loss:</b>  {sl}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>TP1:</b>  {tp1}\n"
        f"🎯 <b>TP2:</b>  {tp2}\n"
        f"🎯 <b>TP3:</b>  {tp3}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⏰ {now} | {tf}\n"
        f"📊 <b>FXDILO FAST SCALP</b>"
    )
    return msg


async def send_to_channel(msg):
    """Ба канал мефиристад"""
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=CHANNEL,
        text=msg,
        parse_mode="HTML"
    )


async def send_to_subscribers(msg, symbol):
    """Ба ҳама обунашудагон мефиристад"""
    bot = Bot(token=BOT_TOKEN)
    sym = symbol.upper()
    for user_id, info in subscribers.items():
        pairs = info.get("pairs", [])
        if "ALL" in pairs or sym in pairs:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=msg,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Хато ба {user_id}: {e}")


# ═══════════════════════════════════════════
#  WEBHOOK АЗ TRADINGVIEW
# ═══════════════════════════════════════════

@app_flask.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"Сигнал омад: {data}")

        symbol    = data.get("symbol", "UNKNOWN")
        direction = data.get("direction", "")

        # Сигналро форматлаш
        msg = format_signal(data)

        # Gold — ба канал
        if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
            asyncio.run(send_to_channel(msg))

        # Ба ҳама обунашудагон
        asyncio.run(send_to_subscribers(msg, symbol))

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Хато: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ═══════════════════════════════════════════
#  БОТ КОМАНДАҲО
# ═══════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id   = update.effective_user.id
    user_name = update.effective_user.first_name

    if user_id not in subscribers:
        subscribers[user_id] = {"pairs": [], "name": user_name}

    msg = (
        f"👋 Салом, <b>{user_name}</b>!\n\n"
        f"<b>FXDILO FAST SCALP Bot</b>\n\n"
        f"Кадом сигналро мехоҳед:\n\n"
        f"/gold — XAUUSD (Gold)\n"
        f"/forex — Ҳама Forex\n"
        f"/crypto — Ҳама Крипто\n"
        f"/all — Ҳама сигналҳо\n"
        f"/pairs — Ҷуфти алоҳида\n"
        f"/mystatus — Ҳолати ман\n"
        f"/stop — Қатъ кун\n"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in subscribers:
        subscribers[user_id] = {"pairs": [], "name": update.effective_user.first_name}
    if "XAUUSD" not in subscribers[user_id]["pairs"]:
        subscribers[user_id]["pairs"].append("XAUUSD")
    await update.message.reply_text("✅ <b>XAUUSD (Gold)</b> сигнал фаъол шуд!", parse_mode="HTML")


async def cmd_forex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in subscribers:
        subscribers[user_id] = {"pairs": [], "name": update.effective_user.first_name}
    forex_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "XAUUSD"]
    for p in forex_pairs:
        if p not in subscribers[user_id]["pairs"]:
            subscribers[user_id]["pairs"].append(p)
    await update.message.reply_text("✅ <b>Ҳама Forex</b> сигнал фаъол шуд!", parse_mode="HTML")


async def cmd_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in subscribers:
        subscribers[user_id] = {"pairs": [], "name": update.effective_user.first_name}
    crypto_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    for p in crypto_pairs:
        if p not in subscribers[user_id]["pairs"]:
            subscribers[user_id]["pairs"].append(p)
    await update.message.reply_text("✅ <b>Ҳама Крипто</b> сигнал фаъол шуд!", parse_mode="HTML")


async def cmd_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribers[user_id] = {"pairs": ["ALL"], "name": update.effective_user.first_name}
    await update.message.reply_text("✅ <b>Ҳама сигналҳо</b> фаъол шуд!", parse_mode="HTML")


async def cmd_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📋 <b>Ҷуфти алоҳида интихоб кун:</b>\n\n"
        "<b>Forex:</b>\n"
        "/pair_EURUSD\n"
        "/pair_GBPUSD\n"
        "/pair_USDJPY\n"
        "/pair_XAUUSD\n\n"
        "<b>Крипто:</b>\n"
        "/pair_BTCUSDT\n"
        "/pair_ETHUSDT\n"
        "/pair_SOLUSDT\n"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cmd     = update.message.text.replace("/pair_", "").upper()
    if user_id not in subscribers:
        subscribers[user_id] = {"pairs": [], "name": update.effective_user.first_name}
    if cmd not in subscribers[user_id]["pairs"]:
        subscribers[user_id]["pairs"].append(cmd)
    await update.message.reply_text(f"✅ <b>{cmd}</b> фаъол шуд!", parse_mode="HTML")


async def cmd_mystatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in subscribers or not subscribers[user_id]["pairs"]:
        await update.message.reply_text("❌ Шумо ҳеҷ сигнал фаъол накардаед.\n/start — оғоз кун", parse_mode="HTML")
        return
    pairs = subscribers[user_id]["pairs"]
    msg = f"📊 <b>Сигналҳои фаъоли шумо:</b>\n\n" + "\n".join([f"✅ {p}" for p in pairs])
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in subscribers:
        subscribers[user_id]["pairs"] = []
    await update.message.reply_text("⛔ Ҳама сигналҳо қатъ шуд.\n/start — дубора оғоз кун", parse_mode="HTML")


# ═══════════════════════════════════════════
#  ОҒОЗ
# ═══════════════════════════════════════════

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start",      cmd_start))
    application.add_handler(CommandHandler("gold",       cmd_gold))
    application.add_handler(CommandHandler("forex",      cmd_forex))
    application.add_handler(CommandHandler("crypto",     cmd_crypto))
    application.add_handler(CommandHandler("all",        cmd_all))
    application.add_handler(CommandHandler("pairs",      cmd_pairs))
    application.add_handler(CommandHandler("mystatus",   cmd_mystatus))
    application.add_handler(CommandHandler("stop",       cmd_stop))

    # Ҷуфти алоҳида
    for pair in ["EURUSD","GBPUSD","USDJPY","USDCHF","AUDUSD","USDCAD","XAUUSD","BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"]:
        application.add_handler(CommandHandler(f"pair_{pair}", cmd_pair))

    application.run_polling()


if __name__ == "__main__":
    import threading
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host="0.0.0.0", port=port)
