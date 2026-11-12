-- scenarios/sql/checks.sql

-- name: zip_not_5_digits
SELECT account_id, zip_code
FROM applications
WHERE NOT regexp_full_match(zip_code, '[0-9]{5}');

-- name: phone_bad_format
SELECT account_id, phone
FROM applications
WHERE NOT regexp_full_match(phone, '\(\d{3}\) \d{3}-\d{4}');

-- name: duplicate_account_id
SELECT account_id, COUNT(*) AS occurrences
FROM applications
GROUP BY account_id
HAVING COUNT(*) > 1;

-- name: applications_by_profile
SELECT group_profile, is_fraud::BOOLEAN AS is_fraud,
       COUNT(DISTINCT group_id) AS groups, COUNT(*) AS applications
FROM labels
GROUP BY ALL
ORDER BY ALL;

-- name: fraud_rate
SELECT AVG(is_fraud::BOOLEAN::INTEGER) AS fraud_rate, COUNT(*) AS applications
FROM labels;

-- name: address_sharing_by_label
WITH address_counts AS (
    SELECT account_id,
           COUNT(*) OVER (PARTITION BY address, city, state, zip_code, latitude, longitude)
               AS applications_at_address
    FROM applications
)
SELECT l.is_fraud::BOOLEAN AS is_fraud,
       AVG((c.applications_at_address > 1)::INTEGER) AS share_sharing_full_address
FROM address_counts AS c
JOIN labels AS l USING (account_id)
GROUP BY ALL
ORDER BY ALL;

-- name: fraud_rate_outside_range
SELECT r.fraud_rate
FROM (SELECT AVG(is_fraud::BOOLEAN::INTEGER) AS fraud_rate FROM labels) AS r
CROSS JOIN params AS p
WHERE r.fraud_rate < p.fraud_rate_min OR r.fraud_rate > p.fraud_rate_max;
