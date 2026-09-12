import sqlite3
from pathlib import Path
DB_PATH = Path(__file__).parent / "auto-save.sqlite"
def connect():
    conn=sqlite3.connect(str(DB_PATH))
    cursor=conn.cursor()
    return conn, cursor
#conn, cursor = connect()
#cursor.execute('select * from runs')
#lists=cursor.fetchall()
#for row in lists:
#    print(" {} | {}".format(row[0], row[1]))



def delete():
    cursor.execute("DELETE FROM runs")


conn, cursor = connect()
cursor.executescript('''CREATE TABLE IF NOT EXISTS runs (
run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
participant TEXT,
offset    REAL,
seed        INTEGER,
bpm         INTEGER,
time_started  TEXT,
hits        INTEGER
);

CREATE TABLE IF NOT EXISTS presses (
    run_id    INTEGER,
    t_press   REAL,
    effektiv INTEGER
);

CREATE TABLE IF NOT EXISTS obstacles (
    run_id    INTEGER,
    idx       INTEGER,
    beat_time REAL,
    hit       INTEGER
);''')
conn.commit()
conn.close()