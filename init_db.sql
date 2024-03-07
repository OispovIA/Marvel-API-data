CREATE TABLE IF NOT EXISTS marvel_characters (
    character_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    comics_appeared_in INT
);
