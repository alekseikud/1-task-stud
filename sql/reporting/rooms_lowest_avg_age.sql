        SELECT r.id,r.name,AVG(a.age) AS average_age
        FROM ages a
        JOIN rooms r
        ON a.room=r.id
        GROUP BY r.id,r.name
        ORDER BY average_age
        LIMIT 5