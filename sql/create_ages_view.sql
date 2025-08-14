CREATE MATERIALIZED VIEW IF NOT EXISTS ages AS
(
    SELECT s.*,
    (CURRENT_DATE-s.birthday)/365 AS age
    FROM students s
)