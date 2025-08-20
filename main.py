import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    ContextTypes, filters
)
from flask import Flask
import threading

# ==============================
# KONFIG
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8304855655:AAG4TChMmiyG5teVNcn4-zMWOwL7mlMmMd0"
PORT = int(os.getenv("PORT", 10000))
ASKING = 1

GROUPS = [
    ("TOTAL",),
    ("JK1", "JK2"),
    ("UMR1", "UMR2", "UMR3", "UMR4", "UMR5"),
    ("PT1", "PT2", "PT3", "PT4"),
    ("FBJ1", "FBJ2", "FBJ3", "FBJ4"),
    ("JJ1", "JJ2", "JJ3", "JJ4"),
    ("PDB1", "PDB2", "PDB3", "PDB4"),
    ("MK1", "MK2"),
    ("FB1", "FB2", "FB3", "FB4"),
    ("KJO1", "KJO2"),
    ("PJO1", "PJO2"),
    ("ABJ1", "ABJ2", "ABJ3", "ABJ4", "ABJ5")
]

ITEM_LABELS = {
    "TOTAL":"📊 TOTAL",
    "JK1":"👩 JK1","JK2":"👨 JK2",
    "UMR1":"🎂 UMR1","UMR2":"🧑‍💼 UMR2","UMR3":"👨‍👩‍👧‍👦 UMR3","UMR4":"👴 UMR4","UMR5":"👵 UMR5",
    "PT1":"📚 PT1","PT2":"🏫 PT2","PT3":"🎓 PT3","PT4":"🎓🎓 PT4",
    "FBJ1":"📅🔥 FBJ1","FBJ2":"📅 FBJ2","FBJ3":"📆 FBJ3","FBJ4":"⏳ FBJ4",
    "JJ1":"🎲 JJ1","JJ2":"⚽ JJ2","JJ3":"🃏 JJ3","JJ4":"❓ JJ4",
    "PDB1":"💸 PDB1","PDB2":"💰 PDB2","PDB3":"💵 PDB3","PDB4":"🏦 PDB4",
    "MK1":"❗ MK1","MK2":"✔️ MK2",
    "FB1":"🙅‍♂️ FB1","FB2":"🤏 FB2","FB3":"🔥 FB3","FB4":"💥 FB4",
    "KJO1":"🎰❗ KJO1","KJO2":"✔️ KJO2",
    "PJO1":"💔 PJO1","PJO2":"💖 PJO2",
    "ABJ1":"🎰 ABJ1","ABJ2":"❗ ABJ2","ABJ3":"🗣️ ABJ3","ABJ4":"⚠️ ABJ4","ABJ5":"🤥 ABJ5"
}

FIELD_PROMPTS = {k: f"Masukkan nilai untuk {v}:" for k,v in ITEM_LABELS.items()}

# ==============================
# FLASK KEEP ALIVE
# ==============================
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"
def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ==============================
# UTILS
# ==============================
def is_int_nonneg(text: str) -> bool:
    try:
        return int(text) >= 0
    except:
        return False

def format_rekap_text(data: dict) -> str:
    text = "📋 Berikut rekap data yang telah kamu input:\n\n"
    for g in GROUPS:
        for k in g:
            text += f"{ITEM_LABELS[k]}: {data.get(k,0)}\n"
        text += "\n"
    return text.strip()

def check_constraints_groups(data: dict) -> list:
    total = data.get("TOTAL",0)
    groups_check = {
        "JK": ["JK1","JK2"],
        "UMR": ["UMR1","UMR2","UMR3","UMR4","UMR5"],
        "PT": ["PT1","PT2","PT3","PT4"],
        "FBJ": ["FBJ1","FBJ2","FBJ3","FBJ4"],
        "JJ": ["JJ1","JJ2","JJ3","JJ4"],
        "PDB": ["PDB1","PDB2","PDB3","PDB4"],
        "MK": ["MK1","MK2"],
        "FB": ["FB1","FB2","FB3","FB4"],
        "KJO": ["KJO1","KJO2"],
        "PJO": ["PJO1","PJO2"],
    }
    wrong_groups = []
    for k, items in groups_check.items():
        s = sum(data.get(i,0) for i in items)
        if s != total:
            wrong_groups.append((k, items))
    
    # cek ABJ
    abj_items = [f"ABJ{i}" for i in range(1,6)]
    abj_total = sum(data.get(i,0) for i in abj_items)
    if abj_total != data.get("PJO1",0):
        wrong_groups.append(("ABJ", abj_items))
    
    return wrong_groups

# ==============================
# HANDLERS
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Input Data", callback_data='input')],
        [InlineKeyboardButton("📋 Rekap Data", callback_data='rekap')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Halo! Pilih menu:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "input":
        context.user_data["data"] = {}
        context.user_data["field_idx"] = 0
        first_field = [k for g in GROUPS for k in g][0]
        await query.edit_message_text(FIELD_PROMPTS[first_field])
        return ASKING
    elif query.data == "rekap":
        data = context.user_data.get("data",{})
        text = format_rekap_text(data)
        await query.edit_message_text(text)

async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    fields = [k for g in GROUPS for k in g]
    idx = context.user_data.get("field_idx", 0)
    field = fields[idx]

    if not is_int_nonneg(text):
        await update.message.reply_text("❌ Harus angka positif. Coba lagi:")
        return ASKING

    # simpan data
    context.user_data.setdefault("data", {})[field] = int(text)
    idx += 1

    # cek apakah masih ada field berikutnya
    if idx < len(fields):
        context.user_data["field_idx"] = idx
        await update.message.reply_text(FIELD_PROMPTS[fields[idx]])
        return ASKING

    # semua data diinput, cek constraints
    wrong_groups = check_constraints_groups(context.user_data["data"])
    if wrong_groups:
        # ambil field pertama dari grup salah
        first_wrong_field = wrong_groups[0][1][0]
        idx = fields.index(first_wrong_field)
        context.user_data["field_idx"] = idx
        await update.message.reply_text(
            f"❌ Jumlah data tidak sesuai di grup {wrong_groups[0][0]}. Silakan input ulang:"
            f"\n{FIELD_PROMPTS[first_wrong_field]}"
        )
        return ASKING

    await update.message.reply_text("✅ Semua data berhasil diinput!")
    return ConversationHandler.END

# ==============================
# MAIN
# ==============================
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='input')],
        states={ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler)]},
        fallbacks=[]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler, pattern='rekap'))

    threading.Thread(target=run_flask).start()
    application.run_polling()

if __name__ == "__main__":
    main()
