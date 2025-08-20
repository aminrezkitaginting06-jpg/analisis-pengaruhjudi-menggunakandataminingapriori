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
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8304855655:AAGMmOBEt3gcmeDKwC4PEARhTp-Bc8Fl-JQ"
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

# Label tampil (emoji diperbaiki)
ITEM_LABELS = {
    "JK1": "👩 JK1", "JK2": "👨 JK2",
    "UMR1": "🎂 UMR1", "UMR2": "🧑‍🦱 UMR2", "UMR3": "👨‍👩‍👦 UMR3",
    "UMR4": "👴 UMR4", "UMR5": "👵 UMR5",
    "PT1": "📚 PT1", "PT2": "🏫 PT2", "PT3": "🎓 PT3", "PT4": "🎓🎓 PT4",
    "FBJ1": "📘🔥 FBJ1", "FBJ2": "📘 FBJ2", "FBJ3": "📗 FBJ3", "FBJ4": "⏳ FBJ4",
    "JJ1": "🎲 JJ1", "JJ2": "⚽ JJ2", "JJ3": "🎰 JJ3", "JJ4": "✔️ JJ4",
    "PDB1": "💸 PDB1", "PDB2": "💰 PDB2", "PDB3": "💵 PDB3", "PDB4": "🏦 PDB4",
    "MK1": "❗ MK1", "MK2": "✅ MK2",
    "FB1": "👨‍❤️‍👨 FB1", "FB2": "🫰 FB2", "FB3": "💥 FB3", "FB4": "💣 FB4",
    "KJO1": "🎰❗ KJO1", "KJO2": "✅ KJO2",
    "PJO1": "💔 PJO1", "PJO2": "💖 PJO2",
    "ABJ1": "🎰 ABJ1", "ABJ2": "❗ ABJ2", "ABJ3": "🧨 ABJ3", "ABJ4": "⚠️ ABJ4", "ABJ5": "🫠 ABJ5",
}

# Prompt per field
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

# =========================
# REKAP FORMAT (emoji diperbaiki)
# =========================
def format_rekap_text(d: Dict[str, int]) -> str:
    val = lambda k: d.get(k, 0)
    return f"""📋 Berikut rekap data yang telah kamu input:

📊 Total keseluruhan data yang dianalisis: {val('TOTAL')}

👩 Jumlah Perempuan (JK1): {val('JK1')}  
👨 Jumlah Laki-Laki (JK2): {val('JK2')}

🎂 Jumlah usia < 20 Tahun (UMR1): {val('UMR1')}  
🧑‍🦱 Jumlah usia 20-30 Tahun (UMR2): {val('UMR2')}  
👨‍👩‍👦 Jumlah usia 31-40 Tahun (UMR3): {val('UMR3')}  
👴 Jumlah usia 41-50 Tahun (UMR4): {val('UMR4')}  
👵 Jumlah usia > 50 Tahun (UMR5): {val('UMR5')}

📚 Tamatan SD/Sederajat (PT1): {val('PT1')}  
🏫 Tamatan SMP/Sederajat (PT2): {val('PT2')}  
🎓 Tamatan SMA/Sederajat (PT3): {val('PT3')}  
🎓🎓 Tamatan Diploma/Sarjana (PT4): {val('PT4')}

📘🔥 Frekuensi Bermain Hampir Setiap Hari (FBJ1): {val('FBJ1')}  
📘 Frekuensi Bermain 2-3 kali/minggu (FBJ2): {val('FBJ2')}  
📗 Frekuensi Bermain 1 kali/minggu (FBJ3): {val('FBJ3')}  
⏳ Frekuensi Bermain <1 kali/minggu (FBJ4): {val('FBJ4')}

🎲 Jenis Judi Togel/Lotere Online (JJ1): {val('JJ1')}  
⚽ Jenis Judi Taruhan Olahraga (JJ2): {val('JJ2')}  
🎰 Jenis Judi Kasino Online (JJ3): {val('JJ3')}  
✔️ Jenis Judi Lainnya (JJ4): {val('JJ4')}

💸 Pengeluaran < Rp 500Rb (PDB1): {val('PDB1')}  
💰 Pengeluaran Rp 500Rb - Rp 2 Jt (PDB2): {val('PDB2')}  
💵 Pengeluaran 2 Jt - 5 Jt (PDB3): {val('PDB3')}  
🏦 Pengeluaran > Rp 5 Jt (PDB4): {val('PDB4')}

❗ Masalah Keuangan YA (MK1): {val('MK1')}  
✅ Masalah Keuangan TIDAK (MK2): {val('MK2')}

👨‍❤️‍👨 Frekuensi Bertengkar Tidak Pernah (FB1): {val('FB1')}  
🫰 Frekuensi Bertengkar Jarang 1-2 Kali/bln (FB2): {val('FB2')}  
💥 Frekuensi Bertengkar Sering 1-2 Kali/bln (FB3): {val('FB3')}  
💣 Frekuensi Bertengkar Hampir Setiap Hari (FB4): {val('FB4')}

🎰❗ Kecanduan Judi Online YA (KJO1): {val('KJO1')}  
✅ Kecanduan Judi Online TIDAK (KJO2): {val('KJO2')}

💔 Perceraian YA (PJO1): {val('PJO1')}  
💖 Perceraian TIDAK (PJO2): {val('PJO2')}

🎰 Kecanduan Bermain Judi Online (ABJ1): {val('ABJ1')}  
❗ Masalah Keuangan dalam Pernikahan (ABJ2): {val('ABJ2')}  
🧨 Pertengkaran/Komunikasi yang Buruk (ABJ3): {val('ABJ3')}  
⚠️ Kekerasan dalam Rumah Tangga (ABJ4): {val('ABJ4')}  
🫠 Ketidakjujuran Pasangan akibat Judi (ABJ5): {val('ABJ5')}
"""
# =========================
# HANDLER BOT
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["group_idx"] = 0
    field = GROUPS[0][0]
    await update.message.reply_text(FIELD_PROMPTS[field])
    return ASKING

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    group_idx = context.user_data.get("group_idx", 0)
    group = GROUPS[group_idx]

    # Cek input integer
    if len(group) == 1:
        key = group[0]
        if not is_int_nonneg(text):
            await update.message.reply_text(f"❌ Masukkan angka non-negatif untuk {key}.")
            return ASKING
        context.user_data[key] = int(text)
    else:
        # Multi field
        keys = group
        values = text.split()
        if len(values) != len(keys):
            await update.message.reply_text(f"❌ Masukkan {len(keys)} angka dipisahkan spasi untuk {', '.join(keys)}.")
            return ASKING
        for k, v in zip(keys, values):
            if not is_int_nonneg(v):
                await update.message.reply_text(f"❌ Semua harus angka non-negatif, cek {k}.")
                return ASKING
            context.user_data[k] = int(v)

    # Validasi grup
    valid, msg = validate_group(context.user_data, group_idx)
    if not valid:
        clear_group(context.user_data, group_idx)
        await update.message.reply_text(msg + "\nSilakan input ulang grup ini.")
        return ASKING

    # Lanjut ke grup berikut
    if group_idx + 1 < len(GROUPS):
        context.user_data["group_idx"] = group_idx + 1
        next_group = GROUPS[group_idx + 1]
        if len(next_group) == 1:
            await update.message.reply_text(FIELD_PROMPTS[next_group[0]])
        else:
            await update.message.reply_text(f"Masukkan nilai untuk {', '.join(next_group)} (pisahkan dengan spasi):")
        return ASKING
    else:
        # Semua selesai
        text_rekap = format_rekap_text(context.user_data)
        export_text("rekap_data.txt", text_rekap)
        await update.message.reply_text("✅ Input selesai!\n\n" + text_rekap)
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Input dibatalkan. Gunakan /start untuk mulai ulang.")
    return ConversationHandler.END

# =========================
# APRIORI UTILITY
# =========================
def generate_itemsets(items: List[str], min_support_count: int):
    # 1-itemset
    freq = {}
    for item in items:
        freq[item] = freq.get(item, 0) + 1
    L1 = {frozenset([k]): v for k, v in freq.items() if v >= min_support_count}

    # 2-itemset dan seterusnya
    current_L = L1
    all_L = [current_L]
    k = 2
    while current_L:
        candidates = {}
        items_list = list(current_L.keys())
        for i in range(len(items_list)):
            for j in range(i + 1, len(items_list)):
                union_set = items_list[i] | items_list[j]
                if len(union_set) == k:
                    candidates[union_set] = 0

        # Hitung support
        for t in items:
            tset = frozenset([t])
            for c in candidates:
                if c.issubset(tset):
                    candidates[c] += 1
        # Filter min_support_count
        current_L = {c: cnt for c, cnt in candidates.items() if cnt >= min_support_count}
        if current_L:
            all_L.append(current_L)
        k += 1
    return all_L

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
