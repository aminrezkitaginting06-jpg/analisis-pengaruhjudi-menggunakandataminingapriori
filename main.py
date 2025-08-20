import os
import csv
from datetime import datetime
from itertools import combinations
from typing import List, Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# =========================
# KONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8417540455:AAHowzwxGRwT1BTA5sC6vO1xkBhvMeBry7U"

DATA_FILE = "responden.csv"
BACKUP_FOLDER = "backup"
RESTORE_LOG = "restore_log.txt"

ASKING = 1

if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)

# =========================
# MAIN MENU KEYBOARD
# =========================
def get_responden_count(context=None):
    if context and "data" in context.user_data:
        return context.user_data["data"].get("TOTAL", 0)
    return 0

def main_menu_keyboard(context=None):
    total = get_responden_count(context)
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

# =========================
# BACKUP / RESTORE / LOG
# =========================
def save_backup(data: Dict[str, int]) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(BACKUP_FOLDER, f"backup_{ts}.csv")
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for k, v in data.items():
            writer.writerow([k, v])
    return filename

def restore_backup(filename: str, context: ContextTypes.DEFAULT_TYPE):
    data = {}
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                key, val = row
                data[key] = int(val)
    context.user_data["data"] = data
    with open(RESTORE_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Restored {filename}\n")

def list_backups() -> List[str]:
    return sorted(os.listdir(BACKUP_FOLDER))

def clear_backups():
    for f in os.listdir(BACKUP_FOLDER):
        os.remove(os.path.join(BACKUP_FOLDER, f))

def read_restore_log() -> str:
    if not os.path.exists(RESTORE_LOG):
        return ""
    with open(RESTORE_LOG, "r", encoding="utf-8") as f:
        return f.read()

def clear_restore_log():
    if os.path.exists(RESTORE_LOG):
        os.remove(RESTORE_LOG)

# =========================
# CALLBACK HANDLER
# =========================
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "input":
        await input_start(update, context)
    elif data == "rekap":
        await rekap(update, context)
    elif data == "reset":
        context.user_data.clear()
        await query.message.reply_text("🔄 Data sudah direset.")
    elif data == "download_backup":
        backups = list_backups()
        if backups:
            files = "\n".join(backups)
            await query.message.reply_text(f"📦 Backup tersedia:\n{files}")
        else:
            await query.message.reply_text("❌ Belum ada backup tersedia.")
    elif data == "delete_backup":
        clear_backups()
        await query.message.reply_text("🗑 Semua backup dihapus.")
    elif data == "restore_backup":
        backups = list_backups()
        if backups:
            restore_backup(os.path.join(BACKUP_FOLDER, backups[-1]), context)
            await query.message.reply_text(f"♻️ Restore sukses dari {backups[-1]}")
        else:
            await query.message.reply_text("❌ Belum ada backup untuk restore.")
    elif data == "view_restore_log":
        log = read_restore_log()
        if log:
            await query.message.reply_text(f"📜 Log Restore:\n{log}")
        else:
            await query.message.reply_text("📜 Belum ada log restore.")
    elif data == "clear_restore_log":
        clear_restore_log()
        await query.message.reply_text("🧹 Log restore sudah dibersihkan.")
    elif data.startswith("apriori"):
        await query.message.reply_text(f"🧩 {data.capitalize()} placeholder")
    else:
        await query.message.reply_text(f"⚠️ Tombol {data} belum diimplementasikan.")

# =========================
# START / INPUT / REKAP
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Halo! Pilih menu di bawah:", reply_markup=main_menu_keyboard(context))

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data.get("data")
    if not data:
        await update.message.reply_text("❌ Belum ada data yang diinput.")
        return
    msg = "📊 Rekap Data:\n"
    for k, v in data.items():
        msg += f"{k}: {v}\n"
    await update.message.reply_text(msg)

async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["data"] = {}
    await update.message.reply_text("📝 Placeholder: Mulai input data...")
    await update.message.reply_text("Gunakan /rekap untuk lihat data setelah input.")

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(main_menu_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
