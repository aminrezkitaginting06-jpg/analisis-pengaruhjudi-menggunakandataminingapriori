import os
import csv
import logging
from itertools import combinations
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MIN_SUPPORT = 0.3

# ------------------- Logging -------------------
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename="bot.log"
)

# ------------------- Struktur & Labels -------------------
GROUPS = [
    ("TOTAL",),
    ("JK1","JK2"), ("UMR1","UMR2","UMR3","UMR4","UMR5"), ("PT1","PT2","PT3","PT4"),
    ("FBJ1","FBJ2","FBJ3","FBJ4"), ("JJ1","JJ2","JJ3","JJ4"), ("PDB1","PDB2","PDB3","PDB4"),
    ("MK1","MK2"), ("FB1","FB2","FB3","FB4"), ("KJO1","KJO2"), ("PJO1","PJO2"),
    ("ABJ1","ABJ2","ABJ3","ABJ4","ABJ5")
]

ITEM_LABELS = {
    "JK1":"👩 JK1","JK2":"👨 JK2","UMR1":"🎂 UMR1","UMR2":"🧑‍💼 UMR2","UMR3":"👨‍👩‍👧‍👦 UMR3",
    "UMR4":"👴 UMR4","UMR5":"👵 UMR5","PT1":"📚 PT1","PT2":"🏫 PT2","PT3":"🎓 PT3","PT4":"🎓🎓 PT4",
    "FBJ1":"📅🔥 FBJ1","FBJ2":"📅 FBJ2","FBJ3":"📆 FBJ3","FBJ4":"⏳ FBJ4","JJ1":"🎲 JJ1","JJ2":"⚽ JJ2",
    "JJ3":"🃏 JJ3","JJ4":"❓ JJ4","PDB1":"💸 PDB1","PDB2":"💰 PDB2","PDB3":"💵 PDB3","PDB4":"🏦 PDB4",
    "MK1":"❗ MK1","MK2":"✔️ MK2","FB1":"🙅‍♂️ FB1","FB2":"🤏 FB2","FB3":"🔥 FB3","FB4":"💥 FB4",
    "KJO1":"🎰❗ KJO1","KJO2":"✔️ KJO2","PJO1":"💔 PJO1","PJO2":"💖 PJO2","ABJ1":"🎰 ABJ1",
    "ABJ2":"❗ ABJ2","ABJ3":"🗣️ ABJ3","ABJ4":"⚠️ ABJ4","ABJ5":"🤥 ABJ5"
}

FIELD_PROMPTS = {k:f"Masukkan jumlah untuk {ITEM_LABELS.get(k,k)}:" for g in GROUPS for k in g}

ASKING = 1

# ------------------- UTIL -------------------
def is_int_nonneg(text: str) -> bool:
    try: return int(text) >=0
    except: return False

def clear_group(user_data: dict, group_idx: int):
    for k in GROUPS[group_idx]: user_data.pop(k,None)

def _all_fields_linear(): return [k for g in GROUPS for k in g]

def ensure_validated_data(context: ContextTypes.DEFAULT_TYPE):
    d = {k:0 for g in GROUPS for k in g}
    if "data" in context.user_data: d.update(context.user_data["data"])
    return d

def save_data_csv(d: dict, filename="data.csv"):
    with open(filename,"w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f)
        writer.writerow(["Item","Jumlah"])
        for k in _all_fields_linear():
            writer.writerow([ITEM_LABELS.get(k,k),d.get(k,0)])
    logging.info("Data user disimpan ke data.csv")

def format_rekap_text(d: dict):
    text = f"📋 Rekap Data:\n\n📊 Total: {d.get('TOTAL',0)}\n\n"
    for g in GROUPS[1:]:
        for k in g: text+=f"{ITEM_LABELS.get(k,k)}: {d.get(k,0)}\n"
        text+="\n"
    return text

def one_itemset(data: dict):
    total = data["TOTAL"]
    out=[]
    for k,v in data.items():
        if k=="TOTAL": continue
        s=v/total if total>0 else 0
        out.append(((k,),v,s,s>=MIN_SUPPORT))
    return out

def k_itemset_from_candidates(data:dict,candidates):
    total=data["TOTAL"]
    out=[]
    for combo in candidates:
        freq=min(data[c] for c in combo)
        s=freq/total if total>0 else 0
        out.append((combo,freq,s,s>=MIN_SUPPORT))
    return out

def apriori_generate_candidates(prev_frequents,k):
    prev_sorted=[tuple(sorted(x)) for x in prev_frequents]
    prev_sorted=sorted(set(prev_sorted))
    candidates=set()
    for i in range(len(prev_sorted)):
        for j in range(i+1,len(prev_sorted)):
            a,b=prev_sorted[i],prev_sorted[j]
            if a[:k-2]==b[:k-2]:
                new=tuple(sorted(set(a).union(b)))
                if len(new)==k:
                    ok=True
                    for sub in combinations(new,k-1):
                        if tuple(sorted(sub)) not in prev_sorted: ok=False;break
                    if ok: candidates.add(new)
    return sorted(candidates)

def apriori_to_rows(data,k):
    if k==1: result=one_itemset(data)
    else:
        prev_rows,prev_freq=apriori_to_rows(data,k-1)
        candidates=apriori_generate_candidates(prev_freq,k)
        result=k_itemset_from_candidates(data,candidates)
    rows=[]
    frequents=[]
    total=data["TOTAL"]
    for combo,freq,sup,is_freq in result:
        labels=" + ".join(ITEM_LABELS[c] for c in combo)
        rows.append([labels,f"{freq}/{total}={sup:.2f}","YES" if is_freq else "NO"])
        if is_freq: frequents.append(combo)
    return rows,frequents

def save_apriori_csv(rows,k):
    fname=f"apriori{k}.csv"
    with open(fname,"w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f)
        writer.writerow(["Itemset","Support","Valid"])
        writer.writerows(rows)
    logging.info(f"{k}-Itemset disimpan ke {fname}")

# ------------------- HANDLERS -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Bot siap.\n/input → input data\n/rekap → rekap data\n/apriori1 → 1-itemset\n"
        "/apriori2 → 2-itemset\n/apriori3 → 3-itemset\n/reset → reset data"
    )
    logging.info("User started bot")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("♻️ Data berhasil direset")
    logging.info("User reset data")

async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["data"]={}
    context.user_data["field_idx"]=0
    field=_all_fields_linear()[0]
    await update.message.reply_text(FIELD_PROMPTS[field])
    return ASKING

async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=update.message.text.strip()
    idx=context.user_data.get("field_idx",0)
    field=_all_fields_linear()[idx]
    if not is_int_nonneg(text):
        await update.message.reply_text("❌ Harus angka positif. Coba lagi:")
        return ASKING
    context.user_data["data"][field]=int(text)
    idx+=1
    if idx>=len(_all_fields_linear()):
        await update.message.reply_text("✅ Semua data berhasil diinput!")
        save_data_csv(context.user_data["data"])
        return ConversationHandler.END
    context.user_data["field_idx"]=idx
    await update.message.reply_text(FIELD_PROMPTS[_all_fields_linear()[idx]])
    return ASKING

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d=ensure_validated_data(context)
    txt=format_rekap_text(d)
    await update.message.reply_text(txt)
    save_data_csv(d)

async def apriori_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, k:int=1):
    d=ensure_validated_data(context)
    rows,_=apriori_to_rows(d,k)
    txt=f"📊 {k}-Itemset (Support ≥ {MIN_SUPPORT:.0%})\n"
    for r in rows: txt+=f"{r[0]} → {r[1]} ({r[2]})\n"
    await update.message.reply_text(txt)
    save_apriori_csv(rows,k)

async def apriori1(update,context): return await apriori_handler(update,context,1)
async def apriori2(update,context): return await apriori_handler(update,context,2)
async def apriori3(update,context): return await apriori_handler(update,context,3)

# ------------------- MAIN -------------------
def main():
    app=Application.builder().token(BOT_TOKEN).build()
    conv=ConversationHandler(
        entry_points=[CommandHandler("input",input_start)],
        states={ASKING:[MessageHandler(filters.TEXT & ~filters.COMMAND,input_handler)]},
        fallbacks=[CommandHandler("reset",reset)]
    )
    app.add_handler(CommandHandler("start",start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("rekap",rekap))
    app.add_handler(CommandHandler("apriori1",apriori1))
    app.add_handler(CommandHandler("apriori2",apriori2))
    app.add_handler(CommandHandler("apriori3",apriori3))
    app.add_handler(CommandHandler("reset",reset))
    app.run_polling()

if __name__=="__main__":
    main()
