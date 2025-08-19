import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

# ===================== KONFIG BOT =====================
TOKEN = "ISI_TOKEN_BOTMU_DI_SINI"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===================== KODE-KODE RESMI (sesuai tabel) =====================
ALL_CODES = [
    # Tabel III.2 Jenis Kelamin
    "JK1","JK2",
    # Tabel III.3 Rentang Usia
    "UMR1","UMR2","UMR3","UMR4","UMR5",
    # Tabel III.4 Pendidikan
    "PT1","PT2","PT3","PT4",
    # Tabel III.5 Frekuensi bermain
    "FBJ1","FBJ2","FBJ3","FBJ4",
    # Tabel III.6 Durasi
    "DB1","DB2","DB3","DB4",
    # Tabel III.7 Jenis judi
    "JJ1","JJ2","JJ3","JJ4",
    # Tabel III.8 Pengeluaran
    "PDB1","PDB2","PDB3","PDB4",
    # Tabel III.9 Masalah keuangan
    "MK1","MK2",
    # Tabel III.10 Frek. bertengkar
    "FB1","FB2","FB3","FB4",
    # Tabel III.11 Kecanduan
    "KJO1","KJO2",
    # Tabel III.12 Pengaruh ke Perceraian
    "PJO1","PJO2",
    # Tabel III.13 Alasan Bercerai (opsional bila PJO1)
    "ABJ1","ABJ2","ABJ3","ABJ4","ABJ5"
]

# Label deskriptif (untuk interpretasi & nasehat)
LABELS = {
    "JK1":"Perempuan", "JK2":"Laki-laki",
    "UMR1":"<20 th", "UMR2":"20–30 th", "UMR3":"31–40 th", "UMR4":"41–50 th", "UMR5":">50 th",
    "PT1":"SD/sederajat","PT2":"SMP/sederajat","PT3":"SMA/sederajat","PT4":"Diploma/Sarjana",
    "FBJ1":"Main hampir tiap hari","FBJ2":"Main 2–3x/minggu","FBJ3":"Main 1x/minggu","FBJ4":"<1x/minggu",
    "DB1":"<30 menit/sesi","DB2":"30–60 menit","DB3":"1–2 jam","DB4":">2 jam",
    "JJ1":"Togel/Lotere","JJ2":"Taruhan Olahraga","JJ3":"Kasino Online","JJ4":"Lainnya",
    "PDB1":"< Rp500rb","PDB2":"Rp500rb–2jt","PDB3":">2–5jt","PDB4":"> Rp5jt",
    "MK1":"Ada masalah keuangan","MK2":"Tidak ada masalah keuangan",
    "FB1":"Tidak pernah bertengkar","FB2":"Jarang (1–2x/bln)","FB3":"Sering (1–2x/mgg)","FB4":"Hampir setiap hari",
    "KJO1":"Kecanduan judi","KJO2":"Tidak kecanduan",
    "PJO1":"Cerai karena judi","PJO2":"Tidak bercerai",
    "ABJ1":"Alasan cerai: Kecanduan judi",
    "ABJ2":"Alasan cerai: Masalah keuangan",
    "ABJ3":"Alasan cerai: Pertengkaran/komunikasi buruk",
    "ABJ4":"Alasan cerai: KDRT",
    "ABJ5":"Alasan cerai: Ketidakjujuran pasangan"
}

# Mapping saran moral per topik/alasan
MORAL_ADVICE = {
    "Judi": "🚫 Hindari perilaku berjudi karena terbukti meningkatkan risiko perceraian. Cari bantuan konseling keuangan atau dukungan keluarga.",
    "Ekonomi": "💰 Perbaiki manajemen keuangan rumah tangga, buat anggaran bersama, dan komunikasikan masalah ekonomi secara terbuka.",
    "Pertengkaran": "🗣️ Perbanyak komunikasi sehat, selesaikan konflik dengan musyawarah, atau pertimbangkan konseling pernikahan.",
    "KDRT": "⚠️ Segera cari bantuan hukum atau lembaga perlindungan. KDRT adalah tindak pidana dan sangat berbahaya bagi keselamatan keluarga.",
    "Ketidakjujuran": "🤥 Bangun kembali kepercayaan dengan bersikap jujur dan terbuka. Kebohongan kecil bisa merusak fondasi rumah tangga.",
    # fallback
    "_default": "🙏 Udahlah, jangan teruskan kebiasaan buruk. Tobatlah. Sayangi dirimu dan orang-orang yang kamu cintai."
}

# Deteksi topik dari consequents/ABJ*
def topic_from_codes(codes: set[str]) -> str:
    # Prioritas: ABJ* (alasan cerai spesifik)
    if "ABJ1" in codes: return "Judi"
    if "ABJ2" in codes: return "Ekonomi"
    if "ABJ3" in codes: return "Pertengkaran"
    if "ABJ4" in codes: return "KDRT"
    if "ABJ5" in codes: return "Ketidakjujuran"
    # fallback dari indikator umum
    if "KJO1" in codes: return "Judi"
    if "MK1"  in codes: return "Ekonomi"
    if "FB3" in codes or "FB4" in codes: return "Pertengkaran"
    return ""

def codes_to_text(codes: set[str]) -> str:
    return ", ".join(LABELS.get(c, c) for c in codes)

# ===================== UTIL: PARSE INPUT =====================
def parse_user_block(text: str) -> pd.DataFrame:
    """
    Terima blok teks, tiap baris = 1 responden, berisi kode-kode dipisah koma.
    Contoh baris: 'JK2, UMR2, PT3, FBJ1, DB3, JJ1, PDB2, MK1, FB3, KJO1, PJO1, ABJ2'
    Return: DataFrame biner (one-hot) dengan kolom ALL_CODES.
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    rows = []
    for ln in lines:
        parts = [p.strip().upper() for p in ln.split(",") if p.strip()]
        # filter hanya kode valid
        parts = [p for p in parts if p in ALL_CODES]
        row = {code: (code in parts) for code in ALL_CODES}
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=ALL_CODES)

    df = pd.DataFrame(rows)
    # pastikan tipe bool/int (mlxtend butuh 0/1)
    df = df.astype(int)
    return df

# ===================== APRIORI CORE =====================
def run_apriori(df: pd.DataFrame, min_support=0.2, min_conf=0.5):
    if df.empty:
        return None, None

    # Frequent itemsets
    fi = apriori(df, min_support=min_support, use_colnames=True)
    if fi.empty:
        return fi, pd.DataFrame()

    # Aturan asosiasi
    rules = association_rules(fi, metric="confidence", min_threshold=min_conf)
    if rules.empty:
        return fi, rules

    # Urutkan aturan: lift desc lalu confidence desc
    rules = rules.sort_values(by=["lift", "confidence", "support"], ascending=False).reset_index(drop=True)
    return fi, rules

# ===================== FORMAT OUTPUT =====================
def format_supports(fi: pd.DataFrame, limit=10) -> str:
    # tampilkan itemset 1-item & 2-item paling kuat
    fi = fi.copy()
    fi["len"] = fi["itemsets"].apply(len)
    one = fi[fi["len"] == 1].sort_values("support", ascending=False).head(limit)
    two = fi[fi["len"] == 2].sort_values("support", ascending=False).head(limit)

    lines = []
    if not one.empty:
        lines.append("• **Support 1-itemset (Top):**")
        for _, r in one.iterrows():
            items = codes_to_text(set(r["itemsets"]))
            lines.append(f"   - {items}: **{r['support']*100:.2f}%**")
    if not two.empty:
        lines.append("\n• **Support 2-itemset (Top):**")
        for _, r in two.iterrows():
            items = codes_to_text(set(r["itemsets"]))
            lines.append(f"   - {items}: **{r['support']*100:.2f}%**")

    return "\n".join(lines) if lines else "_(Tidak ada itemset kuat untuk ditampilkan)_"

def format_rules(rules: pd.DataFrame, top_n=5) -> str:
    if rules is None or rules.empty:
        return "_Tidak ada aturan dengan confidence yang memenuhi ambang._"
    lines = ["• **Aturan (Top berdasarkan Lift & Confidence):**"]
    for i, r in rules.head(top_n).iterrows():
        A = codes_to_text(set(r["antecedents"]))
        B = codes_to_text(set(r["consequents"]))
        lines.append(
            f"   - **Jika** {A} **→ Maka** {B} "
            f"(Support: **{r['support']*100:.2f}%**, Confidence: **{r['confidence']*100:.2f}%**, Lift: **{r['lift']:.2f}**)"
        )
    return "\n".join(lines)

def advice_from_rules(rules: pd.DataFrame) -> str:
    """
    Ambil konsekuen/ABJ paling relevan dari aturan top untuk menentukan tema saran moral.
    Jika tidak ketemu, fallback ke dominan berdasarkan kolom ABJ* atau indikator umum.
    """
    # 1) coba ambil tema dari 3 aturan teratas
    if rules is not None and not rules.empty:
        for _, r in rules.head(3).iterrows():
            cons = set(r["consequents"])
            theme = topic_from_codes(cons)
            if theme:
                return MORAL_ADVICE.get(theme, MORAL_ADVICE["_default"])
    # 2) fallback: tidak ada aturan kuat → saran umum
    return MORAL_ADVICE["_default"]

# ===================== TELEGRAM HANDLERS =====================
INTRO = (
    "Halo! 👋\n"
    "Kirim data responden **per baris** berisi kode-kode (dipisah koma) sesuai Tabel III.2–III.13.\n\n"
    "Contoh:\n"
    "`JK2, UMR2, PT3, FBJ1, DB3, JJ1, PDB2, MK1, FB3, KJO1, PJO1, ABJ2`\n\n"
    "Keterangan:\n"
    "- Gunakan **ABJ1..ABJ5 hanya jika PJO1 (cerai)**.\n"
    "- Minimal 10–20 baris agar Apriori bermakna.\n"
    "- Default ambang: min_support=20%, min_confidence=50%.\n\n"
    "Setelah mengirim data, bot akan menampilkan **support, aturan (confidence & lift),** lalu **saran moral** sesuai topik (Judi/Ekonomi/Pertengkaran/KDRT/Ketidakjujuran)."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INTRO, parse_mode="Markdown")

def build_report(text: str, min_support=0.2, min_conf=0.5) -> str:
    df = parse_user_block(text)
    if df.empty:
        return "⚠️ Tidak ada kode valid yang terbaca. Pastikan setiap baris berisi kode-kode seperti `JK2, UMR2, ...`."

    fi, rules = run_apriori(df, min_support=min_support, min_conf=min_conf)

    # Bagian Support
    supports_txt = format_supports(fi) if fi is not None and not fi.empty else "_Tidak ada frequent itemset pada ambang support saat ini._"

    # Bagian Rules
    rules_txt = format_rules(rules, top_n=5)

    # Saran moral
    advice_txt = advice_from_rules(rules)

    # Tambah pesan moral khas
    moral_tail = "\n\n🧭 *Saran Moral Tambahan*: _Udahlah, jangan kau tambah-tambah lagi. Tobatlah. Sayangi dirimu dan orang-orang yang kau sayang._"

    report = (
        "📊 **Hasil Analisis Apriori**\n\n"
        f"{supports_txt}\n\n"
        f"{rules_txt}\n\n"
        f"💡 **Saran sesuai topik**:\n{advice_txt}"
        f"{moral_tail}"
    )
    return report

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        report = build_report(text, min_support=0.2, min_conf=0.5)
        await update.message.reply_text(report, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Error processing text")
        await update.message.reply_text(f"❌ Terjadi kesalahan saat memproses data:\n{e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
