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
MIN_SUPPORT_1_4 = 0.30
MIN_SUPPORT_5 = 0.35
MIN_CONFIDENCE = 0.80

GROUPS = [
    ("TOTAL",),
    ("JK1", "JK2"),
    ("UMR1", "UMR2", "UMR3", "UMR4", "UMR5"),
    ("PT1", "PT2", "PT3", "PT4"),
    ("FBJ1", "FBJ2", "FBJ3", "FBJ4"),
    ("JJ1", "JJ2", "JJ3", "JJ4"),
    ("PDB1", "PDB2", "PDB3", "PDB4"),
    ("KJO1", "KJO2"),
    ("PJO1", "PJO2"),
    ("ABJ1", "ABJ2", "ABJ3", "ABJ4", "ABJ5"),
]

# Emoji + label
ITEM_LABELS = {
    "JK1": "👩 JK1", "JK2": "👨 JK2",
    "UMR1": "🧒 UMR1", "UMR2": "👦 UMR2", "UMR3": "👧 UMR3", "UMR4": "🧑 UMR4", "UMR5": "🧓 UMR5",
    "PT1": "📚 PT1", "PT2": "📖 PT2", "PT3": "🎓 PT3", "PT4": "🎓 PT4",
    "FBJ1": "🎲 FBJ1", "FBJ2": "🎰 FBJ2", "FBJ3": "🃏 FBJ3", "FBJ4": "🎯 FBJ4",
    "JJ1": "🎴 JJ1", "JJ2": "⚽ JJ2", "JJ3": "🎰 JJ3", "JJ4": "🎲 JJ4",
    "PDB1": "💰 PDB1", "PDB2": "💵 PDB2", "PDB3": "💸 PDB3", "PDB4": "🤑 PDB4",
    "MK1": "❌ MK1", "MK2": "✔ MK2",
    "FB1": "🤝 FB1", "FB2": "🗨 FB2", "FB3": "💢 FB3", "FB4": "🔥 FB4",
    "KJO1": "🎰 KJO1", "KJO2": "✔ KJO2",
    "PJO1": "💔 PJO1", "PJO2": "❤️ PJO2",
    "ABJ1": "🎰 ABJ1", "ABJ2": "💸 ABJ2", "ABJ3": "💢 ABJ3", "ABJ4": "⚠ ABJ4", "ABJ5": "🕵 ABJ5",
}

FIELD_PROMPTS = {k: f"{ITEM_LABELS.get(k, k)} ➡ Masukkan nilai (angka ≥0):" for g in GROUPS for k in g}

# STATE
ASKING = 1

# =========================
# UTIL CSV/TXT
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
        return int(text) >= 0
    except:
        return False

def validate_group(data: Dict[str, int], group_idx: int) -> Tuple[bool, str]:
    group = GROUPS[group_idx]
    if group == ("TOTAL",):
        return True, ""
    total = data.get("TOTAL", None)
    if total is None:
        return False, "TOTAL belum diisi"
    vals = [data.get(k) for k in group]
    if any(v is None for v in vals):
        return False, "Ada nilai yang belum diisi di grup ini"
    s = sum(vals)
    # ABJ
    if group == GROUPS[-1]:
        pjo1 = data.get("PJO1")
        if pjo1 is None: return False, "PJO1 belum diisi"
        if s != pjo1: return False, f"❌ ABJ1–ABJ5 harus = PJO1 ({pjo1}), sekarang={s}"
        return True, ""
    # PJO juga total
    if group == GROUPS[8]:
        if s != total: return False, f"❌ PJO1+PJO2 harus = TOTAL ({total}), sekarang={s}"
        return True, ""
    if s != total:
        return False, f"❌ Jumlah {', '.join(group)} harus = TOTAL ({total}), sekarang={s}"
    return True, ""

def clear_group(user_data: dict, group_idx: int):
    for k in GROUPS[group_idx]: user_data.pop(k, None)

def group_start_index(group_idx: int) -> int:
    idx = 0
    for i in range(group_idx):
        idx += len(GROUPS[i])
    return idx

# =========================
# FORMAT REKAP
# =========================
def format_rekap_text(d: Dict[str,int]) -> str:
    text = "📊 Rekap Data:\n\n"
    for g in GROUPS[1:]:
        for k in g:
            text += f"{ITEM_LABELS[k]}: {d.get(k,0)}\n"
    return text

def rekap_rows_csv(d: Dict[str,int]) -> List[List[str]]:
    rows=[]
    for g in GROUPS[1:]:
        for k in g:
            rows.append([ITEM_LABELS[k], str(d.get(k,0))])
    return rows

# =========================
# APRIORI
# =========================
def one_itemset(data: Dict[str,int], min_support: float) -> List[Tuple[Tuple[str,...],int,float]]:
    total=data["TOTAL"]
    items=[(k,v) for k,v in data.items() if k!="TOTAL"]
    out=[]
    for k,v in items:
        s=v/total if total>0 else 0
        if s>=min_support: out.append(((k,),v,s))
    return out

def k_itemset_from_candidates(data: Dict[str,int], candidates: List[Tuple[str,...]], min_support:float):
    total=data["TOTAL"]
    out=[]
    for combo in candidates:
        freq=min(data[c] for c in combo)
        support=freq/total if total>0 else 0
        if support>=min_support: out.append((combo,freq,support))
    return out

def apriori_generate_candidates(prev_frequents: List[Tuple[str,...]], k:int):
    prev_sorted=[tuple(sorted(x)) for x in prev_frequents]
    candidates=set()
    for i in range(len(prev_sorted)):
        for j in range(i+1,len(prev_sorted)):
            a,b=prev_sorted[i],prev_sorted[j]
            if a[:k-2]==b[:k-2]:
                new=tuple(sorted(set(a).union(b)))
                if len(new)==k:
                    all_subfreq=True
                    for sub in combinations(new,k-1):
                        if tuple(sorted(sub)) not in prev_sorted: all_subfreq=False; break
                    if all_subfreq: candidates.add(new)
    return sorted(candidates)

def apriori(data:Dict[str,int], k:int) -> List[Tuple[Tuple[str,...],int,float]]:
    min_support=MIN_SUPPORT_1_4 if k<5 else MIN_SUPPORT_5
    if k==1: return one_itemset(data,min_support)
    prev=apriori(data,k-1)
    prev_freq=[x[0] for x in prev]
    candidates=apriori_generate_candidates(prev_freq,k)
    return k_itemset_from_candidates(data,candidates,min_support)

# =========================
# RULE CONFIDENCE
# =========================
def generate_rules(frequent_itemsets: List[Tuple[Tuple[str,...],int,float]], data:Dict[str,int]) -> List[Tuple[str,str,float,float]]:
    """Hanya untuk 5-itemset ke PJO1 sebagai contoh"""
    rules=[]
    pjo1_count=data["PJO1"]
    for combo,freq,support in frequent_itemsets:
        if "PJO1" in combo: # target
            antecedent=[c for c in combo if c!="PJO1"]
            conf=freq/pjo1_count if pjo1_count>0 else 0
            if conf>=MIN_CONFIDENCE:
                rules.append((" + ".join([ITEM_LABELS[a] for a in antecedent]), ITEM_LABELS["PJO1"], support, conf))
    return rules

# =========================
# HANDLER
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Halo! Perintah:\n/input\n/rekap\n/apriori1\n/apriori2\n/apriori3\n/apriori4\n/apriori5\n/reset")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🗑 Data direset. Ketik /input untuk mulai lagi.")

async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["idx"]=0
    context.user_data["data"]={}
    fields=[k for g in GROUPS for k in g]
    await update.message.reply_text("📝 Mulai input data step-by-step.\nKetik angka ≥0")
    await update.message.reply_text(FIELD_PROMPTS[fields[0]])
    return ASKING

async def input_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=update.message.text.strip()
    if not is_int_nonneg(text):
        await update.message.reply_text("❌ Masukkan angka bulat ≥0!")
        return ASKING
    value=int(text)
    fields=[k for g in GROUPS for k in g]
    idx=context.user_data.get("idx",0)
    key=fields[idx]
    context.user_data["data"][key]=value

    # validasi grup
    cumulative=0
    for gi,g in enumerate(GROUPS):
        if idx<cumulative+len(g):
            group_idx=gi
            in_group_pos=idx-cumulative
            group_len=len(g)
            break
        cumulative+=len(g)

    if in_group_pos==group_len-1:
        ok,msg=validate_group(context.user_data["data"],group_idx)
        if not ok:
            clear_group(context.user_data["data"],group_idx)
            context.user_data["idx"]=group_start_index(group_idx)
            await update.message.reply_text(msg)
            first_key=GROUPS[group_idx][0]
            await update.message.reply_text(FIELD_PROMPTS[first_key])
            return ASKING

    # next
    idx+=1
    context.user_data["idx"]=idx
    if idx>=len(fields):
        await update.message.reply_text("✅ Input selesai. Gunakan /rekap untuk melihat ringkasan")
        return ConversationHandler.END
    next_key=fields[idx]
    await update.message.reply_text(FIELD_PROMPTS[next_key])
    return ASKING

async def input_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan. Ketik /input untuk mulai lagi.")
    return ConversationHandler.END

def ensure_data(context: ContextTypes.DEFAULT_TYPE) -> Dict[str,int]:
    d={k:0 for g in GROUPS for k in g}
    if "data" in context.user_data:
        for k,v in context.user_data["data"].items(): d[k]=v
    return d

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d=ensure_data(context)
    text=format_rekap_text(d)
    await update.message.reply_text(text)
    export_text("rekap.txt",text)
    await update.message.reply_document(open("rekap.txt","rb"))
    rows=rekap_rows_csv(d)
    export_rows_to_csv("rekap.csv",["Item","Jumlah"],rows)
    await update.message.reply_document(open("rekap.csv","rb"))

async def apriori_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, k:int):
    d=ensure_data(context)
    rows=[]
    freq_itemsets=apriori(d,k)
    for combo,freq,support in freq_itemsets:
        rows.append([" + ".join([ITEM_LABELS[c] for c in combo]), f"{freq}/{d['TOTAL']} = {support:.2f}"])
    text="\n".join([f"{r[0]} → {r[1]}" for r in rows[:30]]) or "Tidak ada"
    await update.message.reply_text(f"📊 {k}-Itemset:\n{text}")
    # file
    export_rows_to_csv(f"apriori{k}.csv",["Itemset","Support"],rows)
    export_text(f"apriori{k}.txt","\n".join([f"{r[0]} | {r[1]}" for r in rows]))
    await update.message.reply_document(open(f"apriori{k}.csv","rb"))
    await update.message.reply_document(open(f"apriori{k}.txt","rb"))
    # rules jika k=5
    if k==5:
        rules=generate_rules(freq_itemsets,d)
        text_rules="\n".join([f"Jika {r[0]} → Maka {r[1]} (Support={r[2]:.2f}, Confidence={r[3]:.2f})" for r in rules])
        if text_rules:
            await update.message.reply_text("📊 Rule Mining (Confidence ≥80%):\n"+text_rules)

async def apriori1(update,context): await apriori_handler(update,context,1)
async def apriori2(update,context): await apriori_handler(update,context,2)
async def apriori3(update,context): await apriori_handler(update,context,3)
async def apriori4(update,context): await apriori_handler(update,context,4)
async def apriori5(update,context): await apriori_handler(update,context,5)

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("input", input_start)],
        states={ASKING:[MessageHandler(filters.TEXT&~filters.COMMAND,input_ask)]},
        fallbacks=[CommandHandler("cancel", input_cancel)],
        name="input_conversation", persistent=False
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(conv)
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(CommandHandler("apriori1",apriori1))
    app.add_handler(CommandHandler("apriori2",apriori2))
    app.add_handler(CommandHandler("apriori3",apriori3))
    app.add_handler(CommandHandler("apriori4",apriori4))
    app.add_handler(CommandHandler("apriori5",apriori5))
    app.run_polling()

if __name__=="__main__":
    main()
