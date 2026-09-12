SELECT COUNT(*) AS position
FROM BOOKING
WHERE CLASS_SESSION_id = ?
    AND status = 'WAITING'
    AND id <= (
        SELECT id
        FROM BOOKING
        WHERE CLASS_SESSION_id = ?
            AND USER_email = ?
    )