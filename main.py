import os
import csv
import glob
import zipfile
import re
import datetime
from itertools import combinations
from typing import List, Tuple, Dict

import pandas as pd
import matplotlib.pyplot as plt

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# =========================
# KONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8038423070:AAGMen0EKwhi1Up3rkWKGghg-Jf_cxgM1DI"
MIN_SUPPORT = 0.30

# =========================
# STATE Conversational
# =========================
ASKING = 1
SEARCH_LOG = 2

# =========================
# URUTAN INPUT & LABELS
# =========================
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
# UTIL: file export
# =========================
def export_rows_to_csv(filename: str, header: List[str], rows: List[List[str]]):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

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
    except Exception:
        return False

def validate_group(data: Dict[str, int], group_idx: int) -> Tuple[bool, str]:
    """Validasi setelah 1 kelompok selesai diisi.
       - Semua kelompok kecuali ABJ: sum == TOTAL
       - ABJ: sum == PJO1
    """
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

    # ABJ should equal PJO1
    if group == GROUPS[-1]:
        pjo1 = data.get("PJO1", None)
        if pjo1 is None:
            return False, "PJO1 belum diisi. Lengkapi grup PJO dulu."
        if s != pjo1:
            return False, f"❌ ABJ1..ABJ5 harus = PJO1 ({pjo1}), sekarang = {s}."
        return True, ""

    # PJO must equal TOTAL
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
# REKAP FORMAT
# =========================
def format_rekap_text(d: Dict[str, int]) -> str:
    val = lambda k: d.get(k, 0)
    return f"""📋 Berikut rekap data yang telah kamu input:

📊 Total keseluruhan data yang dianalisis: {val('TOTAL')}

👩 Jumlah Perempuan (JK1): {val('JK1')}  
👨 Jumlah Laki-Laki (JK2): {val('JK2')}

🎂 Jumlah usia < 20 Tahun (UMR1): {val('UMR1')}  
🧑‍💼 Jumlah usia 20-30 Tahun (UMR2): {val('UMR2')}  
👨‍👩‍👧‍👦 Jumlah usia 31-40 Tahun (UMR3): {val('UMR3')}  
👴 Jumlah usia 41-50 Tahun (UMR4): {val('UMR4')}  
👵 Jumlah usia > 50 Tahun (UMR5): {val('UMR5')}

📚 Tamatan SD/Sederajat (PT1): {val('PT1')}  
🏫 Tamatan SMP/Sederajat (PT2): {val('PT2')}  
🎓 Tamatan SMA/Sederajat (PT3): {val('PT3')}  
🎓🎓 Tamatan Diploma/Sarjana (PT4): {val('PT4')}

📅🔥 Frekuensi Bermain Hampir Setiap Hari (FBJ1): {val('FBJ1')}  
📅 Frekuensi Bermain 2-3 kali/minggu (FBJ2): {val('FBJ2')}  
📆 Frekuensi Bermain 1 kali/minggu (FBJ3): {val('FBJ3')}  
⏳ Frekuensi Bermain <1 kali/minggu (FBJ4): {val('FBJ4')}

🎲 Jenis Judi Togel/Lotere Online (JJ1): {val('JJ1')}  
⚽ Jenis Judi Taruhan Olahraga (JJ2): {val('JJ2')}  
🃏 Jenis Judi Kasino Online (JJ3): {val('JJ3')}  
❓ Jenis Judi Lainnya (JJ4): {val('JJ4')}

💸 Pengeluaran < Rp 500Rb (PDB1): {val('PDB1')}  
💰 Pengeluaran Rp 500Rb - Rp 2 Jt (PDB2): {val('PDB2')}  
💵 Pengeluaran 2 Jt - 5 Jt (PDB3): {val('PDB3')}  
🏦 Pengeluaran > Rp 5 Jt (PDB4): {val('PDB4')}

❗ Masalah Keuangan YA (MK1): {val('MK1')}  
✔️ Masalah Keuangan TIDAK (MK2): {val('MK2')}

🙅‍♂️ Frekuensi Bertengkar Tidak Pernah (FB1): {val('FB1')}  
🤏 Frekuensi Bertengkar Jarang 1-2 Kali/bln (FB2): {val('FB2')}  
🔥 Frekuensi Bertengkar Sering 1-2 Kali/bln (FB3): {val('FB3')}  
💥 Frekuensi Bertengkar Hampir Setiap Hari (FB4): {val('FB4')}

🎰❗ Kecanduan Judi Online YA (KJO1): {val('KJO1')}  
✔️ Kecanduan Judi Online TIDAK (KJO2): {val('KJO2')}

💔 Perceraian YA (PJO1): {val('PJO1')}  
💖 Perceraian TIDAK (PJO2): {val('PJO2')}

🎰 Kecanduan Bermain Judi Online (ABJ1): {val('ABJ1')}  
❗ Masalah Keuangan dalam Pernikahan (ABJ2): {val('ABJ2')}  
🗣️ Pertengkaran/Komunikasi yang Buruk (ABJ3): {val('ABJ3')}  
⚠️ Kekerasan dalam Rumah Tangga (ABJ4): {val('ABJ4')}  
🤥 Ketidakjujuran Pasangan akibat Judi (ABJ5): {val('ABJ5')}
"""

def rekap_rows_csv(d: Dict[str, int]) -> List[List[str]]:
    order = [
        "TOTAL",
        "JK1", "JK2",
        "UMR1", "UMR2", "UMR3", "UMR4", "UMR5",
        "PT1", "PT2", "PT3", "PT4",
        "FBJ1", "FBJ2", "FBJ3", "FBJ4",
        "JJ1", "JJ2", "JJ3", "JJ4",
        "PDB1", "PDB2", "PDB3", "PDB4",
        "MK1", "MK2",
        "FB1", "FB2", "FB3", "FB4",
        "KJO1", "KJO2",
        "PJO1", "PJO2",
        "ABJ1", "ABJ2", "ABJ3", "ABJ4", "ABJ5",
    ]
    rows = []
    for k in order:
        label = ITEM_LABELS.get(k, k) if k != "TOTAL" else "📊 TOTAL"
        rows.append([label, str(d.get(k, 0))])
    return rows

# =========================
# APRIORI
# =========================
def one_itemset(data: Dict[str, int]) -> List[Tuple[Tuple[str, ...], int, float, bool]]:
    total = data.get("TOTAL", 0)
    items = [(k, v) for k, v in data.items() if k != "TOTAL"]
    out = []
    for k, v in items:
        support = (v / total) if total > 0 else 0.0
        out.append(((k,), v, support, support >= MIN_SUPPORT))
    return out


def k_itemset_from_candidates(
    data: Dict[str, int],
    candidates: List[Tuple[str, ...]]
) -> List[Tuple[Tuple[str, ...], int, float, bool]]:
    total = data.get("TOTAL", 0)
    out = []
    for combo in candidates:
        # Proxy co-occurrence: ambil minimum count antar item
        freq = min(data.get(c, 0) for c in combo)
        support = (freq / total) if total > 0 else 0.0
        out.append((combo, freq, support, support >= MIN_SUPPORT))
    return out


def apriori_generate_candidates(prev_frequents: List[Tuple[str, ...]], k: int) -> List[Tuple[str, ...]]:
    prev_sorted = [tuple(sorted(x)) for x in prev_frequents]
    prev_sorted = sorted(set(prev_sorted))
    candidates = set()
    for i in range(len(prev_sorted)):
        for j in range(i + 1, len(prev_sorted)):
            a, b = prev_sorted[i], prev_sorted[j]
            if a[:k - 2] == b[:k - 2]:
                new = tuple(sorted(set(a).union(b)))
                if len(new) == k:
                    # pruning: semua subset (k-1) harus frequent
                    all_subfreq = True
                    for sub in combinations(new, k - 1):
                        if tuple(sorted(sub)) not in prev_sorted:
                            all_subfreq = False
                            break
                    if all_subfreq:
                        candidates.add(new)
    return sorted(candidates)


def apriori_to_rows(
    data: Dict[str, int],
    k: int
) -> Tuple[List[List[str]], List[Tuple[str, ...]]]:
    if k == 1:
        result = one_itemset(data)
    else:
        prev_rows, prev_freq = apriori_to_rows(data, k - 1)
        candidates = apriori_generate_candidates(prev_freq, k)
        result = k_itemset_from_candidates(data, candidates)

    rows = []
    frequents = []
    total = data.get("TOTAL", 0)

    for combo, freq, support, is_freq in result:
        labels = " + ".join(ITEM_LABELS[c] for c in combo)
        rows.append([labels, f"{freq}/{total} = {support:.2f}", "YES" if is_freq else "NO"])
        if is_freq:
            frequents.append(combo)

    return rows, frequents

# =========================
# KEYBOARDS
# =========================
def main_menu_keyboard():
    total = get_total_from_csv() or 0
    keyboard = [
        [
            InlineKeyboardButton("📥 Input Data", callback_data="input"),
            InlineKeyboardButton(f"📊 Rekap (Total: {total})", callback_data="rekap"),
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
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="main_menu")]])

# =========================
# HELPERS
# =========================
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


def get_total_from_csv() -> int:
    try:
        if not os.path.exists("rekap.csv"):
            return 0
        df = pd.read_csv("rekap.csv")
        # cari baris TOTAL
        total_row = df[df["Item"].str.contains("TOTAL", na=False)]
        if not total_row.empty:
            return int(total_row.iloc[0]["Jumlah"]) if str(total_row.iloc[0]["Jumlah"]).isdigit() else 0
        return 0
    except Exception:
        return 0

# =========================
# HANDLERS: START / RESET
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Bot siap. Gunakan menu di bawah ini:",
        reply_markup=main_menu_keyboard(),
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🔄 Data di memori sesi kamu sudah direset. Klik 📥 Input Data untuk mulai lagi.",
        reply_markup=main_menu_keyboard(),
    )

# =========================
# HANDLERS: INPUT FLOW
# =========================
async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["idx"] = 0
    context.user_data["data"] = {}
    fields = _all_fields_linear()
    first_field = fields[0]
    await update.message.reply_text(
        "📝 Mulai input data responden.\nKetik angka (bilangan bulat ≥ 0).",
        reply_markup=back_to_menu_keyboard(),
    )
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

    # grup positioning
    cumulative = 0
    for gi, g in enumerate(GROUPS):
        if idx < cumulative + len(g):
            group_idx = gi
            in_group_pos = idx - cumulative
            group_len = len(g)
            break
        cumulative += len(g)

    # validasi jika akhir grup
    if in_group_pos == group_len - 1:
        ok, msg = validate_group(context.user_data["data"], group_idx)
        if not ok:
            clear_group(context.user_data["data"], group_idx)
            context.user_data["idx"] = group_start_index(group_idx)
            await update.message.reply_text(msg)
            first_key = GROUPS[group_idx][0]
            await update.message.reply_text(
                f"🔁 Ulangi pengisian grup: {', '.join(GROUPS[group_idx])}"
            )
            await update.message.reply_text(FIELD_PROMPTS[first_key])
            return ASKING

    # lanjut field berikutnya
    idx += 1
    context.user_data["idx"] = idx

    if idx >= len(fields):
        context.user_data["validated"] = True
        await update.message.reply_text(
            "✅ Input selesai & valid! Gunakan 📊 Rekap di menu.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    next_key = fields[idx]
    await update.message.reply_text(FIELD_PROMPTS[next_key])
    return ASKING


async def input_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Dibatalkan.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

# =========================
# HANDLERS: REKAP & APRIORI
# =========================
async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = ensure_validated_data(context)

    # validasi semua grup (kecuali TOTAL)
    for gi in range(len(GROUPS)):
        ok, msg = validate_group(d, gi)
        if not ok and GROUPS[gi] != ("TOTAL",):
            await update.message.reply_text(
                "⚠️ Data belum valid. Jalankan 📥 Input untuk melengkapi.",
                reply_markup=main_menu_keyboard(),
            )
            return

    # Teks rekap
    text = format_rekap_text(d)
    await update.message.reply_text(text)

    # File TXT
    export_text("rekap.txt", text)
    await update.message.reply_document(open("rekap.txt", "rb"))

    # CSV
    rows = rekap_rows_csv(d)
    export_rows_to_csv("rekap.csv", ["Item", "Jumlah"], rows)
    await update.message.reply_document(open("rekap.csv", "rb"))

    # XLSX
    try:
        df = pd.DataFrame(rows, columns=["Item", "Jumlah"])
        df.to_excel("rekap.xlsx", index=False)
        await update.message.reply_document(open("rekap.xlsx", "rb"))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal membuat Excel: {e}")


def build_apriori_output_title(k: int) -> str:
    return f"📊 Hasil Perhitungan {k}-Itemset (Support ≥ {int(MIN_SUPPORT*100)}%)"


async def apriori_generic(update: Update, context: ContextTypes.DEFAULT_TYPE, k: int):
    d = ensure_validated_data(context)

    for gi in range(len(GROUPS)):
        ok, msg = validate_group(d, gi)
        if not ok and GROUPS[gi] != ("TOTAL",):
            await update.message.reply_text(
                "⚠️ Data belum valid. Jalankan 📥 Input untuk melengkapi.",
                reply_markup=main_menu_keyboard(),
            )
            return

    title = build_apriori_output_title(k)
    rows, frequents = apriori_to_rows(d, k)

    preview = "\n".join([f"{r[0]} → {r[1]} ({r[2]})" for r in rows[:30]]) or "Tidak ada kombinasi."
    await update.message.reply_text(f"{title}\n\n{preview}\n\n(Detail lengkap dikirim sebagai file CSV & TXT.)")

    fname = f"apriori{k}"
    export_rows_to_csv(fname + ".csv", ["Itemset", "Support", "Valid"], rows)
    await update.message.reply_document(open(fname + ".csv", "rb"))
    export_text(fname + ".txt", "\n".join([f"{r[0]} | {r[1]} | {r[2]}" for r in rows]))
    await update.message.reply_document(open(fname + ".txt", "rb"))


async def apriori1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await apriori_generic(update, context, 1)


async def apriori2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await apriori_generic(update, context, 2)


async def apriori3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await apriori_generic(update, context, 3)

# =========================
# BACKUP / RESTORE / LOG MENU (Callback Query)
# =========================

def create_backup_zip() -> str:
    zip_filename = "backup.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        if os.path.exists("backup"):
            for file in os.listdir("backup"):
                path = os.path.join("backup", file)
                if os.path.isfile(path):
                    zipf.write(path, arcname=file)
    return zip_filename


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # ==== NAV MAIN MENU ====
    if query.data == "main_menu":
        await query.edit_message_text("🏠 Menu utama:", reply_markup=main_menu_keyboard())
        return

    # ==== INPUT ====
    if query.data == "input":
        # mulai input via pesan baru agar ConversationHandler terpicu
        await query.message.reply_text("📝 Mulai input data.")
        return await input_start(update, context)

    # ==== REKAP ====
    if query.data == "rekap":
        await rekap(update, context)
        return

    # ==== RESET (hanya memory session) ====
    if query.data == "reset":
        context.user_data.clear()
        await query.edit_message_text(
            "🔄 Data sesi direset. Silakan 📥 Input lagi.",
            reply_markup=main_menu_keyboard(),
        )
        return

    # ==== DOWNLOAD BACKUP ====
    if query.data == "download_backup":
        if not os.path.exists("backup") or len(os.listdir("backup")) == 0:
            await query.edit_message_text("⚠️ Belum ada file backup.", reply_markup=main_menu_keyboard())
        else:
            zip_file = create_backup_zip()
            await query.message.reply_document(document=open(zip_file, "rb"))
            await query.edit_message_text("📦 Semua backup berhasil dikompres & dikirim.", reply_markup=main_menu_keyboard())
        return

    # ==== DELETE BACKUP (confirm) ====
    if query.data == "delete_backup":
        if not os.path.exists("backup") or len(os.listdir("backup")) == 0:
            await query.edit_message_text("⚠️ Tidak ada file backup yang bisa dihapus.", reply_markup=main_menu_keyboard())
        else:
            keyboard = [[
                InlineKeyboardButton("✅ Ya, Hapus", callback_data="confirm_delete_backup"),
                InlineKeyboardButton("❌ Batal", callback_data="main_menu"),
            ]]
            await query.edit_message_text("⚠️ Apakah kamu yakin ingin menghapus **SEMUA backup**?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "confirm_delete_backup":
        if os.path.exists("backup"):
            for file in os.listdir("backup"):
                try:
                    os.remove(os.path.join("backup", file))
                except Exception:
                    pass
        await query.edit_message_text("🗑 Semua file backup berhasil dihapus.", reply_markup=main_menu_keyboard())
        return

    # ==== RESTORE BACKUP ====
    if query.data == "restore_backup":
        if not os.path.exists("backup") or len(os.listdir("backup")) == 0:
            await query.edit_message_text("⚠️ Tidak ada file backup yang tersedia untuk di-restore.", reply_markup=main_menu_keyboard())
        else:
            files = sorted(
                [f for f in os.listdir("backup") if f.endswith(".xlsx")],
                key=lambda x: os.path.getmtime(os.path.join("backup", x)),
                reverse=True,
            )[:5]
            keyboard = [[InlineKeyboardButton(file, callback_data=f"restore_file|{file}")] for file in files]
            keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="main_menu")])
            await query.edit_message_text("♻️ Pilih file backup yang ingin di-restore:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data.startswith("restore_file|"):
        file_name = query.data.split("|")[1]
        file_path = os.path.join("backup", file_name)
        try:
            df = pd.read_excel(file_path)
            df.to_csv("rekap.csv", index=False)
            df.to_excel("rekap.xlsx", index=False)

            # log restore
            user = query.from_user
            username = f"@{user.username}" if user.username else user.full_name
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("restore_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"[{timestamp}] {username} (ID:{user.id}) restore {file_name}\n")

            await query.edit_message_text(
                f"✅ Backup `{file_name}` berhasil di-restore.\n📝 Restore tercatat di `restore_log.txt`.",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Gagal restore backup: {e}", reply_markup=main_menu_keyboard())
        return

    # ==== VIEW RESTORE LOG ====
    if query.data == "view_restore_log":
        if not os.path.exists("restore_log.txt"):
            await query.edit_message_text("📜 Belum ada aktivitas restore yang tercatat.", reply_markup=main_menu_keyboard())
        else:
            with open("restore_log.txt", "r", encoding="utf-8") as f:
                logs = f.read().strip() or "📜 Log masih kosong."
            if len(logs) > 3500:
                await query.message.reply_document(document=open("restore_log.txt", "rb"), filename="restore_log.txt")
                await query.edit_message_text("📜 Log restore terlalu panjang, dikirim sebagai file.", reply_markup=main_menu_keyboard())
            else:
                await query.edit_message_text(f"📜 Log Restore:\n\n{logs}", reply_markup=main_menu_keyboard())
        return

    # ==== CLEAR RESTORE LOG (confirm + backup) ====
    if query.data == "clear_restore_log":
        if not os.path.exists("restore_log.txt") or os.stat("restore_log.txt").st_size == 0:
            await query.edit_message_text("📜 Log restore sudah kosong.", reply_markup=main_menu_keyboard())
        else:
            keyboard = [[
                InlineKeyboardButton("✅ Ya, Hapus Log", callback_data="confirm_clear_restore_log"),
                InlineKeyboardButton("❌ Batal", callback_data="main_menu"),
            ]]
            await query.edit_message_text("⚠️ Apakah kamu yakin ingin menghapus semua isi log restore?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "confirm_clear_restore_log":
        try:
            if os.path.exists("restore_log.txt") and os.stat("restore_log.txt").st_size > 0:
                os.makedirs("backup", exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_log = f"backup/restore_log_{timestamp}.txt"
                with open("restore_log.txt", "r", encoding="utf-8") as f_src, open(backup_log, "w", encoding="utf-8") as f_dest:
                    f_dest.write(f_src.read())
                open("restore_log.txt", "w", encoding="utf-8").close()
                await query.edit_message_text(
                    f"🧹 Log restore berhasil dihapus.\n📂 Salinan log lama tersimpan di `{backup_log}`",
                    reply_markup=main_menu_keyboard(),
                )
            else:
                await query.edit_message_text("📜 Log restore sudah kosong.", reply_markup=main_menu_keyboard())
        except Exception as e:
            await query.edit_message_text(f"❌ Gagal menghapus log: {e}", reply_markup=main_menu_keyboard())
        return

    # ==== SEARCH RESTORE LOG (enter state) ====
    if query.data == "search_restore_log":
        if not os.path.exists("restore_log.txt") or os.stat("restore_log.txt").st_size == 0:
            await query.edit_message_text("📜 Log restore masih kosong, tidak bisa dicari.", reply_markup=main_menu_keyboard())
        else:
            await query.edit_message_text(
                "🔍 Kirim kata kunci yang ingin dicari di log restore.\n\nContoh:\n- `@username`\n- `2025-08-20`\n- `rekap_20250820`",
            )
            context.user_data["awaiting_search"] = True
        return

    # ==== FILTER DATE LIST ====
    if query.data == "filter_date_log":
        if not os.path.exists("restore_log.txt") or os.stat("restore_log.txt").st_size == 0:
            await query.edit_message_text("📜 Log restore masih kosong, tidak ada tanggal untuk difilter.", reply_markup=main_menu_keyboard())
        else:
            with open("restore_log.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
            dates = sorted({line[1:11] for line in lines if line.startswith("[")}, reverse=True)
            latest_dates = dates[:5]
            keyboard = [[InlineKeyboardButton(date, callback_data=f"filter_date|{date}")] for date in latest_dates]
            keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="main_menu")])
            await query.edit_message_text("📅 Pilih tanggal log restore yang ingin dilihat:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data.startswith("filter_date|"):
        selected_date = query.data.split("|")[1]
        with open("restore_log.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        results = [line for line in lines if line.startswith(f"[{selected_date}")]
        if not results:
            await query.edit_message_text(f"❌ Tidak ada aktivitas restore pada tanggal {selected_date}.", reply_markup=main_menu_keyboard())
        else:
            output = "".join(results[:10])
            if len(results) > 10:
                with open("filter_result.txt", "w", encoding="utf-8") as f_out:
                    f_out.writelines(results)
                await query.message.reply_document(document=open("filter_result.txt", "rb"), filename=f"restore_log_{selected_date}.txt")
                await query.edit_message_text(
                    f"📅 Ditemukan {len(results)} log pada tanggal {selected_date}.\n📂 Semua hasil dikirim sebagai file.",
                    reply_markup=main_menu_keyboard(),
                )
            else:
                await query.edit_message_text(
                    f"📅 Ditemukan {len(results)} log pada tanggal {selected_date}:\n\n{output}",
                    reply_markup=main_menu_keyboard(),
                )
        return

    # ==== CHART: RESTORE PER DAY ====
    if query.data == "chart_restore_log":
        if not os.path.exists("restore_log.txt") or os.stat("restore_log.txt").st_size == 0:
            await query.edit_message_text("📜 Log restore masih kosong, grafik tidak bisa dibuat.", reply_markup=main_menu_keyboard())
        else:
            with open("restore_log.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
            dates = [line[1:11] for line in lines if line.startswith("[")]
            if not dates:
                await query.edit_message_text("📜 Tidak ada data tanggal valid di log restore.", reply_markup=main_menu_keyboard())
                return
            from collections import Counter
            count_per_day = Counter(dates)
            sorted_dates = sorted(count_per_day.keys())
            counts = [count_per_day[d] for d in sorted_dates]
            plt.figure(figsize=(8, 4))
            plt.plot(sorted_dates, counts, marker="o")
            plt.xticks(rotation=45, ha="right")
            plt.title("📊 Jumlah Restore per Hari")
            plt.xlabel("Tanggal")
            plt.ylabel("Jumlah Restore")
            plt.tight_layout()
            plt.savefig("restore_chart.png")
            plt.close()
            await query.message.reply_photo(photo=open("restore_chart.png", "rb"), caption="📊 Grafik jumlah restore per hari")
            await query.edit_message_text("✅ Grafik restore log berhasil dibuat.", reply_markup=main_menu_keyboard())
        return

    # ==== CHART: RESTORE PER USER ====
    if query.data == "chart_user_restore":
        if not os.path.exists("restore_log.txt") or os.stat("restore_log.txt").st_size == 0:
            await query.edit_message_text("📜 Log restore masih kosong, grafik tidak bisa dibuat.", reply_markup=main_menu_keyboard())
        else:
            with open("restore_log.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
            users = []
            for line in lines:
                m = re.search(r"\] (.+?) \(ID:(\d+)\)", line)
                if m:
                    name = m.group(1)
                    user_id = m.group(2)
                    users.append(f"{name}\n(ID:{user_id})")
            if not users:
                await query.edit_message_text("📜 Tidak ada data user valid di log restore.", reply_markup=main_menu_keyboard())
                return
            from collections import Counter
            count_per_user = Counter(users)
            top_users = count_per_user.most_common(5)
            labels = [u for u, _ in top_users]
            counts = [c for _, c in top_users]
            plt.figure(figsize=(8, 4))
            plt.barh(labels, counts)
            plt.xlabel("Jumlah Restore")
            plt.ylabel("User")
            plt.title("👤 Top 5 User Restore")
            plt.tight_layout()
            plt.savefig("restore_user_chart.png")
            plt.close()
            await query.message.reply_photo(photo=open("restore_user_chart.png", "rb"), caption="👤 Grafik Top 5 User Restore")
            await query.edit_message_text("✅ Grafik restore per user berhasil dibuat.", reply_markup=main_menu_keyboard())
        return

    # ==== EXPORT RESTORE STATS EXCEL ====
    if query.data == "export_restore_excel":
        if not os.path.exists("restore_log.txt") or os.stat("restore_log.txt").st_size == 0:
            await query.edit_message_text("📜 Log restore masih kosong, tidak ada data untuk diekspor.", reply_markup=main_menu_keyboard())
        else:
            with open("restore_log.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
            dates = [line[1:11] for line in lines if line.startswith("[")]
            from collections import Counter
            per_day = Counter(dates)
            users = []
            for line in lines:
                m = re.search(r"\] (.+?) \(ID:(\d+)\)", line)
                if m:
                    name = m.group(1)
                    user_id = m.group(2)
                    users.append(f"{name} (ID:{user_id})")
            per_user = Counter(users)
            df_day = pd.DataFrame(per_day.items(), columns=["Tanggal", "Jumlah Restore"]).sort_values("Tanggal")
            df_user = pd.DataFrame(per_user.items(), columns=["User", "Jumlah Restore"]).sort_values("Jumlah Restore", ascending=False)
            with pd.ExcelWriter("restore_stats.xlsx", engine="openpyxl") as writer:
                df_day.to_excel(writer, sheet_name="PerHari", index=False)
                df_user.to_excel(writer, sheet_name="PerUser", index=False)
            await query.message.reply_document(document=open("restore_stats.xlsx", "rb"), filename="restore_stats.xlsx", caption="📂 Statistik restore berhasil diekspor ke Excel.")
            await query.edit_message_text("✅ Export statistik restore ke Excel selesai.", reply_markup=main_menu_keyboard())
        return

# =========================
# SEARCH LOG FREE-TEXT (Message after pressing search)
# =========================
async def search_log_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_search"):
        return ConversationHandler.END

    keyword = update.message.text.strip()
    if not os.path.exists("restore_log.txt"):
        await update.message.reply_text("📜 Log restore tidak ditemukan.", reply_markup=main_menu_keyboard())
        context.user_data.pop("awaiting_search", None)
        return ConversationHandler.END

    with open("restore_log.txt", "r", encoding="utf-8") as f:
        logs = f.readlines()

    results = [line for line in logs if keyword.lower() in line.lower()]

    if not results:
        await update.message.reply_text(f"❌ Tidak ada hasil yang cocok untuk: `{keyword}`", reply_markup=main_menu_keyboard())
    else:
        output = "".join(results[:10])
        if len(results) > 10:
            with open("search_result.txt", "w", encoding="utf-8") as f_out:
                f_out.writelines(results)
            await update.message.reply_document(document=open("search_result.txt", "rb"), filename="search_result.txt")
            await update.message.reply_text(
                f"🔍 Ditemukan {len(results)} hasil untuk `{keyword}`.\n📂 Semua hasil dikirim sebagai file.",
                reply_markup=main_menu_keyboard(),
            )
        else:
            await update.message.reply_text(
                f"🔍 Ditemukan {len(results)} hasil untuk `{keyword}`:\n\n{output}",
                reply_markup=main_menu_keyboard(),
            )
    context.user_data.pop("awaiting_search", None)
    return ConversationHandler.END

# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation for /input (text-based)
    conv_input = ConversationHandler(
        entry_points=[CommandHandler("input", input_start)],
        states={
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_ask)],
        },
        fallbacks=[CommandHandler("cancel", input_cancel)],
        name="input_conversation",
        persistent=False,
    )

    # Conversation for search log (triggered after pressing the button)
    conv_search = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, search_log_input)],
        states={
            SEARCH_LOG: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_log_input)],
        },
        fallbacks=[],
        name="search_log_conversation",
        persistent=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))

    # Keep legacy commands for power users
    app.add_handler(conv_input)
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(CommandHandler("apriori1", apriori1))
    app.add_handler(CommandHandler("apriori2", apriori2))
    app.add_handler(CommandHandler("apriori3", apriori3))

    # Callback buttons (menu + backup/restore/log features)
    app.add_handler(CallbackQueryHandler(button_handler))

    # Search listener (after pressing search button, next text is captured)
    app.add_handler(conv_search)

    app.run_polling()


if __name__ == "__main__":
    main()
