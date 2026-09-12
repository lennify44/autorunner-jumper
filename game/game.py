import pygame
import time
import random
from pathlib import Path
import sqlite3
import math
from datetime import datetime
#Fenster erstellen

STATE_MENU, STATE_RUNNING, STATE_DONE = "menu", "running", "done"

TEXT_COLOR = (235, 235, 240)
DIM_COLOR = (120, 120, 135)
WIDTH, HEIGHT = 960, 540 #genau 1/4 von FHD; passt auf jeden bildschirm
FPS = 120 #zeitliche Auflösung=8,3ms bc length of frame=8,3ms
SCROLL_SPEED = 400 #pixel/sec
BPM = 120
SECONDS_PER_BEAT = 60 / BPM     # 0,5 s bei 120 BPM, eif formatierung
PLAYER_X = 200                  # feste Position der Figur 
GROUND_Y = 380                  # Hoehe des Bodens
def obst_size():
    OBST_SIZE=x, GROUND_Y - 60, 30, 60
    return OBST_SIZE
PLAYER_SIZE = 40
OBSTACLE_W = 30
OBSTACLE_H = 60
LEAD_IN_BEATS = 16               # beats vor dem ersten Hindernis
# N_OBSTACLES = 88         #anzahl obstacle-slots
AUDIO_OFFSET = 0             # +=später;-=früher;in sec.; gute:-0.1
JUMP_VELOCITY = 1000           # Startgeschwindigkeit nach oben, Pixel/s
GRAVITY = 4000                # Beschleunigung nach unten, Pixel/s²
OBSTACLE_EVERY_N_BEATS = 1    # Hindernis-slots auf jedem Beat
JUMP_DURATION = 2 * JUMP_VELOCITY / GRAVITY
LEVEL_SEED = 42
SLOT_BEATS = 1
GAP_CHOICES = [1, 2, 2, 2, 2, 2, 3, 4, 4, 4]
MUSIC_END = 60.0
MUSIC_PATH = Path(__file__).parent / "game_music.wav"
DB_PATH = Path(__file__).parent / "auto-save.sqlite"

# berechnet den optimalpunkt zum springen
_overlap_start = -PLAYER_SIZE / SCROLL_SPEED
_overlap_end = OBSTACLE_W / SCROLL_SPEED
_d = math.sqrt(JUMP_VELOCITY**2 - 2 * GRAVITY * OBSTACLE_H)
_tau_up = (JUMP_VELOCITY - _d) / GRAVITY
_tau_down = (JUMP_VELOCITY + _d) / GRAVITY
JUMP_LEAD = -((_overlap_start - _tau_up) + (_overlap_end - _tau_down)) / 2
print(JUMP_LEAD)


def lustig(): #"etwas" schwerer
    """falls den probanten langweilig wird, ist das hier eine challenge für hinterher ;)"""
    global WIDTH, SCROLL_SPEED, obst_size, FPS, JUMP_VELOCITY
    WIDTH = 1900
    JUMP_VELOCITY = 1300
    SCROLL_SPEED = 4000
    def obst_size():
        OBST_SIZE=x, GROUND_Y - 120, 480, 120
        return OBST_SIZE
    FPS = 240
# lustig()


pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512) # bereitet die einstellungen vor; muss vor init() weil der die fest macht
rng = random.Random(LEVEL_SEED)
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


while True:
    beat = LEAD_IN_BEATS + slot * SLOT_BEATS   #berechnet beat
    t_obstacle = beat * SECONDS_PER_BEAT # wann das obst. kommen wird # 0,5 damit der beat nicht genau über obst spielt sondern wann man drücken soll 
    if t_obstacle > MUSIC_END:
        break
    obstacle_times.append(t_obstacle) #append ist func der liste, hängt einen wert an die liste
    slot += rng.choice(GAP_CHOICES) #geht zur nächsten rand. stelle
# fügt verschiedene stellen hinzu, wo obst. auftauchen




#alles auf werkseinstellung und run starten
def start_run():
    """startet das spiel"""
    global t0, jumpstart, hits, hit_obstacles, presses
    music.stop()
    music.play()
    t0 = time.perf_counter() - AUDIO_OFFSET + JUMP_LEAD # JUMP_LEAD damit der beat nicht genau über obst spielt sondern wann man drücken soll  # var ist zeit, an dem das script startete(perf_counter ist wie lange das OS schon läuft)
    hits = 0
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


def save_run(): # ganz viel in code-expl
    conn, cursor = connect()
    cursor.execute(
        """INSERT INTO runs (participant, offset, seed, bpm, time_started, hits) VALUES (?, ?, ?, ?, ?, ?)""", 
        (participant_id, AUDIO_OFFSET, LEVEL_SEED, BPM, 
         datetime.now().isoformat(timespec="seconds"), hits)
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
    conn.commit()
    conn.close()


state = STATE_MENU
participant_id = ""
t0 = None
t = 0.0
jump_start = None
hits = 0
hit_obstacles = set()
running = True







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
                    
                    #conn, cursor = connect()
                    #cursor.execute("SELECT participant FROM runs WHERE participant = (?)", (participant_id,))
                    #list = cursor.fetchone()# [0] soll den Tupel auspacken
                    #conn.close()
                    #if list == None: 
                    state = STATE_RUNNING
                    start_run()
            elif state == STATE_RUNNING and event.key == pygame.K_SPACE:   #springen       
                presses.append((t, jump_start is None))    # jumpstart is None -> ergebnis ist true/false
                if jump_start is None:          # nur springen, wenn am Boden
                    jump_start = t

            elif state == STATE_DONE and event.key == pygame.K_RETURN:
                state = STATE_RUNNING 
                start_run()
            

    if state == STATE_MENU:
        conn, cursor = connect()
        cursor.execute("SELECT count(DISTINCT participant) FROM runs")
        count = cursor.fetchone()
        conn.close()
        draw_text(str(count), font, DIM_COLOR, 0, 0)
        draw_text("Rhythmus-Autorunner", title_font, TEXT_COLOR, 80, 150)
        draw_text("Versuchsperson: "+ str(participant_id), font, TEXT_COLOR, 80, 260)
        draw_text("Ziffern eingeben         Enter zum starten", font, DIM_COLOR, 80, 310)
    elif state == STATE_RUNNING:

        ######game-code anfang


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

        player_rect = pygame.Rect(PLAYER_X, player_y - 40, 40, 40)
        screen.fill((18, 18, 22))             # farbcode(aka. RGB-Tupel) für farbe über ganzes bild



    
        # Boden
        pygame.draw.line(screen, (60, 60, 70), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

        # Hindernisse schreiben
        for i, beat_time in enumerate(obstacle_times):
            x = PLAYER_X + (beat_time - t) * SCROLL_SPEED #position
            OBST_SIZE=obst_size()
            obstacle_rect = pygame.Rect(OBST_SIZE) #definiert das obstacle i
            if -50 < x < WIDTH: #wenn im bildschirm
                pygame.draw.rect(screen, (220, 80, 80), obstacle_rect) # malt das obstacle

            if i not in hit_obstacles and player_rect.colliderect(obstacle_rect):   #.coliderect() gibt true beim
                hits += 1
                hit_obstacles.add(i)

        # Figur
        pygame.draw.rect(screen, (235, 235, 240), player_rect)           #pygame.draw.rect(screen, (235, 235, 240), (100, 300, 40, 40)) #farbe, dann (x, y, Breite, Höhe) wobei x,y zur linken oberen Ecke



        screen.blit(font.render(f"Treffer: {hits}", True, (200, 200, 210)), (20, 20))
        
        # game-code ende
        

        # checkt so ob das spiel zuende ist
        if t > obstacle_times[-1] + 7:
            music.stop()
            state = STATE_DONE
            save_run()
    if state == STATE_DONE:
        draw_text("Durchlauf beendet", title_font, TEXT_COLOR, 80, 200)
        draw_text(f"Versuchsperson {participant_id} — {hits} Treffer", font, DIM_COLOR, 80, 290)
        draw_text("Enter zum erneut versuchen", font, DIM_COLOR,80, 310)
        

    pygame.display.flip()                  # Gezeichnetes sichtbar machen
            
    clock.tick(FPS)                        # Begrenzt auf FPS (expl. unter ~/code-expl/clock.tick()), begrenzt gleichzeitig cpu auslastung
    

pygame.quit()