"""Banking data quality demo. Python 3.10+, standard library only."""
import csv
import json
import sqlite3
from pathlib import Path
from datetime import date, timedelta
from collections import Counter
import html

ROOT = Path(__file__).resolve().parent

def generate():
    source = []
    for i in range(1, 1001):
        source.append((f"T{i:04}", f"A{i%100:03}", str(date(2026,1,1)+timedelta(days=i%90)),
                       ("branch","mobile","web")[i%3], 1000 + (i*7919)%99000))
    ledger = list(source)
    # Deliberate upstream quality failures and downstream reconciliation breaks.
    source[9] = (*source[9][:1], "", *source[9][2:])
    source[19] = (*source[19][:4], -100)
    source[29] = (*source[29][:2], "2026-02-30", *source[29][3:])
    source[39] = (*source[39][:3], "unknown", source[39][4])
    source.append(source[0])
    ledger = [r for r in ledger if r[0] != "T0050"]
    ledger[59] = (*ledger[59][:4], ledger[59][4]+500)
    ledger.append(("EXTRA","A001","2026-01-02","web",7500))
    return source, ledger

def validate(rows):
    counts = Counter(r[0] for r in rows)
    clean, exceptions = [], []
    for n, row in enumerate(rows, 1):
        tid, account, day, channel, cents = row
        rules = []
        if not tid or counts[tid] > 1: rules.append("duplicate_or_missing_id")
        if not account: rules.append("missing_account")
        try: date.fromisoformat(day)
        except (ValueError, TypeError): rules.append("invalid_date")
        if channel not in {"branch","mobile","web"}: rules.append("invalid_channel")
        if type(cents) is not int or cents <= 0: rules.append("invalid_amount")
        if rules:
            exceptions.extend((n,tid,rule) for rule in rules)
        else: clean.append(row)
    return clean, exceptions

def write_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer=csv.writer(f); writer.writerow(headers); writer.writerows(rows)

def reconcile(db):
    # Two-sided key reconciliation; missing values stay NULL, never zero.
    return db.execute("""
    SELECT s.transaction_id, 'missing_in_ledger', s.amount_cents, NULL
    FROM clean_source s LEFT JOIN ledger l USING(transaction_id)
    WHERE l.transaction_id IS NULL
    UNION ALL
    SELECT l.transaction_id, 'missing_in_clean_source', NULL, l.amount_cents
    FROM ledger l LEFT JOIN clean_source s USING(transaction_id)
    WHERE s.transaction_id IS NULL
    UNION ALL
    SELECT s.transaction_id, 'amount_mismatch', s.amount_cents, l.amount_cents
    FROM clean_source s JOIN ledger l USING(transaction_id)
    WHERE s.amount_cents != l.amount_cents
    ORDER BY 1
    """).fetchall()

def run(output=None):
    out=Path(output) if output else ROOT/"reports"
    out.mkdir(parents=True,exist_ok=True)
    source, ledger=generate()
    clean, exceptions=validate(source)
    with sqlite3.connect(":memory:") as db:
        for table, rows in (("raw_source",source),("clean_source",clean),("ledger",ledger)):
            db.execute(f"CREATE TABLE {table} (transaction_id TEXT, account_id TEXT, transaction_date TEXT, channel TEXT, amount_cents INTEGER)")
            db.executemany(f"INSERT INTO {table} VALUES (?,?,?,?,?)",rows)
        breaks=reconcile(db)
        channels=db.execute("SELECT channel,COUNT(*),SUM(amount_cents) FROM clean_source GROUP BY channel ORDER BY channel").fetchall()
        # SQL control totals must agree with Python integer totals.
        assert db.execute("SELECT SUM(amount_cents) FROM clean_source").fetchone()[0]==sum(r[4] for r in clean)
    metrics={"raw_rows":len(source),"accepted_rows":len(clean),
             "quarantined_rows":len(source)-len(clean),
             "row_acceptance_pct":round(100*len(clean)/len(source),2),
             "reconciliation_breaks":len(breaks),
             "accepted_amount_cents":sum(r[4] for r in clean)}
    write_csv(out/"exceptions.csv",["source_row","transaction_id","rule"],exceptions)
    write_csv(out/"reconciliation.csv",["transaction_id","reason","source_cents","ledger_cents"],breaks)
    write_csv(out/"channel_kpis.csv",["channel","transactions","amount_cents"],channels)
    write_csv(out/"source.csv",["transaction_id","account_id","transaction_date","channel","amount_cents"],source)
    write_csv(out/"ledger.csv",["transaction_id","account_id","transaction_date","channel","amount_cents"],ledger)
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    cards="".join(f"<article><strong>{v:,}</strong><span>{html.escape(k.replace('_',' '))}</span></article>" for k,v in metrics.items())
    bars="".join(f"<p>{c}: {n} transactions · USD {amt/100:,.2f}</p><meter min='0' max='{len(clean)}' value='{n}'></meter>" for c,n,amt in channels)
    rows="".join("<tr>"+"".join(f"<td>{html.escape(str(x)) if x is not None else '—'}</td>" for x in row)+"</tr>" for row in breaks)
    page="""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Banking Data Quality Monitor</title><style>
    body{font:16px system-ui;background:#0b1525;color:#e5edf6;margin:0;padding:5vw;max-width:1200px}
    h1{font-size:clamp(30px,5vw,52px)}p{color:#b5c8df}section{display:flex;flex-wrap:wrap;gap:16px}
    article{background:#182b43;padding:24px;border-radius:14px;min-width:200px;flex:1}strong{display:block;font-size:30px;color:#67e8c3}
    span{display:block;margin-top:12px}table{border-collapse:collapse;width:100%;background:#182b43}td,th{padding:12px;border-bottom:1px solid #35506c;text-align:left}
    meter{width:100%;height:24px}a{color:#67e8c3}.scroll{overflow-x:auto}</style>
    <p>AKSHITHA THAKUR · ANALYTICS PORTFOLIO</p><h1>Banking Data Quality Monitor</h1>
    <p>Synthetic USD transaction data · January–March 2026 · Demonstration only</p><section>"""
    page+=cards+"</section><h2>Accepted transactions by channel</h2>"+bars
    page+="<h2>Reconciliation exceptions</h2><p>Amounts below are integer cents. A missing value is not a zero balance.</p><div class='scroll'><table><tr><th>Transaction</th><th>Reason</th><th>Source cents</th><th>Ledger cents</th></tr>"+rows+"</table></div>"
    page+="<p>Acceptance measures validation coverage, not verified financial accuracy. Quarantined source records may produce downstream reconciliation exceptions.</p></html>"
    (out/"dashboard.html").write_text(page,encoding="utf-8")
    print(json.dumps(metrics,indent=2))
    return metrics

if __name__=="__main__": run()
