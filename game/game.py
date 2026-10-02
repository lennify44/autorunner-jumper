import pygame
import time
import random
from pathlib import Path
import sqlite3
import math
from datetime import datetime
import statistics
#Fenster erstellen

STATE_MENU, STATE_PRACTICE, STATE_BREAK, STATE_RUNNING, STATE_DONE, STATE_CALIBRATE = "menu", "practice", "break", "running", "done", "calibrate"

DEBUG = True

MUTE=False
BLUETOOTH = True
TEXT_COLOR = (235, 235, 240)
DIM_COLOR = (120, 120, 135)
WIDTH, HEIGHT = 960, 540 #genau 1/4 von FHD; passt auf jeden bildschirm
FPS = 120 #zeitliche Auflösung=8,3ms bc length of frame=8,3ms
SCROLL_SPEED = 400 #pixel/sec
BPM = 120
SECONDS_PER_BEAT = 60 / BPM     # 0,5 s bei 120 BPM, eif formatierung
PLAYER_X = 200                  # feste Position der Figur 
GROUND_Y = 380                  # Hoehe des Bodens
PLAYER_SIZE = 40
OBSTACLE_W = 30
OBSTACLE_H = 60
def obst_size(x):
    return (x, GROUND_Y - OBSTACLE_H, OBSTACLE_W, OBSTACLE_H)
LEAD_IN_BEATS = 16               # beats vor dem ersten Hindernis
# N_OBSTACLES = 88         #anzahl obstacle-slots
OFFSETS = [-0.150, -0.100, -0.050, 0.0, 0.050, 0.100, 0.150, 0.200]
PRACTICE_OFFSET = 0.0           # +=später;-=früher;in sec.
JUMP_VELOCITY = 1000           # Startgeschwindigkeit nach oben, Pixel/s
GRAVITY = 4000                # Beschleunigung nach unten, Pixel/s²
JUMP_DURATION = 2 * JUMP_VELOCITY / GRAVITY
LEVEL_SEED = 42
SLOT_BEATS = 1
GAP_CHOICES = [2, 2, 2, 2, 2, 3, 4, 4, 4]
MUSIC_END = 60.0
CALIB_COUNTIN_BEATS = 24               # bis Takt 7, wo der Beat einsetzt
CALIB_TAP_BEATS = 16
MUSIC_PATH = Path(__file__).parent / "game_music.wav"
DB_PATH = Path(__file__).parent / "auto-save.sqlite"
PRACTICE_TIMES = 2 #wie oft practice ist
# berechnet den optimalpunkt zum springen
def jump_lead_calc():
    """wie weit vor der Ankunft gedrückt werden muss."""
    overlap_start = -PLAYER_SIZE / SCROLL_SPEED
    overlap_end = OBSTACLE_W / SCROLL_SPEED
    d = math.sqrt(JUMP_VELOCITY**2 - 2 * GRAVITY * OBSTACLE_H)
    tau_up = (JUMP_VELOCITY - d) / GRAVITY
    tau_down = (JUMP_VELOCITY + d) / GRAVITY
    return -((overlap_start - tau_up) + (overlap_end - tau_down)) / 2

JUMP_DURATION = 2 * JUMP_VELOCITY / GRAVITY
JUMP_LEAD = jump_lead_calc()
     



def lustig():
    """falls den probanten langweilig wird, ist das hier eine challenge fuer hinterher ;)"""
    global WIDTH, SCROLL_SPEED, FPS, JUMP_VELOCITY, OBSTACLE_W, OBSTACLE_H, JUMP_DURATION, JUMP_LEAD, GAP_CHOICES
    WIDTH = 1900
    JUMP_VELOCITY = 1300
    SCROLL_SPEED = 4000
    OBSTACLE_W = 480
    OBSTACLE_H = 120
    FPS = 240
    JUMP_DURATION = 2 * JUMP_VELOCITY / GRAVITY
    JUMP_LEAD = jump_lead_calc()
    GAP_CHOICES = [1, 2, 2, 3]
# lustig()

def start_calib():
    global t0, calib_presses
    calib_presses = []
    music.stop()
    music.play()
    t0 = time.perf_counter()

participant_id = ""
bluetooth_offset = 0
if BLUETOOTH:
    bluetooth_offset=-0.2
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512) # bereitet die einstellungen vor; muss vor init() weil der die fest macht
rng = random.Random(LEVEL_SEED)          #Level
pygame.init() #startet die untersysteme
title_font = pygame.font.SysFont(None, 64) # Font size von Menu
font = pygame.font.SysFont(None, 32)
screen=pygame.display.set_mode((WIDTH, HEIGHT)) #erstellt bild(auch alleine). var ist für verweis auf objekt. setmode braucht tupel, desshalb doppelte klammern.
pygame.display.set_caption("Rhythmus-Autorunner")
clock = pygame.time.Clock()
obstacle_times = [] #eckige klammer is ne liste
music = pygame.mixer.Sound(str(MUSIC_PATH)) #gibt die musik-quelle an
slot = 0
presses=[]








#alles auf werkseinstellung und run starten
def start_run():
    """startet das spiel"""
    global t0, jump_start, hits, hit_obstacles, presses
    music.stop()
    if MUTE == False:
        music.play()
    t0 = time.perf_counter() - current_offset + bluetooth_offset - JUMP_LEAD # JUMP_LEAD damit der beat nicht genau über obst spielt sondern wann man drücken soll  # var ist zeit, an dem das script startete(perf_counter ist wie lange das OS schon läuft)
    hits = 0
    jump_start = None
    hit_obstacles = set()  #ist menge ohne duplikate
    presses=[]

# text
def draw_text(text, f, color, x, y):
    """malt so text und so"""
    screen.blit(f.render(text, True, color), (x, y))

def connect():
    conn=sqlite3.connect(str(DB_PATH))
    cursor=conn.cursor()
    return conn, cursor
conn, cursor = connect()

cursor.execute("SELECT count(DISTINCT participant) FROM runs")
participant_count = cursor.fetchone()[0]

def save_run(): # ganz viel in code-expl
    global participant_count
    conn, cursor = connect()
    cursor.execute("""INSERT INTO runs (participant, offset, seed, bpm, time_started, hits, position, calib_offset, calib_sd, jump_lead, run_nr)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (participant_id, current_offset, LEVEL_SEED, BPM,
         datetime.now().isoformat(timespec="seconds"), hits, condition_index, calib_offset, calib_sd, JUMP_LEAD, run_count)
    )
    run_id = cursor.lastrowid

    cursor.executemany( # schreibt mehrere zeilen auf einmal
        "INSERT INTO presses (run_id, t_press, effektiv) VALUES (?, ?, ?)",
        [(run_id, tp, int(eff)) for tp, eff in presses]#[(a, b, c) for-schleife]; for a, b in... macht tupel-entpackung
    )
    cursor.executemany(
        "INSERT INTO obstacles (run_id, idx, beat_time, hit) VALUES (?, ?, ?, ?)",
        [(run_id, i, bt, int(i in hit_obstacles)) for i, bt in enumerate(obstacle_times)] # i-teil: checkt bei enumerate(obstacle_times)[nr., beat] ob nr. in hit_obstacles ist
    )  
    """enumerate() macht so aus obstacle_times=[a, v, s] [(0, a), (1, v), (2, s)]"""
    print(f"gespeichert: run {run_id}, VP {participant_id}, offset {current_offset}")
    cursor.execute("SELECT count(DISTINCT participant) FROM runs") # nur QoL für part. count in menu
    participant_count = cursor.fetchone()[0]
    conn.commit()
    conn.close()


while True:
    beat = LEAD_IN_BEATS + slot * SLOT_BEATS   #berechnet beat
    t_obstacle = beat * SECONDS_PER_BEAT # wann das obst. kommen wird # 0,5 damit der beat nicht genau über obst spielt sondern wann man drücken soll 
    if t_obstacle > MUSIC_END:
        break
    obstacle_times.append(t_obstacle) #append ist func der liste, hängt einen wert an die liste
    slot += rng.choice(GAP_CHOICES) #geht zur nächsten rand. stelle
# fügt verschiedene stellen hinzu, wo obst. auftauchen



state = STATE_MENU
t0 = None
t = 0.0
jump_start = None
hits = 0
hit_obstacles = set()
running = True
conditions = []
condition_index = 0
current_offset = 0.0
calib_offset = None
calib_sd = None
practices = 0
run_count = 0







while running: # damit nicht unvollständig abgebrochen wird

    screen.fill((18, 18, 22))             # farbcode(aka. RGB-Tupel) für farbe über ganzes bild
    # Ereigniswarteschlange jeden Frame leeren, sonst haelt das
    # Betriebssystem das Fenster fuer abgestuerzt.

    #event-horizon
    for event in pygame.event.get(): #event ist ne var event.get() ist die liste. kann mehrmals pro tick abarbeiten, weil clock.tick extra steht
        
        if event.type == pygame.QUIT: #event.type ist immer ein attribut aus dem anstehenden event. QUIT ist wenn geschlossen wird
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:# keydown ist wenn key gedrrückt wurd(KEYUP ist wenn losgelassen)
                running = False

            elif state == STATE_MENU:
                if event.unicode.isdigit() and len(participant_id) < 3:
                    participant_id += event.unicode   
                elif event.key == pygame.K_BACKSPACE:
                    participant_id = participant_id[:-1] # siehe code expl
                elif event.key == pygame.K_RETURN and participant_id != "":
                    conditions = OFFSETS[:]   #[:] macht kopie der liste damit nix kapputt
                    random.Random(int(participant_id)).shuffle(conditions) # macht shuffle
                    condition_index = 0
                    current_offset = PRACTICE_OFFSET
                    state = STATE_PRACTICE
                    start_run()
                elif event.key == pygame.K_k:
                    state = STATE_CALIBRATE
                    start_calib()

            elif state == STATE_CALIBRATE and event.key == pygame.K_SPACE:
                calib_presses.append(t)

            elif state in (STATE_PRACTICE, STATE_RUNNING) and event.key == pygame.K_SPACE:   #springen       
                presses.append((t, jump_start is None))    # jumpstart is None -> ergebnis ist true/false
                if jump_start is None:          # nur springen, wenn am Boden
                    jump_start = t
            elif DEBUG and state in (STATE_PRACTICE, STATE_RUNNING) and event.key == pygame.K_s:
                t0 -= 100          # Zeit vorspulen zu ende
            elif state == STATE_BREAK and event.key == pygame.K_RETURN:
                current_offset = conditions[condition_index]
                if practices >= PRACTICE_TIMES:
                    state = STATE_RUNNING
                else:
                    state = STATE_PRACTICE
                start_run()

            elif state == STATE_DONE and event.key == pygame.K_RETURN:
                participant_id = ""
                state = STATE_MENU
            

    if state == STATE_MENU:
        draw_text(str(participant_count), font, DIM_COLOR, 0, 0)
        draw_text("Rhythmus-Autorunner", title_font, TEXT_COLOR, 80, 150)
        draw_text("Versuchsperson: "+ str(participant_id), font, TEXT_COLOR, 80, 260)
        draw_text("Ziffern eingeben         Enter zum starten", font, DIM_COLOR, 80, 310)
    
    
    
    elif state == STATE_CALIBRATE:
        t = time.perf_counter() - t0
        beat_nr = t / SECONDS_PER_BEAT

        if beat_nr < CALIB_COUNTIN_BEATS:
            draw_text("Zuhören", title_font, DIM_COLOR, 80, 200)
        elif beat_nr < CALIB_COUNTIN_BEATS + CALIB_TAP_BEATS:
            draw_text("mitdrücken", title_font, TEXT_COLOR, 80, 200)
        else:
            music.stop()
            grenze = CALIB_COUNTIN_BEATS * SECONDS_PER_BEAT - 0.25
            gewertet = [tp for tp in calib_presses if tp >= grenze]
            abw = [tp - round(tp / SECONDS_PER_BEAT) * SECONDS_PER_BEAT
                   for tp in gewertet]
            if len(abw) >= 5:
                calib_offset = statistics.median(abw)
                calib_sd = statistics.stdev(abw)
            state = STATE_MENU

    elif state in (STATE_RUNNING, STATE_PRACTICE): # in checkt so listen,ist kürzer
        
        
        
        """game-code anfang"""

        t = time.perf_counter() - t0 # t=wie lange es her ist bis das game startete
        #
        # springen
        if jump_start is None:    
            player_y = GROUND_Y
        else:
            tau = t - jump_start
            height = JUMP_VELOCITY * tau - 0.5 * GRAVITY * tau * tau
            if tau >= JUMP_DURATION:
                jump_start = None               # gelandet
                player_y = GROUND_Y
            else:
                player_y = GROUND_Y - height

        player_rect = pygame.Rect(PLAYER_X, player_y - PLAYER_SIZE, PLAYER_SIZE, PLAYER_SIZE)
        screen.fill((18, 18, 22))             # farbcode(aka. RGB-Tupel) für farbe über ganzes bild



    
        # Boden
        pygame.draw.line(screen, (60, 60, 70), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

        # Hindernisse schreiben
        for i, beat_time in enumerate(obstacle_times):
            x = PLAYER_X + (beat_time - t) * SCROLL_SPEED #position
            OBST_SIZE=obst_size(x)
            obstacle_rect = pygame.Rect(OBST_SIZE) #definiert das obstacle i
            if -50 < x < WIDTH: #wenn im bildschirm
                pygame.draw.rect(screen, (220, 80, 80), obstacle_rect) # malt das bobstacle

            if i not in hit_obstacles and player_rect.colliderect(obstacle_rect):   #.coliderect() gibt true beim
                hits += 1
                hit_obstacles.add(i)

        # Figur
        pygame.draw.rect(screen, (235, 235, 240), player_rect)           #pygame.draw.rect(screen, (235, 235, 240), (100, 300, 40, 40)) #farbe, dann (x, y, Breite, Höhe) wobei x,y zur linken oberen Ecke



        screen.blit(font.render(f"Treffer: {hits}", True, (200, 200, 210)), (20, 20))
        
        # game-code ende
        

        # checkt so ob das spiel zuende ist
        if t > obstacle_times[-1] + 8:
            run_count += 1
            music.stop()
            if state == STATE_PRACTICE:
                state = STATE_BREAK
                practices += 1
            else:
                save_run()
                condition_index += 1
                state = STATE_DONE if condition_index >= len(conditions) else STATE_BREAK
    if state == STATE_DONE:
        draw_text("Test beendet", title_font, TEXT_COLOR, 80, 200)
        draw_text(f"Versuchsperson {participant_id} — {hits} Treffer", font, DIM_COLOR, 80, 290)
        draw_text("Bitte auf Anweisungen warten", font, DIM_COLOR,80, 310)
    elif state == STATE_BREAK:
        draw_text("Pause", title_font, TEXT_COLOR, 80, 180)
        if practices >= PRACTICE_TIMES:
            draw_text(f"Als nächstes: Durchgang {condition_index + 1} von {len(conditions)}",
                      font, TEXT_COLOR, 80, 270)
        else:
            draw_text(f"Als nächstes: Übung {practices + 1} von {PRACTICE_TIMES}",
                      font, TEXT_COLOR, 80, 270)
        draw_text("Enter startet den nächsten Durchgang", font, DIM_COLOR, 80, 320)
        

    pygame.display.flip()                  # Gezeichnetes sichtbar machen
            
    clock.tick(FPS)                        # Begrenzt auf FPS (expl. unter ~/code-expl/clock.tick()), begrenzt gleichzeitig cpu auslastung
    

pygame.quit()