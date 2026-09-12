SELECT max_capacity - (
    SELECT COUNT(*) 
    FROM BOOKING 
    WHERE CLASS_SESSION_id = CLASS_SESSION.id
        AND status = 'ENROLLED') AS available_spots
FROM CLASS_SESSION
WHERE CLASS_SESSION.id = ?