INSERT INTO COOKING_CLASS (title, cuisine, duration, difficulty, chef_name, description, dietary_category, photo_1, photo_2, photo_3, USER_email)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);

INSERT INTO INGREDIENT (name, COOKING_CLASS_id)
VALUES (?, ?);