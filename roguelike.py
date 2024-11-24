import pygame
import random

# Inicjalizacja Pygame
pygame.init()

WIDTH, HEIGHT = 800, 600  # Rozmiar ekranu
TILE_SIZE = 32  # Rozmiar kafelka
MAP_WIDTH, MAP_HEIGHT = 50, 50  # Rozmiar mapy w kafelkach
VISIBLE_TILES_X = WIDTH // TILE_SIZE
VISIBLE_TILES_Y = HEIGHT // TILE_SIZE

# Kolory
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Ustawienia ekranu
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Roguelike Game")

# Klasa Kamery
class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x_offset = 0  # Przesunięcie kamery w osi X
        self.y_offset = 0  # Przesunięcie kamery w osi Y

    def update(self, player):
        """
        Aktualizuje pozycję kamery na podstawie pozycji gracza.
        Kamera śledzi gracza i ogranicza widok do granic mapy.
        """
        self.x_offset = player.x * TILE_SIZE - self.width // 2 + TILE_SIZE // 2
        self.y_offset = player.y * TILE_SIZE - self.height // 2 + TILE_SIZE // 2

        # Ograniczenie przesunięcia kamery, aby nie wychodziła poza mapę
        self.x_offset = max(0, min(self.x_offset, MAP_WIDTH * TILE_SIZE - self.width))
        self.y_offset = max(0, min(self.y_offset, MAP_HEIGHT * TILE_SIZE - self.height))

    def apply(self, x, y):
        """
        Przekształca globalne współrzędne obiektów na współrzędne lokalne względem kamery.
        """
        return x * TILE_SIZE - self.x_offset, y * TILE_SIZE - self.y_offset



# Klasa Gracza
class Player:
    def __init__(self, x, y):
        # Statystyki gracza
        self.x = x
        self.y = y
        self.hp = 100
        self.max_hp = 100
        self.damage = 10
        self.attack_speed = 1
        self.defense = 0
        self.last_shoot_time = 0  # Czas ostatniego strzału
        self.last_move_time = 0  # Czas ostatniego ruchu
        self.last_damage_time = 0
        self.move_delay = 150  # Minimalny czas między ruchami (w ms)
        self.holy_water_level = 0  # Poziom Holy Water (0 oznacza brak umiejętności)
        self.holy_water_damage = 0  # Bazowe obrażenia Holy Water
        self.holy_water_aoe = TILE_SIZE  # Obszar działania Holy Water
        self.last_holy_water_time = 0  # Czas ostatniego rzutu Holy Water

        # Doświadczenie
        self.exp = 0
        self.level = 1
        self.next_level_exp = 100

        # Załaduj obraz gracza
        self.image = pygame.image.load("23.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILE_SIZE*3, TILE_SIZE*3))  # Dopasuj do TILE_SIZE


    def throw_holy_water(self, holy_waters):
        """Rzucanie Holy Water, jeśli odblokowane."""
        if self.holy_water_level > 0:  # Sprawdzamy, czy gracz odblokował umiejętność
            current_time = pygame.time.get_ticks()
            if current_time - self.last_holy_water_time >= 3000:  # Rzucanie co 3 sekundy
                self.last_holy_water_time = current_time

                # Losowy kierunek
                directions = [(0, -5), (0, 5), (-5, 0), (5, 0)]  # Góra, dół, lewo, prawo
                dx, dy = random.choice(directions)

                # Ustawienie pozycji rzutu
                holy_water_x = (self.x + dx) * TILE_SIZE
                holy_water_y = (self.y + dy) * TILE_SIZE

                # Tworzenie obiektu Holy Water
                holy_water = HolyWater(holy_water_x, holy_water_y, self.holy_water_damage, self.holy_water_aoe)
                holy_waters.append(holy_water)

    def upgrade_holy_water(self):
        """Ulepszanie Holy Water na wyższy poziom."""
        if self.holy_water_level < 5:  # Maksymalny poziom to 5
            self.holy_water_level += 1
            self.holy_water_damage += 5  # Każdy poziom dodaje 5 obrażeń
            self.holy_water_aoe += int(self.holy_water_aoe * 0.1)  # Powiększamy obszar działania o 10%

    def gain_exp(self, amount):
        """Zdobywanie doświadczenia"""
        self.exp += amount
        if self.exp >= self.next_level_exp:
            self.level_up()

    def level_up(self):
        """Awans na kolejny poziom"""
        self.exp -= self.next_level_exp
        self.level += 1
        self.next_level_exp += 50  # Zwiększ wymagane EXP do następnego poziomu
        self.show_level_up_dialog()

    def show_level_up_dialog(self):
        """Wyświetlanie okna dialogowego wyboru nagrody."""
        font = pygame.font.Font(None, 36)
        running = True
        while running:
            screen.fill(BLACK)

            # Wyświetlanie opcji
            text = font.render("Level Up! Choose an upgrade:", True, WHITE)
            dmg_text = font.render("1: Increase Damage (+5)", True, WHITE)
            hp_text = font.render("2: Increase Max HP (+5)", True, WHITE)
            if self.holy_water_level < 5:
                holy_water_text = font.render(
                    "3: Upgrade Holy Water (+" + str(5 + self.holy_water_level) + " Damage, +10% AOE)", True, WHITE)

            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100))
            screen.blit(dmg_text, (WIDTH // 2 - dmg_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(hp_text, (WIDTH // 2 - hp_text.get_width() // 2, HEIGHT // 2))
            if self.holy_water_level < 5:
                screen.blit(holy_water_text, (WIDTH // 2 - holy_water_text.get_width() // 2, HEIGHT // 2 + 50))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.damage += 5
                        running = False
                    elif event.key == pygame.K_2:
                        self.max_hp += 5
                        self.hp += 5
                        running = False
                    elif event.key == pygame.K_3 and self.holy_water_level < 5:
                        self.upgrade_holy_water()
                        running = False

    def draw_xp_bar(surface, player):
        """Rysowanie paska doświadczenia."""
        bar_width = WIDTH - 20  # Szerokość paska (mniej niż szerokość ekranu)
        bar_height = 20  # Wysokość paska
        x = 10  # Odstęp od lewej krawędzi ekranu
        y = HEIGHT - 30  # Odstęp od dolnej krawędzi ekranu

        # Obliczanie proporcji wypełnienia paska
        xp_ratio = player.exp / player.next_level_exp

        # Rysowanie tła paska
        pygame.draw.rect(surface, GRAY, (x, y, bar_width, bar_height))
        # Rysowanie wypełnionej części paska
        pygame.draw.rect(surface, YELLOW, (x, y, int(bar_width * xp_ratio), bar_height))
        # Rysowanie obramowania paska
        pygame.draw.rect(surface, WHITE, (x, y, bar_width, bar_height), 2)

        # Wyświetlanie poziomu gracza
        font = pygame.font.Font(None, 24)
        text = font.render(f"Level {player.level}", True, WHITE)
        surface.blit(text, (x + 5, y - 25))

    def shoot(self, projectiles, direction):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shoot_time >= 500:  # Strzał co 500 ms
            self.last_shoot_time = current_time
            dx, dy = direction

            # Początkowa pozycja pocisku: środek gracza
            projectile_x = self.x * TILE_SIZE + TILE_SIZE*3 // 2
            projectile_y = self.y * TILE_SIZE + TILE_SIZE*3 // 2

            # Tworzenie pocisku
            projectile = Projectile(projectile_x, projectile_y, dx, dy, speed=10)
            projectiles.append(projectile)

    def move(self, dx, dy, game_map):
        """Ograniczenie ruchu gracza w czasie"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time >= self.move_delay:  # Ruch co move_delay ms
            new_x = self.x + dx
            new_y = self.y + dy

            # Sprawdzamy, czy nowa pozycja mieści się w granicach mapy
            if 0 <= new_x < len(game_map[0]) and 0 <= new_y < len(game_map):
                self.x = new_x
                self.y = new_y

            self.last_move_time = current_time  # Aktualizacja czasu ostatniego ruchu

    def take_damage(self, damage):
        """Metoda do otrzymywania obrażeń"""
        reduced_damage = max(damage - self.defense, 0)  # Obrona zmniejsza obrażenia
        self.hp -= reduced_damage
        print(f"Gracz otrzymał obrażenia: {reduced_damage}, HP: {self.hp}/{self.max_hp}")
        if self.hp <= 0:
            self.hp = 0
            print("Gracz zginął!")

    def attack(self, enemy):
        """Metoda do atakowania przeciwnika"""
        print(f"Atakuję przeciwnika za {self.damage} obrażeń!")
        enemy.take_damage(self.damage)

    def heal(self, amount):
        """Metoda do leczenia gracza"""
        self.hp = min(self.hp + amount, self.max_hp)
        print(f"Gracz wyleczony do {self.hp}/{self.max_hp} HP.")

    def auto_attack(self, enemies):
        """Automatyczne atakowanie przeciwników w zasięgu"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time >= 1000:  # Atak co 1 sekundę
            self.last_attack_time = current_time
            for enemy in enemies:
                if abs(self.x - enemy.x) <= 1 and abs(self.y - enemy.y) <= 1:  # Wrogowie w zasięgu 1 kratki
                    self.attack(enemy)

    def draw(self, surface, camera):
        # Przekształć pozycję gracza w pozycję względem kamery
        screen_x, screen_y = camera.apply(self.x, self.y)

        # Rysuj obraz gracza
        surface.blit(self.image, (screen_x, screen_y))

        # Rysowanie paska HP nad postacią
        pygame.draw.rect(surface, RED, (screen_x, screen_y - 10, TILE_SIZE*3, 5))
        pygame.draw.rect(surface, GREEN, (screen_x, screen_y - 10, TILE_SIZE*3 * (self.hp / self.max_hp), 5))

class HolyWater:
    def __init__(self, x, y, damage, aoe):
        self.x = x
        self.y = y
        self.damage = damage
        self.aoe = aoe  # Promień działania
        self.duration = 20000  # Czas trwania w ms
        self.start_time = pygame.time.get_ticks()  # Moment rzutu

        # Ładowanie obrazu Holy Water
        self.image = pygame.image.load("holywater.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.aoe * 2, self.aoe * 2))  # Dopasowanie do rozmiaru AOE

    def draw(self, surface, camera):
        """Rysowanie Holy Water na ekranie."""
        screen_x = self.x - camera.x_offset
        screen_y = self.y - camera.y_offset
        # Rysowanie obrazu Holy Water na ekranie
        surface.blit(self.image, (screen_x - self.aoe, screen_y - self.aoe))

    def is_active(self):
        """Sprawdzenie, czy Holy Water jeszcze działa."""
        current_time = pygame.time.get_ticks()
        return current_time - self.start_time <= self.duration

    def check_collision(self, enemies, player):
        """Zadawanie obrażeń przeciwnikom w obszarze działania."""
        for enemy in enemies[:]:  # Przechodzimy przez listę przeciwników
            enemy_center_x, enemy_center_y = enemy.get_center()
            distance = ((self.x - enemy_center_x) ** 2 + (self.y - enemy_center_y) ** 2) ** 0.5
            if distance <= self.aoe:
                enemy.take_damage(self.damage)
                if enemy.hp <= 0:  # Jeśli przeciwnik zginął
                    enemies.remove(enemy)  # Usuń przeciwnika z listy
                    player.gain_exp(20)  # Przyznaj doświadczenie graczowi

class Enemy:
    def __init__(self, x, y, hp, damage):
        self.x = x
        self.y = y
        self.hp = hp
        self.damage = damage
        self.color = (255, 0, 0)
        self.move_delay = 500  # Czas między ruchami w ms
        self.last_move_time = pygame.time.get_ticks()
        self.respawn_delay = random.randint(1000, 3000)  # Losowy czas respawnu (5-15 sekund)
        self.last_respawn_time = pygame.time.get_ticks()
        self.is_dead = False  # Czy przeciwnik jest martwy

        self.image = pygame.image.load("3.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILE_SIZE*3, TILE_SIZE*3))  # Dopasuj do TILE_SIZE

    def move_towards_player(self, player):
        """Poruszanie się przeciwnika w kierunku gracza"""
        if self.is_dead:
            return  # Martwy przeciwnik się nie porusza

        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time >= self.move_delay:
            self.last_move_time = current_time
            dx = player.x - self.x
            dy = player.y - self.y

            if abs(dx) > abs(dy):  # Ruch w poziomie
                self.x += 1 if dx > 0 else -1
            else:  # Ruch w pionie
                self.y += 1 if dy > 0 else -1

    def take_damage(self, damage):
        """Otrzymanie obrażeń"""
        if self.is_dead:
            return  # Martwy przeciwnik nie otrzymuje obrażeń

        self.hp -= damage
        print(f"Przeciwnik otrzymał {damage} obrażeń. Pozostało HP: {self.hp}")
        if self.hp <= 0:
            self.is_dead = True  # Oznacz jako martwego
            self.last_respawn_time = pygame.time.get_ticks()  # Ustaw czas "śmierci"
            print("Przeciwnik zginął!")

    def should_respawn(self):
        """Sprawdzenie, czy przeciwnik powinien się zrespawnować"""
        current_time = pygame.time.get_ticks()
        return self.is_dead and (current_time - self.last_respawn_time >= self.respawn_delay)

    def respawn(self, width, height):
        """Respawn przeciwnika w nowej losowej pozycji"""
        self.x = random.randint(0, width - 1)
        self.y = random.randint(0, height - 1)
        self.hp = 50  # Reset HP
        self.is_dead = False  # Przywróć do życia
        print(f"Przeciwnik zrespawnował się w pozycji ({self.x}, {self.y})")

    def attack(self, player):
        print(f"Przeciwnik atakuje za {self.damage} obrażeń!")
        player.take_damage(self.damage)

    def get_center(self):
        """Zwraca współrzędne środka obrazu przeciwnika."""
        center_x = self.x * TILE_SIZE + (TILE_SIZE * 3) // 2
        center_y = self.y * TILE_SIZE + (TILE_SIZE * 3) // 2
        return center_x, center_y

    def draw(self, surface, camera):
        screen_x, screen_y = camera.apply(self.x, self.y)
        surface.blit(self.image, (screen_x, screen_y))


class Projectile:
    def __init__(self, x, y, dx, dy, speed):
        self.x = x  # Współrzędna X w pikselach
        self.y = y  # Współrzędna Y w pikselach
        self.dx = dx  # Kierunek ruchu w osi X (-1, 0, 1)
        self.dy = dy  # Kierunek ruchu w osi Y (-1, 0, 1)
        self.speed = speed  # Prędkość pocisku w pikselach na klatkę
        self.color = (255, 255, 0)  # Żółty kolor dla pocisku
        self.size = 5  # Rozmiar pocisku (promień)

    def move(self):
        """Aktualizacja pozycji pocisku."""
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

    def draw(self, surface, camera):
        """Rysowanie pocisku."""
        screen_x = int(self.x - camera.x_offset)
        screen_y = int(self.y - camera.y_offset)
        pygame.draw.circle(surface, self.color, (screen_x, screen_y), self.size)



# Funkcja generowania mapy
def generate_map(width, height):
    return [[random.choice([0, 0, 0, 1]) for _ in range(width)] for _ in range(height)]


def draw_map(surface, game_map, camera):
    # Załaduj obraz tła i przeskaluj go do rozmiarów całej mapy
    grass_tile = pygame.image.load("grass6.png").convert_alpha()
    grass_tile = pygame.transform.scale(grass_tile, (MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))

    # Oblicz przesunięcie kamery i wyświetl odpowiedni fragment tła
    screen_x = -camera.x_offset
    screen_y = -camera.y_offset
    surface.blit(grass_tile, (screen_x, screen_y))



def draw_minimap(surface, game_map, player, enemies, minimap_size):
    """Rysowanie minimapy w rogu ekranu."""
    if not game_map or not game_map[0]:  # Jeśli mapa jest pusta, nie rysujemy
        return

    minimap_width, minimap_height = minimap_size
    map_width = len(game_map[0])
    map_height = len(game_map)

    # Skalowanie kratki na minimapie
    tile_width = minimap_width // map_width
    tile_height = minimap_height // map_height

    # Rysowanie mapy
    for y, row in enumerate(game_map):
        for x, tile in enumerate(row):
            color = GRAY if tile == 1 else BLACK
            pygame.draw.rect(surface, color,
                             (x * tile_width, y * tile_height, tile_width, tile_height))

    # Rysowanie gracza na minimapie
    pygame.draw.rect(surface, GREEN,
                     (player.x * tile_width, player.y * tile_height, tile_width, tile_height))

    # Rysowanie przeciwników na minimapie
    for enemy in enemies:
        if not enemy.is_dead:  # Tylko żywi przeciwnicy
            pygame.draw.rect(surface, RED,
                             (enemy.x * tile_width, enemy.y * tile_height, tile_width, tile_height))

    # Obramowanie minimapy
    pygame.draw.rect(surface, WHITE, (0, 0, minimap_width, minimap_height), 2)


def show_death_screen():
    """Wyświetla ekran śmierci z opcjami resetu lub wyjścia."""
    font = pygame.font.Font(None, 72)
    small_font = pygame.font.Font(None, 36)

    while True:
        screen.fill(BLACK)

        # Teksty na ekranie śmierci
        title_text = font.render("You Died", True, RED)
        reset_text = small_font.render("Press R to Restart", True, WHITE)
        quit_text = small_font.render("Press Q to Quit", True, WHITE)

        # Wyświetlanie tekstów
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(reset_text, (WIDTH // 2 - reset_text.get_width() // 2, HEIGHT // 2))
        screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Restart gry
                    return True  # Zwraca True, aby zresetować grę
                elif event.key == pygame.K_q:  # Wyjście z gry
                    pygame.quit()
                    exit()

def generate_map_vampire_style(width, height):
    """
    Generuje mapę w stylu Vampire Survivors:
    - Krawędzie mapy (skały) jako '1'.
    - Wnętrze mapy (trawa) jako '0'.
    """
    game_map = []

    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                row.append(1)  # Skały na krawędziach
            else:
                row.append(0)  # Trawa w środku
        game_map.append(row)

    return game_map


def draw_background(surface):
    """
    Rysuje tło mapy na ekranie.
    """
    background = pygame.image.load("grass6.png")  # Ścieżka do pliku
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))  # Dopasowanie do rozmiaru ekranu
    surface.blit(background, (0, 0))


# Główna funkcja gry
def main():
    clock = pygame.time.Clock()

    MAP_WIDTH = 50  # Szerokość mapy w kafelkach
    MAP_HEIGHT = 50  # Wysokość mapy w kafelkach

    # Załaduj tło mapy
    grass_tile = pygame.image.load("grass6.png")
    grass_tile = pygame.transform.scale(grass_tile, (TILE_SIZE, TILE_SIZE))
    holy_waters = []  # Lista aktywnych Holy Water

    game_map = generate_map_vampire_style(MAP_WIDTH, MAP_HEIGHT)
    player = Player(10, 10)
    enemies = [Enemy(random.randint(0, MAP_WIDTH - 1), random.randint(0, MAP_HEIGHT - 1), 50, 10) for _ in range(10)]
    camera = Camera(WIDTH, HEIGHT)

    projectiles = []  # Lista pocisków
    minimap_size = (200, 150)  # Rozmiar minimapy

    # Sterowanie liczbą przeciwników
    max_enemies = 10
    spawn_interval = 2000  # Co ile milisekund spawnujemy nowego przeciwnika
    last_spawn_time = pygame.time.get_ticks()

    # Pętla gry
    # Pętla gry
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Sterowanie graczem
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            player.move(0, -1, game_map)
        if keys[pygame.K_DOWN]:
            player.move(0, 1, game_map)
        if keys[pygame.K_LEFT]:
            player.move(-1, 0, game_map)
        if keys[pygame.K_RIGHT]:
            player.move(1, 0, game_map)

        # Strzelanie pociskami
        if keys[pygame.K_w]:
            player.shoot(projectiles, (0, -1))
        if keys[pygame.K_s]:
            player.shoot(projectiles, (0, 1))
        if keys[pygame.K_a]:
            player.shoot(projectiles, (-1, 0))
        if keys[pygame.K_d]:
            player.shoot(projectiles, (1, 0))

        # Rzucanie Holy Water
        if keys[pygame.K_h]:
            player.throw_holy_water(holy_waters)

        # Dodawanie nowego przeciwnika co określony czas
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time >= spawn_interval and len(enemies) < max_enemies:
            last_spawn_time = current_time
            enemies.append(Enemy(random.randint(0, MAP_WIDTH - 1), random.randint(0, MAP_HEIGHT - 1), 50, 10))

        # Aktualizacja pozycji przeciwników
        for enemy in enemies:
            enemy.move_towards_player(player)

        # Ruch pocisków i sprawdzanie kolizji
        for projectile in projectiles[:]:
            projectile.move()  # Pocisk się porusza

            # Sprawdź, czy pocisk jest w granicach mapy
            if not (0 <= projectile.x <= MAP_WIDTH * TILE_SIZE and
                    0 <= projectile.y <= MAP_HEIGHT * TILE_SIZE):
                projectiles.remove(projectile)
                continue

            # Sprawdź kolizję pocisku z przeciwnikiem
            for enemy in enemies[:]:
                enemy_center_x, enemy_center_y = enemy.get_center()
                tolerance = TILE_SIZE // 2  # Tolerancja na trafienie
                if abs(projectile.x - enemy_center_x) <= tolerance and \
                        abs(projectile.y - enemy_center_y) <= tolerance:
                    enemy.take_damage(player.damage)
                    if enemy.hp <= 0:  # Jeśli przeciwnik zginął, usuń go
                        player.gain_exp(20)
                        enemies.remove(enemy)
                    projectiles.remove(projectile)
                    break

        # Kolizja gracza z przeciwnikami
        for enemy in enemies:
            if player.x == enemy.x and player.y == enemy.y:
                if current_time - player.last_damage_time >= 1000:  # Ograniczenie czasu otrzymania obrażeń
                    player.take_damage(enemy.damage)
                    player.last_damage_time = current_time


        # Sprawdzenie, czy gracz zginął
        if player.hp <= 0:
            if show_death_screen():
                return main()  # Restart gry
            else:
                running = False
                break

        # Aktualizacja kamery
        camera.update(player)

        # Rysowanie ekranu
        screen.fill(BLACK)  # Wyczyść ekran

        # Rysowanie mapy w oparciu o kafelki
        draw_map(screen, game_map, camera)

        # Rysowanie obiektów gry
        for enemy in enemies:
            enemy.draw(screen, camera)
        for projectile in projectiles:
            projectile.draw(screen, camera)
        player.draw(screen, camera)

        # Rysowanie minimapy
        minimap_surface = pygame.Surface(minimap_size)
        draw_minimap(minimap_surface, game_map, player, enemies, minimap_size)
        screen.blit(minimap_surface, (WIDTH - minimap_size[0] - 10, 10))

        # Obsługa i rysowanie Holy Water
        for holy_water in holy_waters[:]:
            if holy_water.is_active():  # Sprawdzamy, czy Holy Water nadal działa
                holy_water.draw(screen, camera)  # Rysowanie obiektu Holy Water
                holy_water.check_collision(enemies, player)  # Sprawdzanie kolizji
            else:
                holy_waters.remove(holy_water)  # Usuń, jeśli czas działania upłynął

        Player.draw_xp_bar(screen,player)
        # Aktualizacja wyświetlacza
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    exit()


if __name__ == "__main__":
    main()
