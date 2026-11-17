import tempfile
import unittest
import sqlite3
from pathlib import Path
from pipeline import generate, validate, reconcile, run

class Controls(unittest.TestCase):
    def test_quarantines_all_duplicate_occurrences(self):
        row=("T1","A1","2026-01-01","web",100)
        clean, errors=validate([row,row])
        self.assertEqual(clean,[])
        self.assertEqual(len(errors),2)

    def test_rejects_invalid_calendar_date_and_zero(self):
        clean, errors=validate([("T1","A1","2026-02-30","web",0)])
        self.assertEqual(clean,[])
        self.assertEqual({e[2] for e in errors},{"invalid_date","invalid_amount"})

    def test_known_population_controls(self):
        source,ledger=generate()
        clean,errors=validate(source)
        self.assertEqual((len(source),len(clean),len(errors)),(1001,995,6))
        self.assertEqual(len(ledger),1000)
        self.assertEqual(len({r[0] for r in clean}),995)

    def test_two_sided_reconciliation(self):
        with sqlite3.connect(":memory:") as db:
            for table in ("clean_source","ledger"):
                db.execute(f"CREATE TABLE {table}(transaction_id TEXT,amount_cents INTEGER)")
            db.executemany("INSERT INTO clean_source VALUES (?,?)",[("same",100),("different",100),("source_only",200)])
            db.executemany("INSERT INTO ledger VALUES (?,?)",[("same",100),("different",101),("ledger_only",300)])
            rows=reconcile(db)
            self.assertEqual(len(rows),3)
            self.assertEqual({r[1] for r in rows},{"missing_in_ledger","missing_in_clean_source","amount_mismatch"})

    def test_end_to_end_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            metrics=run(tmp)
            self.assertEqual(metrics["reconciliation_breaks"],8)
            self.assertEqual(metrics["quarantined_rows"],6)
            self.assertEqual(metrics["row_acceptance_pct"],99.4)
            self.assertTrue((Path(tmp)/"dashboard.html").exists())
            self.assertEqual(len(list(Path(tmp).glob("*.csv"))),5)

if __name__=="__main__": unittest.main()
