import pygame
import time
import random
#Fenster erstellen


WIDTH, HEIGHT = 960, 540 #genau 1/4 von FHD; passt auf jeden bildschirm
FPS = 120 #zeitliche Auflösung=8,3ms bc length of frame=8,3ms
SCROLL_SPEED = 400 #pixel/sec
BPM = 120
SECONDS_PER_BEAT = 60 / BPM     # 0,5 s bei 120 BPM, eif formatierung
PLAYER_X = 200                  # feste Position der Figur 
GROUND_Y = 380                  # Hoehe des Bodens
LEAD_IN_BEATS = 16               # beats vor dem ersten Hindernis
N_OBSTACLES = 44           #anzahl obstacles
AUDIO_OFFSET = 0.0              # +=früher;-=später;in sec.
JUMP_VELOCITY = 1000           # Startgeschwindigkeit nach oben, Pixel/s
GRAVITY = 4000                # Beschleunigung nach unten, Pixel/s²
OBSTACLE_EVERY_N_BEATS = 1    # Hindernis nur auf jedem zweiten Beat
JUMP_DURATION = 2 * JUMP_VELOCITY / GRAVITY
LEVEL_SEED = 42
SLOT_BEATS = 1
GAP_CHOICES = [1, 2, 2, 2, 3]
MUSIC_END = 48.0

rng = random.Random(LEVEL_SEED)
pygame.init() #startet die untersysteme
font = pygame.font.SysFont(None, 32)
t0 = time.perf_counter() # var ist zeit, an dem das script startete(perf_counter ist wie lange das OS schon läuft)
screen=pygame.display.set_mode((WIDTH, HEIGHT)) #erstellt bild(auch alleine). var ist für verweis auf objekt. setmode braucht tupel, desshalb doppelte klammern.
pygame.display.set_caption("Rhythmus-Autorunner")
clock = pygame.time.Clock()
obstacle_times = [] #eckige klammer is ne liste
slot = 0

while True:
    beat = LEAD_IN_BEATS + slot * SLOT_BEATS #berechnet beat
    t_obstacle = beat * SECONDS_PER_BEAT # wann das obst. kommen wird
    if t_obstacle > MUSIC_END:
        break
    obstacle_times.append(t_obstacle) #append ist func der liste, hängt einen wert an die liste
    slot += rng.choice(GAP_CHOICES) #geht zur nächsten rand. stelle
# fügt verschiedene stellen hinzu, wo obst. auftauchen

running = True
jump_start = None   #am boden
hits = 0
hit_obstacles = set()  #ist menge ohne duplikate


pygame.key.set_repeat(50, 10)
while running: # damit nicht unvollständig abgebrochen wird
    t = time.perf_counter() - t0 # t=wie lange es her ist bis das programm startete


    # Ereigniswarteschlange jeden Frame leeren, sonst haelt das
    # Betriebssystem das Fenster fuer abgestuerzt.

    #event-horizon
    for event in pygame.event.get(): #event ist ne var event.get() ist die liste. kann mehrmals pro tick abarbeiten, weil clock.tick extra steht
        if event.type == pygame.QUIT: #event.type ist immer ein attribut aus dem anstehenden event. QUIT ist wenn geschlossen wird
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:# keydown ist wenn key gedrrückt wurd(KEYUP ist wenn losgelassen)
            running = False
        elif (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):   #springen
            if jump_start is None:          # nur springen, wenn am Boden
                jump_start = t
                jumped=event

    
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

    # Hindernisse
    for i, beat_time in enumerate(obstacle_times):
        x = PLAYER_X + (beat_time - t) * SCROLL_SPEED #position
        obstacle_rect = pygame.Rect(x, GROUND_Y - 60, 30, 60) #definiert das obstacle i
        if -50 < x < WIDTH: #wenn im bildschirm
            pygame.draw.rect(screen, (220, 80, 80), obstacle_rect) # malt das obstacle

        if i not in hit_obstacles and player_rect.colliderect(obstacle_rect):   #.coliderect() gibt true beim
            hits += 1
            hit_obstacles.add(i)

    # Figur
    pygame.draw.rect(screen, (235, 235, 240), player_rect)           #pygame.draw.rect(screen, (235, 235, 240), (100, 300, 40, 40)) #farbe, dann (x, y, Breite, Höhe) wobei x,y zur linken oberen Ecke



    screen.blit(font.render(f"Treffer: {hits}", True, (200, 200, 210)), (20, 20))
    pygame.display.flip()                  # Gezeichnetes sichtbar machen

    clock.tick(FPS)                        # Begrenzt auf FPS (expl. unter ~/code-expl/clock.tick()), begrenzt gleichzeitig cpu auslastung

pygame.quit()