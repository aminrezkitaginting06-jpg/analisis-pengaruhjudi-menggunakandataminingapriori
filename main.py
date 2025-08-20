import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

# =========================
# KONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8304855655:AAG4TChMmiyG5teVNcn4-zMWOwL7mlMmMd0"

# =========================
# STATES
# =========================
MENU, INPUT_TOTAL, INPUT_SUBCATEGORIES = range(3)

# =========================
# KATEGORI & SUBKATEGORI + EMOJI
# =========================
CATEGORIES = [
    ("👩‍👩‍👦 JK", ["JK1", "JK2"]),
    ("🎂 UMR", ["UMR1","UMR2","UMR3","UMR4","UMR5"]),
    ("🧑‍💼 PT", ["PT1","PT2"]),
    ("📚 FBJ", ["FBJ1","FBJ2"]),
    ("🏃 JJ", ["JJ1","JJ2"]),
    ("💰 PDB", ["PDB1","PDB2"]),
    ("🏫 MK", ["MK1","MK2"]),
    ("🎨 FB", ["FB1","FB2"]),
    ("⚙️ KJO", ["KJO1","KJO2"]),
    ("🛠️ PBJO", ["PBJO1","PBJO2"]),
    ("🎯 PJO1", ["PJO1"]),
    ("📊 ABJ", ["ABJ1","ABJ2","ABJ3","ABJ4","ABJ5"])
]

# =========================
# HANDLER
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔹 Mulai Input Data", callback_data='start_input')],
        [InlineKeyboardButton("📋 Lihat Rekap", callback_data='rekap')],
        [InlineKeyboardButton("❌ Keluar", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Selamat datang!\nSilakan pilih menu:", reply_markup=reply_markup)
    return MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'start_input':
        context.user_data.clear()
        await query.edit_message_text("📝 Masukkan Total Keseluruhan Data (angka):")
        context.user_data['category_index'] = 0
        return INPUT_TOTAL
    elif query.data == 'rekap':
        await display_rekap(update, context)
        return MENU
    elif query.data == 'cancel':
        await query.edit_message_text("❌ Conversation dibatalkan. Ketik /start untuk mulai lagi.")
        return ConversationHandler.END

async def input_total_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ Mohon masukkan angka valid untuk Total Keseluruhan Data!")
        return INPUT_TOTAL

    context.user_data['TOTAL'] = int(text)
    context.user_data['category_index'] = 0
    category_name = CATEGORIES[0][0]
    num_subs = len(CATEGORIES[0][1])
    await update.message.reply_text(f"✅ Total data disimpan: {text}\nMasukkan nilai subkategori {category_name} ({num_subs} angka, jumlah harus sama dengan total)")
    return INPUT_SUBCATEGORIES

async def input_subcategories_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = context.user_data['TOTAL']
    idx = context.user_data.get('category_index', 0)
    category_name, subcats = CATEGORIES[idx]

    try:
        values = [int(x.strip()) for x in update.message.text.strip().split()]
    except:
        await update.message.reply_text("⚠️ Masukkan angka valid, pisahkan dengan spasi!")
        return INPUT_SUBCATEGORIES

    if len(values) != len(subcats):
        await update.message.reply_text(f"⚠️ Jumlah input salah! {category_name} memiliki {len(subcats)} subkategori: {', '.join(subcats)}")
        return INPUT_SUBCATEGORIES

    if category_name not in ["📊 ABJ", "🎯 PJO1"] and sum(values) != total:
        await update.message.reply_text(f"⚠️ Total {category_name} = {sum(values)} tidak sama dengan TOTAL = {total}")
        return INPUT_SUBCATEGORIES

    for sub, val in zip(subcats, values):
        context.user_data[sub] = val

    idx += 1
    context.user_data['category_index'] = idx
    if idx >= len(CATEGORIES):
        sum_abj = sum([context.user_data.get(sub,0) for sub in CATEGORIES[-1][1]])
        pjo1 = context.user_data.get('PJO1',0)
        if sum_abj != pjo1:
            context.user_data['category_index'] = idx-1
            await update.message.reply_text(f"⚠️ Jumlah 📊 ABJ = {sum_abj} harus sama dengan 🎯 PJO1 = {pjo1}. Masukkan ulang ABJ:")
            return INPUT_SUBCATEGORIES
        await update.message.reply_text("✅ Semua data valid! Kembali ke menu utama atau lihat rekap.")
        return MENU
    else:
        next_category_name, next_subcats = CATEGORIES[idx]
        await update.message.reply_text(f"Masukkan nilai subkategori {next_category_name} ({len(next_subcats)} angka, jumlah harus = {total})")
        return INPUT_SUBCATEGORIES

async def display_rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    if not data:
        await update.callback_query.edit_message_text("⚠️ Belum ada data yang diinput.")
        return

    text = "📋 *Rekap Data User*\n\n"
    total = data.get('TOTAL',0)
    text += f"📊 Total Keseluruhan Data: {total}\n\n"

    for cat_name, subcats in CATEGORIES:
        vals = [str(data.get(sub,0)) for sub in subcats]
        text += f"{cat_name}: " + " | ".join(vals) + f" (Jumlah: {sum([int(v) for v in vals])})\n"

    keyboard = [
        [InlineKeyboardButton("🔄 Restart Input", callback_data='start_input')],
        [InlineKeyboardButton("↩ Kembali ke Menu", callback_data='back_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def back_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)
    return MENU

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [
                CallbackQueryHandler(menu_handler, pattern='^(start_input|rekap|cancel)$'),
                CallbackQueryHandler(back_menu_handler, pattern='^back_menu$')
            ],
            INPUT_TOTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_total_handler)],
            INPUT_SUBCATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_subcategories_handler)]
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)]
        # per_message=True dihapus
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
