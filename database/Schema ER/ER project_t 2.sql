/* Tables */
CREATE TABLE USER (
    email TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('manager', 'student')) NOT NULL,
    PRIMARY KEY (email)
);
CREATE TABLE COOKING_CLASS (
    id INTEGER NOT NULL,
    cuisine TEXT NOT NULL,
    title TEXT NOT NULL,
    duration INTEGER NOT NULL,
    difficulty TEXT CHECK(difficulty IN ('Beginner', 'Intermediate', 'Advanced')) NOT NULL,
    chef_name TEXT NOT NULL,
    description TEXT NOT NULL,
    dietary_category TEXT CHECK(dietary_category IN ('Standard', 'Vegetarian', 'Vegan', 'Gluten-free')) NOT NULL,
    photo_1 TEXT NOT NULL,
    photo_2 TEXT NOT NULL,
    photo_3 TEXT NOT NULL,
    USER_email TEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (USER_email) REFERENCES USER (email) ON DELETE CASCADE
);
CREATE TABLE CLASS_SESSION (
    id INTEGER NOT NULL,
    max_capacity INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    day_of_week TEXT NOT NULL,
    kitchen TEXT NOT NULL,
    COOKING_CLASS_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (COOKING_CLASS_id) REFERENCES COOKING_CLASS (id) ON DELETE CASCADE
);
CREATE TABLE BOOKING (
    id INTEGER NOT NULL,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5) NOT NULL,
    status TEXT CHECK(status IN ('ENROLLED', 'WAITING')) NOT NULL,
    CLASS_SESSION_id INTEGER NOT NULL,
    USER_email TEXT NOT NULL,
    UNIQUE(CLASS_SESSION_id, USER_email),
    PRIMARY KEY (id),
    FOREIGN KEY (CLASS_SESSION_id) REFERENCES CLASS_SESSION (id) ON DELETE CASCADE,
    FOREIGN KEY (USER_email) REFERENCES USER (email) ON DELETE CASCADE
);
CREATE TABLE INGREDITENT (
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    COOKING_CLASS_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (COOKING_CLASS_id) REFERENCES COOKING_CLASS (id) ON DELETE CASCADE
);