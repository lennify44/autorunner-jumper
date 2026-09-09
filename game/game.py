import pygame
import time
#Fenster erstellen


WIDTH, HEIGHT = 960, 540 #genau 1/4 von FHD; passt auf jeden bildschirm
FPS = 120 #zeitliche Auflösung=8,3ms bc length of frame=8,3ms
SCROLL_SPEED = 300 #pixel/sec
BPM = 120
SECONDS_PER_BEAT = 60 / BPM     # 0,5 s bei 120 BPM, eif formatierung
PLAYER_X = 200                  # feste Position der Figur 
GROUND_Y = 380                  # Hoehe des Bodens
LEAD_IN_BEATS = 4               # Vorlauf, bevor das erste Hindernis kommt
N_OBSTACLES = 32           #anzahl obstacles
JUMP_VELOCITY = 600           # Startgeschwindigkeit nach oben, Pixel/s
GRAVITY = 2000                # Beschleunigung nach unten, Pixel/s²
OBSTACLE_EVERY_N_BEATS = 2    # Hindernis nur auf jedem zweiten Beat
JUMP_DURATION = 2 * JUMP_VELOCITY / GRAVITY


pygame.init() #startet die untersysteme
font = pygame.font.SysFont(None, 32)
t0 = time.perf_counter() # var ist zeit, an dem das script startete(perf_counter ist wie lange das OS schon läuft)
screen=pygame.display.set_mode((WIDTH, HEIGHT)) #erstellt bild(auch alleine). var ist für verweis auf objekt. setmode braucht tupel, desshalb doppelte klammern.
pygame.display.set_caption("Rhythmus-Autorunner")
clock = pygame.time.Clock()

obstacle_times = [] #eckige klammer is ne liste
for i in range(N_OBSTACLES):           #"für jedes obstacle"
    obstacle_times.append((LEAD_IN_BEATS + i * OBSTACLE_EVERY_N_BEATS) * SECONDS_PER_BEAT) #append ist func der liste, hängt einen wert an die liste
#macht eine liste von zeitpunkten in sec.       sagt später wann objekte entstehen sollen

running = True
jump_start = None   #am boden
hits = 0
hit_obstacles = set()  #ist menge ohne duplikate



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
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:   #springen
            if jump_start is None:          # nur springen, wenn am Boden
                jump_start = t
    
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
        if -50 < x < WIDTH: #wenn im bildschirm
            obstacle_rect = pygame.Rect(x, GROUND_Y - 60, 30, 60) #definiert das obstacle i
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