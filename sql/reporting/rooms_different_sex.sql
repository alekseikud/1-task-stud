SELECT * FROM
(
    SELECT r.name,s.room,
    COUNT(
        CASE WHEN sex='M' THEN 1
        END
    ) AS male_count,
    COUNT(
        CASE WHEN sex='F' THEN 1
        END
    ) AS female_count
    FROM rooms r
    JOIN students s
    ON r.id=s.room
    GROUP BY r.name,s.room
)
WHERE male_count>0 AND female_count>0