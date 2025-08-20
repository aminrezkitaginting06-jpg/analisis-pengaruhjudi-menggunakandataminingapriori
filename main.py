import os
import csv
from itertools import combinations
from typing import List, Tuple, Dict

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    filters, ContextTypes
)

# =========================
# KONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8417540455:AAHowzwxGRwT1BTA5sC6vO1xkBhvMeBry7U"
MIN_SUPPORT = 0.30

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

ASKING = 1

# =========================
# UTIL: file export
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

# =========================
# VALIDASI
# =========================
def is_int_nonneg(text: str) -> bool:
    try:
        v = int(text)
        return v >= 0
    except:
        return False

def validate_group(data: Dict[str, int], group_idx: int) -> Tuple[bool, str]:
    group = GROUPS[group_idx]
    if group == ("TOTAL",):
        return True, ""
    total = data.get("TOTAL", None)
    if total is None:
        return False, "TOTAL belum diisi."
    vals = [data.get(k, None) for k in group]
    if any(v is None for v in vals):
        return False, "Ada nilai yang belum diisi di grup ini."
    s = sum(vals)
    if group == GROUPS[-1]:
        pjo1 = data.get("PJO1", None)
        if pjo1 is None:
            return False, "PJO1 belum diisi. Lengkapi grup PJO dulu."
        if s != pjo1:
            return False, f"❌ ABJ1..ABJ5 harus = PJO1 ({pjo1}), sekarang = {s}."
        return True, ""
    if group == GROUPS[10]:
        if s != total:
            return False, f"❌ PJO1 + PJO2 harus = TOTAL ({total}), sekarang = {s}."
        return True, ""
    if s != total:
        return False, f"❌ Jumlah {', '.join(group)} harus = TOTAL ({total}), sekarang = {s}."
    return True, ""

def clear_group(user_data: dict, group_idx: int):
    for k in GROUPS[group_idx]:
        user_data.pop(k, None)

def group_start_index(group_idx: int) -> int:
    idx = 0
    for i in range(group_idx):
        idx += len(GROUPS[i])
    return idx

def _all_fields_linear():
    fields = []
    for g in GROUPS:
        fields.extend(g)
    return fields

def ensure_validated_data(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    d = {k: 0 for g in GROUPS for k in g}
    if "data" in context.user_data:
        for k, v in context.user_data["data"].items():
            d[k] = v
    return d

# =========================
# /START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Bot siap.\n\n"
        "Perintah:\n"
        "/input  → mulai input data responden (step-by-step + validasi)\n"
        "/rekap  → tampilkan rekap & kirim rekap.csv + rekap.txt\n"
        "/apriori1 → hasil 1-itemset (file CSV & TXT)\n"
        "/apriori2 → hasil 2-itemset (dari frequent 1-item)\n"
        "/apriori3 → hasil 3-itemset (dari frequent 2-item)\n"
        "/reset  → hapus data & mulai ulang"
    )

# =========================
# /RESET FINAL
# =========================
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hapus data user
    context.user_data.clear()

    # Stop conversation handler aktif
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    context.application.conversations.stop(chat_id=chat_id, user_id=user_id)

    # Hapus file lama (rekap & apriori)
    for f in ["rekap.csv", "rekap.txt", "apriori1.csv", "apriori1.txt",
              "apriori2.csv", "apriori2.txt", "apriori3.csv", "apriori3.txt"]:
        if os.path.exists(f):
            os.remove(f)

    await update.message.reply_text(
        "🔄 Data & file lama sudah direset. Ketik /input untuk mulai isi lagi."
    )
    return ConversationHandler.END

# =========================
# INPUT CONVERSATION
# =========================
async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["idx"] = 0
    context.user_data["data"] = {}
    first_field = _all_fields_linear()[0]
    await update.message.reply_text("📝 Mulai input data responden.\nKetik angka (bilangan bulat ≥ 0).")
    await update.message.reply_text(FIELD_PROMPTS[first_field])
    return ASKING

async def input_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not is_int_nonneg(text):
        await update.message.reply_text("❗ Masukkan angka bulat ≥ 0. Coba lagi.")
        return ASKING

    value = int(text)
    fields = _all_fields_linear()
    idx = context.user_data.get("idx", 0)
    key = fields[idx]
    context.user_data["data"][key] = value

    # Validasi grup
    cumulative = 0
    for gi, g in enumerate(GROUPS):
        if idx < cumulative + len(g):
            group_idx = gi
            in_group_pos = idx - cumulative
            group_len = len(g)
            break
        cumulative += len(g)

    if in_group_pos == group_len - 1:
        ok, msg = validate_group(context.user_data["data"], group_idx)
        if not ok:
            clear_group(context.user_data["data"], group_idx)
            context.user_data["idx"] = group_start_index(group_idx)
            await update.message.reply_text(msg)
            first_key = GROUPS[group_idx][0]
            await update.message.reply_text(f"🔁 Ulangi pengisian grup: {', '.join(GROUPS[group_idx])}")
            await update.message.reply_text(FIELD_PROMPTS[first_key])
            return ASKING

    idx += 1
    context.user_data["idx"] = idx
    if idx >= len(fields):
        context.user_data["validated"] = True
        await update.message.reply_text("✅ Input selesai & valid! Gunakan /rekap untuk melihat ringkasan.")
        return ConversationHandler.END

    next_key = fields[idx]
    await update.message.reply_text(FIELD_PROMPTS[next_key])
    return ASKING

async def input_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Dibatalkan. Ketik /input untuk mulai lagi.")
    return ConversationHandler.END

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("input", input_start)],
        states={ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_ask)]},
        fallbacks=[CommandHandler("cancel", input_cancel)],
        name="input_conversation",
        persistent=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(conv)
    # Tambahkan handler rekap & apriori sesuai kode sebelumnya
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(CommandHandler("apriori1", apriori1))
    app.add_handler(CommandHandler("apriori2", apriori2))
    app.add_handler(CommandHandler("apriori3", apriori3))

    app.run_polling()

if __name__ == "__main__":
    main()
