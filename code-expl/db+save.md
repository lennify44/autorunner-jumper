runs — eine Zeile pro Durchlauf, die Rahmendaten.

offset ist AUDIO OFFSET

presses — eine Zeile pro Tastendruck. Das ist die eigentliche Messung.

t_press ist der Rohwert: Spielzeit des Drucks. Keine Abweichung, keine Differenz — die rechnest du später. effective sagt, ob sprung in luft oder vom boden aus war

obstacles — eine Zeile pro Hindernis, mit seiner Sollzeit und ob es getroffen wurde.



CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    participant TEXT,
    offset_s    REAL,
    seed        INTEGER,
    bpm         INTEGER,
    started_at  TEXT,
    hits        INTEGER
);
CREATE TABLE IF NOT EXISTS presses (
    run_id    INTEGER,
    t_press   REAL,
    effective INTEGER
);
CREATE TABLE IF NOT EXISTS obstacles (
    run_id    INTEGER,
    idx       INTEGER,
    beat_time REAL,
    hit       INTEGER



def save_run():
conn, cursor = connect()
cursor.execute(
    """INSERT INTO runs (participant, offset_s, seed, bpm, started_at, hits)
       VALUES (?, ?, ?, ?, ?, ?)""",
    (participant_id, AUDIO_OFFSET, LEVEL_SEED, BPM,
     datetime.now().isoformat(timespec="seconds"), hits)
)
run_id = cursor.lastrowid
cursor.executemany(
    "INSERT INTO presses (run_id, t_press, effective) VALUES (?, ?, ?)",
    [(run_id, tp, int(eff)) for tp, eff in presses]
)
cursor.executemany(
    "INSERT INTO obstacles (run_id, idx, beat_time, hit) VALUES (?, ?, ?, ?)",
    [(run_id, i, bt, int(i in hit_obstacles)) for i, bt in enumerate(obstacle_times)]
)
conn.commit()
conn.close()

Eine List Comprehension ist nur eine Kurzschreibweise für eine Schleife mit append

Die zwei Hälften

[(run_id, tp, int(eff)) for tp, eff in presses]
 └──── was gebaut wird ────┘ └── woher die Werte kommen ──┘

Beim Lesen fängst du rechts an:

1. for tp, eff in presses — geh die Liste presses durch
2. (run_id, tp, int(eff)) — bau für jedes Element dieses Tupel und leg es in die neue Liste

Die eckigen Klammern außen sagen: „das Ergebnis ist eine Liste". Genau wie [] eine leere Liste ist.

Identisch zur langen Form:

zeilen = []
for tp, eff in presses:
    zeilen.append((run_id, tp, int(eff)))

Das ist buchstäblich derselbe Code — die Demo oben vergleicht beide Ergebnisse und sie sind gleich.

Das Entpacken im for-Teil

Das ist wahrscheinlich der verwirrende Punkt. Zwei Namen hinter for:

for tp, eff in presses:

presses enthält Paare wie (4.03, True). Schreibst du einen Namen, bekommst du das ganze Paar:

p = (4.03, True)   ->  p[0]=4.03  p[1]=True

Schreibst du zwei, teilt Python das Paar automatisch auf:

tp=4.03  eff=True

Das heißt Tupel-Entpacken und funktioniert überall, nicht nur in Schleifen. WIDTH, HEIGHT = 960, 540 ganz oben in deiner Datei ist dasselbe Prinzip, und conn, cursor = connect() auch.



p = (4.03, True)   ->  p[0]=4.03  p[1]=True

Schreibst du zwei, teilt Python das Paar automatisch auf:

Die obstacles-Zeile

Schreibst du zwei, teilt Python das Paar automatisch auf:

tp=4.03  eff=True

Das heißt Tupel-Entpacken und funktioniert überall, nicht nur in Schleifen. WIDTH, HEIGHT = 960, 540 ganz oben in deiner Datei ist dasselbe Prinzip, und conn, cursor = connect() auch.

Die obstacles-Zeile

[(run_id, i, bt, int(i in hit_obstacles)) for i, bt in enumerate(obstacle_times)]

enumerate liefert Index und Wert, die zwei Namen fangen beide auf:

i=0  bt=8.0    i in hit_obstacles -> False
i=1  bt=10.0   i in hit_obstacles -> True
i=2  bt=11.0   i in hit_obstacles -> False
i=3  bt=13.0   i in hit_obstacles -> True

i in hit_obstacles ist die Mengenabfrage, die du in der Kollisionsprüfung schon benutzt — hier nur als Wert statt als Bedingung. Sie ergibt True/False, int() macht 1/0 daraus.
