DROP TABLE IF EXISTS rooms CASCADE;
CREATE TABLE rooms
(
	id INT PRIMARY KEY,
	name TEXT NOT NULL
);

DROP TABLE IF EXISTS students ;
CREATE TABLE students
(
	id INT PRIMARY KEY,
	birthday DATE,
	name TEXT NOT NULL,
	room int NOT NULL,
	sex VARCHAR(1),
	CONSTRAINT fk_room
		FOREIGN KEY (room)
			REFERENCES rooms(id)
);