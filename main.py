import os
import csv
from itertools import combinations
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    filters, ContextTypes
)

# =========================
# KONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8038423070:AAGMen0EKwhi1Up3rkWKGghg-Jf_cxgM1DI"
MIN_SUPPORT = 0.3

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
    ("ABJ1", "ABJ2", "ABJ3", "ABJ4", "ABJ5"),
]

# Prompt per field
FIELD_PROMPTS = {k: f"Masukkan nilai {k} (angka ≥0):" for g in GROUPS for k in g}

# =========================
# STATE
# =========================
ASKING = 1

# =========================
# UTIL
# =========================
def is_int_nonneg(text: str) -> bool:
    try:
        return int(text) >= 0
    except:
        return False

def clear_group(user_data: dict, group_idx: int):
    for k in GROUPS[group_idx]:
        user_data.pop(k, None)

def group_start_index(group_idx: int) -> int:
    idx = 0
    for i in range(group_idx):
        idx += len(GROUPS[i])
    return idx

def validate_group(data: dict, group_idx: int) -> tuple:
    group = GROUPS[group_idx]
    if group == ("TOTAL",):
        return True, ""
    total = data.get("TOTAL")
    if total is None:
        return False, "TOTAL belum diisi"
    vals = [data.get(k) for k in group]
    if any(v is None for v in vals):
        return False, "Ada nilai yang belum diisi di grup ini"
    s = sum(vals)
    # ABJ group = PJO1
    if group == GROUPS[-1]:
        pjo1 = data.get("PJO1")
        if pjo1 is None:
            return False, "PJO1 belum diisi"
        if s != pjo1:
            return False, f"Jumlah ABJ harus = PJO1 ({pjo1})"
        return True, ""
    # PJO1+PJO2 = TOTAL
    if group == GROUPS[10]:
        if s != total:
            return False, f"PJO1+PJO2 harus = TOTAL ({total})"
        return True, ""
    # grup lain = TOTAL
    if s != total:
        return False, f"Jumlah {group} harus = TOTAL ({total})"
    return True, ""

def export_rows_to_csv(filename, header, rows):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

def ensure_validated_data(context: ContextTypes.DEFAULT_TYPE) -> dict:
    d = {k: 0 for g in GROUPS for k in g}
    if "data" in context.user_data:
        for k,v in context.user_data["data"].items():
            d[k] = v
    return d

# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Halo! Bot siap.\nKetik /input untuk mulai input data.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🔄 Data sudah direset. Ketik /input untuk mulai lagi.")

async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["idx"] = 0
    context.user_data["data"] = {}
    first_field = GROUPS[0][0]
    await update.message.reply_text("📝 Mulai input data. Ketik angka ≥0.")
    await update.message.reply_text(FIELD_PROMPTS[first_field])
    return ASKING

async def input_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not is_int_nonneg(text):
        await update.message.reply_text("❗ Masukkan angka ≥0")
        return ASKING
    value = int(text)
    idx = context.user_data["idx"]
    fields = [k for g in GROUPS for k in g]
    key = fields[idx]
    context.user_data["data"][key] = value

    # check grup selesai
    cumulative = 0
    for gi, g in enumerate(GROUPS):
        if idx < cumulative + len(g):
            group_idx = gi
            in_group_pos = idx - cumulative
            break
        cumulative += len(g)

    if in_group_pos == len(GROUPS[group_idx])-1:
        ok, msg = validate_group(context.user_data["data"], group_idx)
        if not ok:
            clear_group(context.user_data["data"], group_idx)
            context.user_data["idx"] = group_start_index(group_idx)
            await update.message.reply_text(f"❌ {msg}\n🔁 Ulangi grup: {GROUPS[group_idx]}")
            await update.message.reply_text(FIELD_PROMPTS[GROUPS[group_idx][0]])
            return ASKING

    idx += 1
    context.user_data["idx"] = idx
    if idx >= len(fields):
        await update.message.reply_text("✅ Input selesai. Gunakan /rekap untuk melihat ringkasan.")
        return ConversationHandler.END
    next_key = fields[idx]
    await update.message.reply_text(FIELD_PROMPTS[next_key])
    return ASKING

async def input_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan. Ketik /input untuk mulai lagi.")
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
    app.run_polling()

if __name__ == "__main__":
    main()
