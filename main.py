import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters, ContextTypes

# =========================
# KONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8304855655:AAG4TChMmiyG5teVNcn4-zMWOwL7mlMmMd0"

# =========================
# STATE INPUT
# =========================
(
    PT1, PT2, PT3, PT4,
    FBJ1, FBJ2, FBJ3, FBJ4,
    JJ1, JJ2, JJ3, JJ4,
    PDB1, PDB2, PDB3, PDB4,
    MK1, MK2,
    FB1, FB2, FB3, FB4,
    KJO1, KJO2,
    PJO1, PJO2,
    ABJ1, ABJ2, ABJ3, ABJ4, ABJ5,
    TOTAL,
) = range(32)

# =========================
# PENYIMPAN DATA
# =========================
user_data_store = {}

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id] = {}
    await update.message.reply_text("📋 Masukkan jumlah TOTAL data:")
    return TOTAL

# =========================
# FUNGSI SIMPAN INPUT
# =========================
async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, next_state: int, prompt: str):
    user_data_store[update.effective_chat.id][key] = int(update.message.text)
    await update.message.reply_text(prompt)
    return next_state

# =========================
# VALIDASI
# =========================
def validate_data(data: dict):
    total = data.get("TOTAL", 0)

    checks = []

    # Semua kategori selain ABJ harus sama dengan TOTAL
    kategori = ["PT", "FBJ", "JJ", "PDB", "MK", "FB", "KJO", "PJO"]
    for k in kategori:
        keys = [x for x in data.keys() if x.startswith(k)]
        jumlah = sum(data.get(x, 0) for x in keys)
        if jumlah != total:
            checks.append(f"❌ {k} tidak valid (jumlah={jumlah}, harus={total})")

    # ABJ validasi khusus
    abj_total = sum(data.get(f"ABJ{i}", 0) for i in range(1, 6))
    if abj_total != data.get("PJO1", 0):
        checks.append(f"❌ ABJ tidak valid (jumlah={abj_total}, harus={data.get('PJO1', 0)})")

    return checks

# =========================
# HASIL REKAP
# =========================
def format_output(data: dict):
    return (
        f"📊 Hasil Rekap Data\n\n"
        f"📋 Total: {data.get('TOTAL', 0)}\n\n"
        f"🏫 PT: {data.get('PT1', 0)}, {data.get('PT2', 0)}, {data.get('PT3', 0)}, {data.get('PT4', 0)}\n"
        f"📚 FBJ: {data.get('FBJ1', 0)}, {data.get('FBJ2', 0)}, {data.get('FBJ3', 0)}, {data.get('FBJ4', 0)}\n"
        f"🎓 JJ: {data.get('JJ1', 0)}, {data.get('JJ2', 0)}, {data.get('JJ3', 0)}, {data.get('JJ4', 0)}\n"
        f"🧑‍💼 PDB: {data.get('PDB1', 0)}, {data.get('PDB2', 0)}, {data.get('PDB3', 0)}, {data.get('PDB4', 0)}\n"
        f"📖 MK: {data.get('MK1', 0)}, {data.get('MK2', 0)}\n"
        f"👥 FB: {data.get('FB1', 0)}, {data.get('FB2', 0)}, {data.get('FB3', 0)}, {data.get('FB4', 0)}\n"
        f"🏢 KJO: {data.get('KJO1', 0)}, {data.get('KJO2', 0)}\n"
        f"📌 PJO: {data.get('PJO1', 0)}, {data.get('PJO2', 0)}\n"
        f"📝 ABJ: {data.get('ABJ1', 0)}, {data.get('ABJ2', 0)}, {data.get('ABJ3', 0)}, {data.get('ABJ4', 0)}, {data.get('ABJ5', 0)}\n"
    )

# =========================
# VALIDASI & AUTO OUTPUT
# =========================
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data_store.get(update.effective_chat.id, {})

    errors = validate_data(data)
    if errors:
        msg = "⚠️ Data tidak valid:\n" + "\n".join(errors)
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("✅ Data valid!")

    # langsung auto tampilkan hasil rekap
    await update.message.reply_text(format_output(data))
    return ConversationHandler.END

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: save_input(u, c, "TOTAL", PT1, "🏫 Masukkan PT1:"))],
            PT1: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: save_input(u, c, "PT1", PT2, "🏫 Masukkan PT2:"))],
            PT2: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: save_input(u, c, "PT2", PT3, "🏫 Masukkan PT3:"))],
            PT3: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: save_input(u, c, "PT3", PT4, "🏫 Masukkan PT4:"))],
            PT4: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: save_input(u, c, "PT4", FBJ1, "📚 Masukkan FBJ1:"))],
            # tambahin semua step lain sesuai urutan (FBJ1 → FBJ4 → JJ1 → ... → ABJ5)
            ABJ5: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: save_input(u, c, "ABJ5", ConversationHandler.END, "✅ Semua data masuk, sedang validasi..."))],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, done))  # auto validasi setelah selesai

    app.run_polling()

if __name__ == "__main__":
    main()
