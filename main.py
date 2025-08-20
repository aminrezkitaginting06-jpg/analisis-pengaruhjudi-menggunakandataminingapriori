import os
import csv
from itertools import combinations
from typing import List, Tuple, Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# =========================
# KONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8417540455:AAHowzwxGRwT1BTA5sC6vO1xkBhvMeBry7U"
MIN_SUPPORT = 0.30

# Urutan input & grup validasi
GROUPS = [
    ("TOTAL",),  # 0
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
    ("ABJ1", "ABJ2", "ABJ3", "ABJ4", "ABJ5"),
]

ITEM_LABELS = {
    "JK1": "👩 JK1", "JK2": "👨 JK2",
    "UMR1": "🎂 UMR1", "UMR2": "🧑‍💼 UMR2", "UMR3": "👨‍👩‍👧‍👦 UMR3",
    "UMR4": "👴 UMR4", "UMR5": "👵 UMR5",
    "PT1": "📚 PT1", "PT2": "🏫 PT2", "PT3": "🎓 PT3", "PT4": "🎓🎓 PT4",
    "FBJ1": "📅🔥 FBJ1", "FBJ2": "📅 FBJ2", "FBJ3": "📆 FBJ3", "FBJ4": "⏳ FBJ4",
    "JJ1": "🎲 JJ1", "JJ2": "⚽ JJ2", "JJ3": "🃏 JJ3", "JJ4": "❓ JJ4",
    "PDB1": "💸 PDB1", "PDB2": "💰 PDB2", "PDB3": "💵 PDB3", "PDB4": "🏦 PDB4",
    "MK1": "❗ MK1", "MK2": "✔️ MK2",
    "FB1": "🙅‍♂️ FB1", "FB2": "🤏 FB2", "FB3": "🔥 FB3", "FB4": "💥 FB4",
    "KJO1": "🎰❗ KJO1", "KJO2": "✔️ KJO2",
    "PJO1": "💔 PJO1", "PJO2": "💖 PJO2",
    "ABJ1": "🎰 ABJ1", "ABJ2": "❗ ABJ2", "ABJ3": "🗣️ ABJ3", "ABJ4": "⚠️ ABJ4", "ABJ5": "🤥 ABJ5",
}

FIELD_PROMPTS = {
    "TOTAL": "Masukkan TOTAL keseluruhan data yang dianalisis (angka):",
    "JK1": "Masukkan Jumlah Perempuan (JK1):",
    "JK2": "Masukkan Jumlah Laki-Laki (JK2):",
    "UMR1": "Masukkan Jumlah usia < 20 Tahun (UMR1):",
    "UMR2": "Masukkan Jumlah usia 20-30 Tahun (UMR2):",
    "UMR3": "Masukkan Jumlah usia 31-40 Tahun (UMR3):",
    "UMR4": "Masukkan Jumlah usia 41-50 Tahun (UMR4):",
    "UMR5": "Masukkan Jumlah usia > 50 Tahun (UMR5):",
    "PT1": "Masukkan Tamatan SD/Sederajat (PT1):",
    "PT2": "Masukkan Tamatan SMP/Sederajat (PT2):",
    "PT3": "Masukkan Tamatan SMA/Sederajat (PT3):",
    "PT4": "Masukkan Tamatan Diploma/Sarjana (PT4):",
    "FBJ1": "Masukkan Frek. Bermain Hampir Setiap Hari (FBJ1):",
    "FBJ2": "Masukkan Frek. Bermain 2-3 kali/minggu (FBJ2):",
    "FBJ3": "Masukkan Frek. Bermain 1 kali/minggu (FBJ3):",
    "FBJ4": "Masukkan Frek. Bermain <1 kali/minggu (FBJ4):",
    "JJ1": "Masukkan Jenis Judi Togel/Lotere Online (JJ1):",
    "JJ2": "Masukkan Jenis Judi Taruhan Olahraga (JJ2):",
    "JJ3": "Masukkan Jenis Judi Kasino Online (JJ3):",
    "JJ4": "Masukkan Jenis Judi Lainnya (JJ4):",
    "PDB1": "Masukkan Pengeluaran < Rp 500Rb (PDB1):",
    "PDB2": "Masukkan Pengeluaran Rp 500Rb - Rp 2 Jt (PDB2):",
    "PDB3": "Masukkan Pengeluaran 2 Jt - 5 Jt (PDB3):",
    "PDB4": "Masukkan Pengeluaran > Rp 5 Jt (PDB4):",
    "MK1": "Masukkan Masalah Keuangan YA (MK1):",
    "MK2": "Masukkan Masalah Keuangan TIDAK (MK2):",
    "FB1": "Masukkan Frek. Bertengkar Tidak Pernah (FB1):",
    "FB2": "Masukkan Frek. Bertengkar Jarang 1-2 Kali/bln (FB2):",
    "FB3": "Masukkan Frek. Bertengkar Sering 1-2 Kali/bln (FB3):",
    "FB4": "Masukkan Frek. Bertengkar Hampir Setiap Hari (FB4):",
    "KJO1": "Masukkan Kecanduan Judi Online YA (KJO1):",
    "KJO2": "Masukkan Kecanduan Judi Online TIDAK (KJO2):",
    "PJO1": "Masukkan Perceraian YA (PJO1):",
    "PJO2": "Masukkan Perceraian TIDAK (PJO2):",
    "ABJ1": "Masukkan Kecanduan Bermain Judi Online (ABJ1):",
    "ABJ2": "Masukkan Masalah Keuangan dalam Pernikahan (ABJ2):",
    "ABJ3": "Masukkan Pertengkaran/Komunikasi yang Buruk (ABJ3):",
    "ABJ4": "Masukkan Kekerasan dalam Rumah Tangga (ABJ4):",
    "ABJ5": "Masukkan Ketidakjujuran Pasangan akibat Judi (ABJ5):",
}

# =========================
# STATE Conversational
# =========================
ASKING = 1

# =========================
# UTIL
# =========================
def export_rows_to_csv(filename: str, header: List[str], rows: List[List[str]]):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in rows:
            writer.writerow(r)

def export_text(filename: str, content: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def is_int_nonneg(text: str) -> bool:
    try:
        return int(text) >= 0
    except:
        return False

def get_responden_count() -> int:
    # Placeholder, bisa dihitung dari backup/file CSV nyata
    return 0

# =========================
# MAIN MENU INLINE
# =========================
def main_menu_keyboard():
    total = get_responden_count()
    keyboard = [
        [
            InlineKeyboardButton("📥 Input Data", callback_data="input"),
            InlineKeyboardButton(f"📊 Rekap ({total} responden)", callback_data="rekap"),
        ],
        [
            InlineKeyboardButton("🔄 Reset", callback_data="reset"),
            InlineKeyboardButton("📦 Download Backup", callback_data="download_backup"),
        ],
        [
            InlineKeyboardButton("🗑 Hapus Semua Backup", callback_data="delete_backup"),
            InlineKeyboardButton("♻️ Restore Backup", callback_data="restore_backup"),
        ],
        [
            InlineKeyboardButton("📜 Lihat Log Restore", callback_data="view_restore_log"),
            InlineKeyboardButton("🧹 Clear Log Restore", callback_data="clear_restore_log"),
        ],
        [
            InlineKeyboardButton("🔍 Cari di Log Restore", callback_data="search_restore_log"),
            InlineKeyboardButton("📅 Filter Tanggal Log Restore", callback_data="filter_date_log"),
        ],
        [
            InlineKeyboardButton("📊 Grafik Restore Log", callback_data="chart_restore_log"),
            InlineKeyboardButton("👤 Grafik Restore Per User", callback_data="chart_user_restore"),
        ],
        [
            InlineKeyboardButton("📂 Export Statistik Restore (Excel)", callback_data="export_restore_excel"),
        ],
        [
            InlineKeyboardButton("🧩 Apriori 1", callback_data="apriori1"),
            InlineKeyboardButton("🧩 Apriori 2", callback_data="apriori2"),
            InlineKeyboardButton("🧩 Apriori 3", callback_data="apriori3"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_source = update.message or update.callback_query.message
    await msg_source.reply_text("🗂 Menu Utama:", reply_markup=main_menu_keyboard())

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "input":
        # panggil input_start tapi aman untuk callback
        await input_start(update, context)
    elif data == "rekap":
        await rekap(update, context)
    elif data == "reset":
        context.user_data.clear()
        msg_source = update.callback_query.message
        await msg_source.reply_text("🔄 Data direset.")
    else:
        msg_source = update.callback_query.message
        await msg_source.reply_text(f"Fitur {data} belum tersedia (placeholder).")

# =========================
# INPUT / REKAP / APRIORI (placeholder, bisa pakai versi lengkap sebelumnya)
# =========================
async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["idx"] = 0
    context.user_data["data"] = {}
    msg_source = update.message or update.callback_query.message
    await msg_source.reply_text("📝 Mulai input data (placeholder).")
    await msg_source.reply_text("Gunakan /rekap untuk melihat ringkasan.")
    return ConversationHandler.END

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_source = update.message or update.callback_query.message
    await msg_source.reply_text("📋 Menampilkan rekap data (placeholder).")

async def apriori1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_source = update.message or update.callback_query.message
    await msg_source.reply_text("🧩 Apriori 1-itemset (placeholder).")

async def apriori2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_source = update.message or update.callback_query.message
    await msg_source.reply_text("🧩 Apriori 2-itemset (placeholder).")

async def apriori3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_source = update.message or update.callback_query.message
    await msg_source.reply_text("🧩 Apriori 3-itemset (placeholder).")

# =========================
# START / RESET
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    msg_source = update.message or update.callback_query.message
    await msg_source.reply_text("🔄 Data kamu sudah direset.")

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler untuk input (placeholder)
    conv = ConversationHandler(
        entry_points=[CommandHandler("input", input_start)],
        states={ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_start)]},
        fallbacks=[CommandHandler("cancel", input_start)],
        name="input_conversation",
        persistent=False,
    )

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(conv)
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(CommandHandler("apriori1", apriori1))
    app.add_handler(CommandHandler("apriori2", apriori2))
    app.add_handler(CommandHandler("apriori3", apriori3))
    app.add_handler(CallbackQueryHandler(main_menu_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
