CREATE TABLE IF NOT EXISTS "photos" (
	"id"	INTEGER,
	"width"	INTEGER,
	"height"	INTEGER,
	"url"	TEXT,
	"photographer"	TEXT,
	"photographer_url"	TEXT,
	"photographer_id"	INTEGER,
	"avg_color"	TEXT,
	"liked"	INTEGER,
	"alt"	TEXT,
	PRIMARY KEY("id")
);
CREATE INDEX IF NOT EXISTS avg_color_idx ON photos(avg_color COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS "photo_sources" (
	"type"	TEXT,
	"url"	TEXT,
	"photo_id"	INTEGER,
	"photo_source_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	FOREIGN KEY("photo_id") REFERENCES "photos"("id")
);
