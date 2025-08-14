SELECT r.*,(MAX(a.age)-MIN(a.age)) AS age_difference
FROM rooms r
JOIN ages a ON r.id=a.room
GROUP BY r.id,r.name
ORDER BY age_difference DESC
LIMIT 5