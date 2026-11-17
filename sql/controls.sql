-- All monetary amounts are integer USD cents. Tables created in pipeline.py.
SELECT 'raw_source' AS population, COUNT(*) AS rows FROM raw_source
UNION ALL SELECT 'clean_source', COUNT(*) FROM clean_source
UNION ALL SELECT 'ledger', COUNT(*) FROM ledger;

SELECT transaction_id, COUNT(*) AS occurrences
FROM raw_source GROUP BY transaction_id HAVING COUNT(*) > 1;

SELECT substr(transaction_date,1,7) AS month, channel,
       COUNT(*) AS transactions, SUM(amount_cents) AS amount_cents
FROM clean_source GROUP BY month, channel ORDER BY month, channel;

SELECT s.transaction_id, s.amount_cents AS source_cents,
       l.amount_cents AS ledger_cents,
       l.amount_cents-s.amount_cents AS difference_cents
FROM clean_source s JOIN ledger l USING(transaction_id)
WHERE s.amount_cents <> l.amount_cents;
