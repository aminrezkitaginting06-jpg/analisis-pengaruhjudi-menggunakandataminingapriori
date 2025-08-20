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
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8038423070:AAGMen0EKwhi1Up3rkWKGghg-Jf_cxgM1DI"
MIN_SUPPORT = 0.30

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
    "TOTAL": "📊 Masukkan TOTAL keseluruhan data yang dianalisis (angka):",
    "JK1": "👩 Masukkan Jumlah Perempuan (JK1):",
    "JK2": "👨 Masukkan Jumlah Laki-Laki (JK2):",
    "UMR1": "🎂 Masukkan Jumlah usia < 20 Tahun (UMR1):",
    "UMR2": "🧑‍💼 Masukkan Jumlah usia 20-30 Tahun (UMR2):",
    "UMR3": "👨‍👩‍👧‍👦 Masukkan Jumlah usia 31-40 Tahun (UMR3):",
    "UMR4": "👴 Masukkan Jumlah usia 41-50 Tahun (UMR4):",
    "UMR5": "👵 Masukkan Jumlah usia > 50 Tahun (UMR5):",
    "PT1": "📚 Masukkan Tamatan SD/Sederajat (PT1):",
    "PT2": "🏫 Masukkan Tamatan SMP/Sederajat (PT2):",
    "PT3": "🎓 Masukkan Tamatan SMA/Sederajat (PT3):",
    "PT4": "🎓🎓 Masukkan Tamatan Diploma/Sarjana (PT4):",
    "FBJ1": "📅🔥 Masukkan Frek. Bermain Hampir Setiap Hari (FBJ1):",
    "FBJ2": "📅 Masukkan Frek. Bermain 2-3 kali/minggu (FBJ2):",
    "FBJ3": "📆 Masukkan Frek. Bermain 1 kali/minggu (FBJ3):",
    "FBJ4": "⏳ Masukkan Frek. Bermain <1 kali/minggu (FBJ4):",
    "JJ1": "🎲 Masukkan Jenis Judi Togel/Lotere Online (JJ1):",
    "JJ2": "⚽ Masukkan Jenis Judi Taruhan Olahraga (JJ2):",
    "JJ3": "🃏 Masukkan Jenis Judi Kasino Online (JJ3):",
    "JJ4": "❓ Masukkan Jenis Judi Lainnya (JJ4):",
    "PDB1": "💸 Masukkan Pengeluaran < Rp 500Rb (PDB1):",
    "PDB2": "💰 Masukkan Pengeluaran Rp 500Rb - Rp 2 Jt (PDB2):",
    "PDB3": "💵 Masukkan Pengeluaran 2 Jt - 5 Jt (PDB3):",
    "PDB4": "🏦 Masukkan Pengeluaran > Rp 5 Jt (PDB4):",
    "MK1": "❗ Masukkan Masalah Keuangan YA (MK1):",
    "MK2": "✔️ Masalah Keuangan TIDAK (MK2):",
    "FB1": "🙅‍♂️ Masukkan Frek. Bertengkar Tidak Pernah (FB1):",
    "FB2": "🤏 Masukkan Frek. Bertengkar Jarang 1-2 Kali/bln (FB2):",
    "FB3": "🔥 Masukkan Frek. Bertengkar Sering 1-2 Kali/bln (FB3):",
    "FB4": "💥 Masukkan Frek. Bertengkar Hampir Setiap Hari (FB4):",
    "KJO1": "🎰❗ Masukkan Kecanduan Judi Online YA (KJO1):",
    "KJO2": "✔️ Masukkan Kecanduan Judi Online TIDAK (KJO2):",
    "PJO1": "💔 Masukkan Perceraian YA (PJO1):",
    "PJO2": "💖 Masukkan Perceraian TIDAK (PJO2):",
    "ABJ1": "🎰 Masukkan Kecanduan Bermain Judi Online (ABJ1):",
    "ABJ2": "❗ Masalah Keuangan dalam Pernikahan (ABJ2):",
    "ABJ3": "🗣️ Pertengkaran/Komunikasi yang Buruk (ABJ3):",
    "ABJ4": "⚠️ Kekerasan dalam Rumah Tangga (ABJ4):",
    "ABJ5": "🤥 Ketidakjujuran Pasangan akibat Judi (ABJ5):",
}

# =========================
# STATE Conversational
# =========================
ASKING = 1

# =========================
# UTILS
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
    # ABJ group
    if group == GROUPS[-1]:
        pjo1 = data.get("PJO1", None)
        if pjo1 is None:
            return False, "PJO1 belum diisi."
        if s != pjo1:
            return False, f"❌ ABJ1..ABJ5 harus = PJO1 ({pjo1}), sekarang = {s}."
        return True, ""
    # PJO group juga harus = TOTAL
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
# FORMAT REKAP
# =========================
def format_rekap_text(d: Dict[str, int]) -> str:
    val = lambda k: d.get(k, 0)
    text = f"📋 Berikut rekap data yang telah kamu input:\n\n📊 Total: {val('TOTAL')}\n\n"
    for g in GROUPS[1:]:
        for k in g:
            text += f"{ITEM_LABELS.get(k, k)}: {val(k)}\n"
        text += "\n"
    return text

def rekap_rows_csv(d: Dict[str, int]) -> List[List[str]]:
    rows = []
    for g in GROUPS:
        for k in g:
            label = ITEM_LABELS.get(k, k) if k != "TOTAL" else "📊 TOTAL"
            rows.append([label, str(d.get(k, 0))])
    return rows

# =========================
# APRIORI
# =========================
def one_itemset(data: Dict[str, int]):
    total = data["TOTAL"]
    out = []
    for k, v in data.items():
        if k == "TOTAL":
            continue
        support = v/total if total>0 else 0
        out.append(((k,), v, support, support>=MIN_SUPPORT))
    return out

def k_itemset_from_candidates(data: Dict[str,int], candidates):
    total = data["TOTAL"]
    out = []
    for combo in candidates:
        freq = min(data[c] for c in combo)
        support = freq/total if total>0 else 0
        out.append((combo, freq, support, support>=MIN_SUPPORT))
    return out

def apriori_generate_candidates(prev_frequents, k):
    prev_sorted = [tuple(sorted(x)) for x in prev_frequents]
    prev_sorted = sorted(set(prev_sorted))
    candidates = set()
    for i in range(len(prev_sorted)):
        for j in range(i+1, len(prev_sorted)):
            a, b = prev_sorted[i], prev_sorted[j]
            if a[:k-2]==b[:k-2]:
                new = tuple(sorted(set(a).union(b)))
                if len(new)==k:
                    all_subfreq = True
                    for sub in combinations(new, k-1):
                        if tuple(sorted(sub)) not in prev_sorted:
                            all_subfreq = False
                            break
                    if all_subfreq:
                        candidates.add(new)
    return sorted(candidates)

def apriori_to_rows(data: Dict[str,int], k: int):
    if k==1:
        result = one_itemset(data)
    else:
        prev_rows, prev_freq = apriori_to_rows(data, k-1)
        candidates = apriori_generate_candidates(prev_freq, k)
        result = k_itemset_from_candidates(data, candidates)
    rows = []
    frequents = []
    total = data["TOTAL"]
    for combo, freq, support, is_freq in result:
        labels = " + ".join(ITEM_LABELS[c] for c in combo)
        rows.append([labels, f"{freq}/{total}={support:.2f}", "YES" if is_freq else "NO"])
        if is_freq:
            frequents.append(combo)
    return rows, frequents

# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Bot siap.\n\n"
        "/input → mulai input data\n"
        "/rekap → tampil rekap data\n"
        "/apriori1 → 1-itemset\n"
        "/apriori2 → 2-itemset\n"
        "/apriori3 → 3-itemset\n"
        "/reset → reset data"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("♻️ Data berhasil direset.")

async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["data"] = {}
    context.user_data["field_idx"] = 0
    field = _all_fields_linear()[0]
    await update.message.reply_text(FIELD_PROMPTS[field])
    return ASKING

async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    fields = _all_fields_linear()
    idx = context.user_data.get("field_idx", 0)
    field = fields[idx]

    if not is_int_nonneg(text):
        await update.message.reply_text("❌ Harus angka positif. Coba lagi:")
        return ASKING
    context.user_data["data"][field] = int(text)

    # Validasi grup jika terakhir
    for g_idx, g in enumerate(GROUPS):
        if field in g:
            valid, msg = validate_group(context.user_data["data"], g_idx)
            if not valid:
                clear_group(context.user_data["data"], g_idx)
                await update.message.reply_text(f"{msg}\n💡 Input ulang grup ini:")
                return ASKING
            break

    idx += 1
    if idx >= len(fields):
        await update.message.reply_text("✅ Semua data berhasil diinput!")
        return ConversationHandler.END

    context.user_data["field_idx"] = idx
    next_field = fields[idx]
    await update.message.reply_text(FIELD_PROMPTS[next_field])
    return ASKING

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = ensure_validated_data(context)
    text = format_rekap_text(data)
    await update.message.reply_text(text)

    # Export CSV/TXT
    export_rows_to_csv("rekap.csv", ["Item", "Jumlah"], rekap_rows_csv(data))
    export_text("rekap.txt", text)

async def apriori1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = ensure_validated_data(context)
    rows, _ = apriori_to_rows(data, 1)
    txt = "📊 1-Itemset (Support ≥ {:.0%})\n".format(MIN_SUPPORT)
    for r in rows:
        txt += f"{r[0]} → {r[1]} ({r[2]})\n"
    await update.message.reply_text(txt)
    export_text("apriori1.txt", txt)

async def apriori2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = ensure_validated_data(context)
    rows, _ = apriori_to_rows(data, 2)
    txt = "📊 2-Itemset (Support ≥ {:.0%})\n".format(MIN_SUPPORT)
    for r in rows:
        txt += f"{r[0]} → {r[1]} ({r[2]})\n"
    await update.message.reply_text(txt)
    export_text("apriori2.txt", txt)

async def apriori3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = ensure_validated_data(context)
    rows, _ = apriori_to_rows(data, 3)
    txt = "📊 3-Itemset (Support ≥ {:.0%})\n".format(MIN_SUPPORT)
    for r in rows:
        txt += f"{r[0]} → {r[1]} ({r[2]})\n"
    await update.message.reply_text(txt)
    export_text("apriori3.txt", txt)

# =========================
# MAIN
# =========================
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('input', input_start)],
        states={
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler)],
        },
        fallbacks=[CommandHandler('reset', reset)]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("rekap", rekap))
    application.add_handler(CommandHandler("apriori1", apriori1))
    application.add_handler(CommandHandler("apriori2", apriori2))
    application.add_handler(CommandHandler("apriori3", apriori3))
    application.add_handler(CommandHandler("reset", reset))

    application.run_polling()

if __name__ == "__main__":
    main()
