SELECT r.*,COUNT(*)
FROM rooms r
JOIN students s ON r.id=s.room
GROUP BY r.id,r.name
ORDER BY count DESC