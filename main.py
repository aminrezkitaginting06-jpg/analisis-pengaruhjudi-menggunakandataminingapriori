import os
import csv
from datetime import datetime
from typing import Dict, List, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)

# =========================
# KONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8417540455:AAE4ihl_idjQD-WVifK1U5sIevLoozDCHlM"

CSV_FILE = "rekap_data.csv"

# =========================
# MENU STATES
# =========================
MENU, INPUT_FLOW = range(2)

# =========================
# DEFINISI PROMPT (URUTAN WAJIB)
# =========================
# Key -> Teks prompt (emoji + label persis seperti yang kamu minta)
PROMPTS = [
    ("TOTAL", "📊 Total keseluruhan data yang dianalisis: "),
    ("JK1", "👩 Jumlah Perempuan (JK1): "),
    ("JK2", "👨 Jumlah Laki-Laki (JK2): "),
    ("UMR1", "🎂 Jumlah usia < 20 Tahun (UMR1): "),
    ("UMR2", "🧑‍💼 Jumlah usia 20-30 Tahun (UMR2): "),
    ("UMR3", "👨‍👩‍👧‍👦 Jumlah usia 31-40 Tahun (UMR3): "),
    ("UMR4", "👴 Jumlah usia 41-50 Tahun (UMR4): "),
    ("UMR5", "👵 Jumlah usia > 50 Tahun (UMR5): "),
    ("PT1", "📚 Tamatan SD/Sederajat (PT1): "),
    ("PT2", "🏫 Tamatan SMP/Sederajat (PT2): "),
    ("PT3", "🎓 Tamatan SMA/Sederajat (PT3): "),
    ("PT4", "🎓🎓 Tamatan Diploma/Sarjana (PT4): "),
    ("FBJ1", "📅🔥 Frekuensi Bermain Hampir Setiap Hari (FBJ1): "),
    ("FBJ2", "📅 Frekuensi Bermain 2-3 kali/minggu (FBJ2): "),
    ("FBJ3", "📆 Frekuensi Bermain 1 kali/minggu (FBJ3): "),
    ("FBJ4", "⏳ Frekuensi Bermain <1 kali/minggu (FBJ4): "),
    ("JJ1", "🎲 Jenis Judi Togel/Lotere Online (JJ1): "),
    ("JJ2", "⚽ Jenis Judi Taruhan Olahraga (JJ2): "),
    ("JJ3", "🃏 Jenis Judi Kasino Online (JJ3): "),
    ("JJ4", "❓ Jenis Judi Lainnya (JJ4): "),
    ("PDB1", "💸 Pengeluaran < Rp 500Rb (PDB1): "),
    ("PDB2", "💰 Pengeluaran Rp 500Rb - Rp 2 Jt (PDB2): "),
    ("PDB3", "💵 Pengeluaran 2 Jt - 5 Jt (PDB3): "),
    ("PDB4", "🏦 Pengeluaran > Rp 5 Jt (PDB4): "),
    ("MK1", "❗ Masalah Keuangan YA (MK1): "),
    ("MK2", "✔️ Masalah Keuangan TIDAK (MK2): "),
    ("FB1", "🙅‍♂️ Frekuensi Bertengkar Tidak Pernah (FB1): "),
    ("FB2", "🤏 Frekuensi Bertengkar Jarang 1-2 Kali/bln (FB2): "),
    ("FB3", "🔥 Frekuensi Bertengkar Sering 1-2 Kali/bln (FB3): "),
    ("FB4", "💥 Frekuensi Bertengkar Hampir Setiap Hari (FB4): "),
    ("KJO1", "🎰❗ Kecanduan Judi Online YA (KJO1): "),
    ("KJO2", "✔️ Kecanduan Judi Online TIDAK (KJO2): "),
    ("PJO1", "💔 Perceraian YA (PJO1): "),
    ("PJO2", "💖 Perceraian TIDAK (PJO2): "),
    ("ABJ1", "🎰 Kecanduan Bermain Judi Online (ABJ1): "),
    ("ABJ2", "❗ Masalah Keuangan dalam Pernikahan (ABJ2): "),
    ("ABJ3", "🗣️ Pertengkaran/Komunikasi yang Buruk (ABJ3): "),
    ("ABJ4", "⚠️ Kekerasan dalam Rumah Tangga (ABJ4): "),
    ("ABJ5", "🤥 Ketidakjujuran Pasangan akibat Judi (ABJ5): "),
]
FLOW_KEYS = [k for k, _ in PROMPTS]
PROMPT_MAP = dict(PROMPTS)

# =========================
# DEFINISI KELOMPOK & VALIDASI
# =========================
# group_code, keys, validate: "sum_total" atau "sum_pjo1" atau None
GROUPS: List[Tuple[str, List[str], str]] = [
    ("TOTAL", ["TOTAL"], None),
    ("JK", ["JK1", "JK2"], "sum_total"),
    ("UMR", ["UMR1", "UMR2", "UMR3", "UMR4", "UMR5"], "sum_total"),
    ("PT", ["PT1", "PT2", "PT3", "PT4"], "sum_total"),
    ("FBJ", ["FBJ1", "FBJ2", "FBJ3", "FBJ4"], "sum_total"),
    ("JJ", ["JJ1", "JJ2", "JJ3", "JJ4"], "sum_total"),
    ("PDB", ["PDB1", "PDB2", "PDB3", "PDB4"], "sum_total"),
    ("MK", ["MK1", "MK2"], "sum_total"),
    ("FB", ["FB1", "FB2", "FB3", "FB4"], "sum_total"),
    ("KJO", ["KJO1", "KJO2"], "sum_total"),
    ("PJO", ["PJO1", "PJO2"], "sum_total"),
    ("ABJ", ["ABJ1", "ABJ2", "ABJ3", "ABJ4", "ABJ5"], "sum_pjo1"),
]

# Peta: key -> (group_code, start_index, end_index)
KEY_GROUP_INFO: Dict[str, Tuple[str, int, int]] = {}
cursor = 0
for code, keys, _ in GROUPS:
    start = cursor
    for k in keys:
        KEY_GROUP_INFO[k] = (code, start, start + len(keys) - 1)
        cursor += 1  # penting: bergerak mengikuti FLOW tanpa TOTAL diulang

# =========================
# HELPERS CSV
# =========================
def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header = ["timestamp", "user_id"] + FLOW_KEYS
            writer.writerow(header)

def append_csv(user_id: int, data: Dict[str, int]):
    ensure_csv()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        row = [datetime.utcnow().isoformat(), user_id] + [int(data.get(k, 0)) for k in FLOW_KEYS]
        writer.writerow(row)

# =========================
# UI HELPERS
# =========================
def main_menu_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📝 INPUT", callback_data="input")],
            [InlineKeyboardButton("📊 REKAP", callback_data="rekap")],
            [InlineKeyboardButton("🔄 RESTART", callback_data="restart")],
        ]
    )

def after_valid_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Lihat Rekap", callback_data="rekap")],
            [InlineKeyboardButton("🏠 Kembali ke Menu", callback_data="menu")],
            [InlineKeyboardButton("🔄 Restart", callback_data="restart")],
        ]
    )

# =========================
# START / MENU
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # reset state visual (tidak hapus data yang sudah tersimpan)
    await update.message.reply_text("👋 Selamat datang! Silakan pilih menu:", reply_markup=main_menu_kb())
    return MENU

async def menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "menu":
        await q.edit_message_text("🏠 Menu Utama", reply_markup=main_menu_kb())
        return MENU

    if q.data == "restart":
        # Hapus progres input saat ini
        context.user_data.clear()
        await q.edit_message_text("🔄 Progres input kamu sudah direset.\nPilih menu:", reply_markup=main_menu_kb())
        return MENU

    if q.data == "rekap":
        # Rekap dari data terakhir yang valid di sesi (bukan otomatis saat input)
        if not context.user_data.get("last_valid"):
            await q.edit_message_text("⚠️ Belum ada rekap tersimpan di sesi ini.\nSilakan INPUT terlebih dahulu.", reply_markup=main_menu_kb())
            return MENU

        text = format_rekap(context.user_data["last_valid"])
        await q.edit_message_text(text, reply_markup=main_menu_kb(), disable_web_page_preview=True)
        return MENU

    if q.data == "input":
        # Mulai alur input step-by-step
        context.user_data["answers"] = {}
        context.user_data["pos"] = 0
        await q.edit_message_text("📝 Mode INPUT dimulai.\nMasukkan angka saja (≥ 0).")
        # Kirim prompt pertama
        await q.message.reply_text(PROMPT_MAP[FLOW_KEYS[0]])
        return INPUT_FLOW

    # fallback ke menu
    await q.edit_message_text("Pilih menu:", reply_markup=main_menu_kb())
    return MENU

# =========================
# INPUT FLOW HANDLER
# =========================
async def handle_input_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ Masukkan *angka bulat* (≥ 0). Coba lagi:", parse_mode="Markdown")
        # ulang prompt yang sama
        key = FLOW_KEYS[context.user_data.get("pos", 0)]
        await update.message.reply_text(PROMPT_MAP[key])
        return INPUT_FLOW

    value = int(text)
    pos = context.user_data.get("pos", 0)
    key = FLOW_KEYS[pos]

    # simpan
    answers = context.user_data["answers"]
    answers[key] = value

    # jika TOTAL, validasi sederhana (>=0 saja)
    if key == "TOTAL" and value < 0:
        await update.message.reply_text("⚠️ TOTAL tidak boleh negatif. Ulangi.")
        await update.message.reply_text(PROMPT_MAP["TOTAL"])
        return INPUT_FLOW

    # cek apakah kita di ujung kelompok → validasi kelompok
    group_code, start_idx, end_idx = KEY_GROUP_INFO.get(key, ("", 0, 0))
    if pos == end_idx:
        # Kumpulkan nilai kelompok
        keys_in_group = [FLOW_KEYS[i] for i in range(start_idx, end_idx + 1)]
        if group_code == "TOTAL":
            # tidak ada validasi jumlah untuk TOTAL
            pass
        else:
            valid, msg = validate_group(group_code, keys_in_group, answers)
            if not valid:
                # Hapus jawaban kelompok & mundur ke awal kelompok
                for k in keys_in_group:
                    answers.pop(k, None)
                context.user_data["pos"] = start_idx
                await update.message.reply_text(msg)
                # prompt ulang dari kunci pertama kelompok
                first_key = FLOW_KEYS[start_idx]
                await update.message.reply_text(PROMPT_MAP[first_key])
                return INPUT_FLOW

    # lanjut ke variabel berikutnya atau selesai
    pos += 1
    context.user_data["pos"] = pos

    if pos >= len(FLOW_KEYS):
        # Semua terisi & valid → simpan CSV & tawarkan tombol
        append_csv(update.effective_user.id, answers)
        # simpan rekap terakhir di sesi
        context.user_data["last_valid"] = dict(answers)

        await update.message.reply_text(
            "✅ Semua data valid & sudah disimpan.\nPilih aksi:",
            reply_markup=after_valid_kb()
        )
        return MENU

    # kirim prompt berikutnya
    next_key = FLOW_KEYS[pos]
    await update.message.reply_text(PROMPT_MAP[next_key])
    return INPUT_FLOW

# =========================
# VALIDASI KELOMPOK
# =========================
def validate_group(code: str, keys: List[str], answers: Dict[str, int]) -> Tuple[bool, str]:
    total = answers.get("TOTAL", 0)
    s = sum(int(answers.get(k, 0)) for k in keys)

    if code != "ABJ":
        # semua selain ABJ wajib == TOTAL
        if s != total:
            # contoh pesan: "❌ JK tidak valid (jumlah=120, harus TOTAL=100). Ulangi dari JK1."
            first = keys[0]
            msg = f"❌ {code} tidak valid (jumlah={s}, harus TOTAL={total}).\n🔁 Silakan ulangi mulai dari {first}."
            return False, msg
        return True, ""

    # ABJ: jumlah ABJ1..ABJ5 = PJO1
    pjo1 = int(answers.get("PJO1", 0))
    if s != pjo1:
        msg = f"❌ ABJ tidak valid (jumlah={s}, harus sama dengan PJO1={pjo1}).\n🔁 Silakan ulangi mulai dari {keys[0]}."
        return False, msg

    return True, ""

# =========================
# FORMAT REKAP / OUTPUT
# =========================
def format_rekap(ans: Dict[str, int]) -> str:
    # fungsi bantu sum kelompok
    def sumi(keys): return sum(int(ans.get(k, 0)) for k in keys)
    T = int(ans.get("TOTAL", 0))

    JK = ["JK1", "JK2"]
    UMR = ["UMR1", "UMR2", "UMR3", "UMR4", "UMR5"]
    PT = ["PT1", "PT2", "PT3", "PT4"]
    FBJ = ["FBJ1", "FBJ2", "FBJ3", "FBJ4"]
    JJ = ["JJ1", "JJ2", "JJ3", "JJ4"]
    PDB = ["PDB1", "PDB2", "PDB3", "PDB4"]
    MK = ["MK1", "MK2"]
    FB = ["FB1", "FB2", "FB3", "FB4"]
    KJO = ["KJO1", "KJO2"]
    PJO = ["PJO1", "PJO2"]
    ABJ = ["ABJ1", "ABJ2", "ABJ3", "ABJ4", "ABJ5"]

    sum_JK, sum_UMR, sum_PT = sumi(JK), sumi(UMR), sumi(PT)
    sum_FBJ, sum_JJ, sum_PDB = sumi(FBJ), sumi(JJ), sumi(PDB)
    sum_MK, sum_FB, sum_KJO = sumi(MK), sumi(FB), sumi(KJO)
    sum_PJO, sum_ABJ = sumi(PJO), sumi(ABJ)

    ok = lambda cond: "✅" if cond else "❌"

    lines = []
    lines.append("📊 FINAL DATA REKAP 📊\n")
    lines.append(f"🔢 Total Data : {T}\n")

    # JK
    lines.append(f"👩 JK1 : {ans.get('JK1',0)}")
    lines.append(f"👨 JK2 : {ans.get('JK2',0)}")
    lines.append(f"📌 Total JK = {sum_JK} {ok(sum_JK==T)}\n")

    # UMR
    lines.append(f"🎂 UMR1 : {ans.get('UMR1',0)}")
    lines.append(f"🧑‍💼 UMR2 : {ans.get('UMR2',0)}")
    lines.append(f"👨‍👩‍👧‍👦 UMR3 : {ans.get('UMR3',0)}")
    lines.append(f"👴 UMR4 : {ans.get('UMR4',0)}")
    lines.append(f"🧓 UMR5 : {ans.get('UMR5',0)}")
    lines.append(f"📌 Total UMR = {sum_UMR} {ok(sum_UMR==T)}\n")

    # PT
    lines.append(f"📚 PT1 : {ans.get('PT1',0)}")
    lines.append(f"🏫 PT2 : {ans.get('PT2',0)}")
    lines.append(f"🎓 PT3 : {ans.get('PT3',0)}")
    lines.append(f"🎓🎓 PT4 : {ans.get('PT4',0)}")
    lines.append(f"📌 Total PT = {sum_PT} {ok(sum_PT==T)}\n")

    # FBJ
    lines.append(f"📅🔥 FBJ1 : {ans.get('FBJ1',0)}")
    lines.append(f"📅 FBJ2 : {ans.get('FBJ2',0)}")
    lines.append(f"📆 FBJ3 : {ans.get('FBJ3',0)}")
    lines.append(f"⏳ FBJ4 : {ans.get('FBJ4',0)}")
    lines.append(f"📌 Total FBJ = {sum_FBJ} {ok(sum_FBJ==T)}\n")

    # JJ
    lines.append(f"🎲 JJ1 : {ans.get('JJ1',0)}")
    lines.append(f"⚽ JJ2 : {ans.get('JJ2',0)}")
    lines.append(f"🃏 JJ3 : {ans.get('JJ3',0)}")
    lines.append(f"❓ JJ4 : {ans.get('JJ4',0)}")
    lines.append(f"📌 Total JJ = {sum_JJ} {ok(sum_JJ==T)}\n")

    # PDB
    lines.append(f"💸 PDB1 : {ans.get('PDB1',0)}")
    lines.append(f"💰 PDB2 : {ans.get('PDB2',0)}")
    lines.append(f"💵 PDB3 : {ans.get('PDB3',0)}")
    lines.append(f"🏦 PDB4 : {ans.get('PDB4',0)}")
    lines.append(f"📌 Total PDB = {sum_PDB} {ok(sum_PDB==T)}\n")

    # MK
    lines.append(f"❗ MK1 : {ans.get('MK1',0)}")
    lines.append(f"✔️ MK2 : {ans.get('MK2',0)}")
    lines.append(f"📌 Total MK = {sum_MK} {ok(sum_MK==T)}\n")

    # FB (bertengkar)
    lines.append(f"🙅‍♂️ FB1 : {ans.get('FB1',0)}")
    lines.append(f"🤏 FB2 : {ans.get('FB2',0)}")
    lines.append(f"🔥 FB3 : {ans.get('FB3',0)}")
    lines.append(f"💥 FB4 : {ans.get('FB4',0)}")
    lines.append(f"📌 Total FB = {sum_FB} {ok(sum_FB==T)}\n")

    # KJO
    lines.append(f"🎰❗ KJO1 : {ans.get('KJO1',0)}")
    lines.append(f"✔️ KJO2 : {ans.get('KJO2',0)}")
    lines.append(f"📌 Total KJO = {sum_KJO} {ok(sum_KJO==T)}\n")

    # PJO
    lines.append(f"💔 PJO1 : {ans.get('PJO1',0)}")
    lines.append(f"💖 PJO2 : {ans.get('PJO2',0)}")
    lines.append(f"📌 Total PJO = {sum_PJO} {ok(sum_PJO==T)}\n")

    # ABJ
    lines.append(f"🎰 ABJ1 : {ans.get('ABJ1',0)}")
    lines.append(f"❗ ABJ2 : {ans.get('ABJ2',0)}")
    lines.append(f"🗣️ ABJ3 : {ans.get('ABJ3',0)}")
    lines.append(f"⚠️ ABJ4 : {ans.get('ABJ4',0)}")
    lines.append(f"🤥 ABJ5 : {ans.get('ABJ5',0)}")
    lines.append(f"📌 Total ABJ = PJO1 = {sum_ABJ} {ok(sum_ABJ==int(ans.get('PJO1',0)))}")

    return "\n".join(lines)

# =========================
# MAIN
# =========================
def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(menu_cb, pattern="^(input|rekap|restart|menu)$")],
            INPUT_FLOW: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input_number)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )
    app.add_handler(conv)

    # tombol menu tetap bisa dipakai kapan pun
    app.add_handler(CallbackQueryHandler(menu_cb, pattern="^(input|rekap|restart|menu)$"))

    return app

def main():
    ensure_csv()
    app = build_app()
    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
