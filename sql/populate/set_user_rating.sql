UPDATE BOOKING
SET rating = ?
WHERE USER_email = ?
    AND CLASS_SESSION_id = ?
    AND rating IS NULL