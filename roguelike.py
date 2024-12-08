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
        self.inventory = {"weapons": [], "shield": None}  # Ekwipunek gracza
        self.equipped_weapon = None  # Aktualnie wyposażona broń
        self.quest_target = random.randint(5, 15)  # Liczba nietoperzy do pokonania
        self.quest_progress = 0  # Postęp w aktualnym zadaniu
        self.bats_defeated = 0

        # Doświadczenie
        self.exp = 0
        self.bats_defeated = 0
        self.level = 1
        self.next_level_exp = 100

        # Rozmiar docelowy dla wszystkich obrazów
        self.target_size = (TILE_SIZE * 2, TILE_SIZE * 2)

        # Animacja chodzenia
        self.walk_frames = [
            pygame.transform.scale(
                pygame.image.load(f"walk{i}.png").convert_alpha(), self.target_size
            )
            for i in range(1, 7)
        ]
        self.current_frame = 0
        self.image = self.walk_frames[0]  # Początkowy obraz
        self.animation_speed = 100  # Prędkość zmiany klatek (ms)
        self.last_frame_time = pygame.time.get_ticks()
        self.facing_left = False

        # Obraz w stanie bezruchu
        self.idle_image = pygame.transform.scale(
            pygame.image.load("idle.png").convert_alpha(), self.target_size
        )

    def update_animation(self, moving):
        """Aktualizuje animację gracza."""
        if moving:  # Animacja chodzenia
            current_time = pygame.time.get_ticks()
            if current_time - self.last_frame_time > 150:  # Czas między klatkami
                self.last_frame_time = current_time
                self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
            self.image = self.walk_frames[self.current_frame]
        else:  # Obraz w stanie bezruchu
            self.image = self.idle_image

        # Obrót w zależności od kierunku
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

    def move(self, dx, dy, game_map):
        """Ruch gracza."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time >= self.move_delay:
            new_x = self.x + dx
            new_y = self.y + dy

            if 0 <= new_x < len(game_map[0]) and 0 <= new_y < len(game_map):
                self.x = new_x
                self.y = new_y
                self.moving = True  # Gracz się porusza
            else:
                self.moving = False  # Gracz nie porusza się

            self.facing_left = dx < 0  # Aktualizacja kierunku patrzenia
            self.last_move_time = current_time
        else:
            self.moving = False  # Gracz nie porusza się

    def pick_item(self, items):
        """Zbieranie przedmiotu."""
        for item in items[:]:
            if self.x == item.x and self.y == item.y:
                if item.item_type.startswith("weapon"):
                    weapon_names = {
                        "weapon1": "wooden sword",
                        "weapon2": "bronze sword",
                        "weapon3": "silver sword"
                    }
                    weapon_name = weapon_names.get(item.item_type, item.item_type)
                    if weapon_name not in self.inventory["weapons"]:
                        self.inventory["weapons"].append(weapon_name)
                    print(f"Picked up weapon: {weapon_name}")
                elif item.item_type == "shield1":
                    self.inventory["shield"] = "basic shield"
                    self.apply_shield_effect()
                    print(f"Picked up shield: basic shield")
                items.remove(item)

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

    def apply_weapon_effect(self):
        """Zastosowanie efektu wybranej broni."""
        # Mapowanie nazw broni na bonusy
        weapon_bonuses = {
            "wooden sword": 5,
            "bronze sword": 10,
            "silver sword": 15,
        }

        # Odejmij bonus poprzedniej broni
        if hasattr(self, 'previous_weapon') and self.previous_weapon in weapon_bonuses:
            self.damage -= weapon_bonuses[self.previous_weapon]

        # Dodaj bonus dla aktualnie wyposażonej broni
        if self.equipped_weapon in weapon_bonuses:
            self.damage += weapon_bonuses[self.equipped_weapon]

        # Zaktualizuj poprzednią broń
        self.previous_weapon = self.equipped_weapon

        print(f"Wybrano broń: {self.equipped_weapon}, obrażenia gracza: {self.damage}")

    def apply_shield_effect(self):
        """Zastosowanie efektu tarczy."""
        if self.inventory['shield'] == "basic shield":
            self.defense = 2  # Przykładowa wartość obrony dla tarczy
        else:
            self.defense = 0  # Brak tarczy oznacza brak bonusu obrony
        print(f"Obrona gracza została ustawiona na: {self.defense}")

    def draw_inventory(self, surface):
        """Rysowanie ekwipunku gracza w lewym górnym rogu ekranu z obrazkami."""
        font = pygame.font.Font(None, 24)
        x = 10  # Punkt początkowy blisko lewej krawędzi
        y = 10  # Punkt początkowy blisko górnej krawędzi

        # Mapowanie broni na pliki graficzne
        weapon_images = {
            "wooden sword": "weapon1.png",
            "bronze sword": "weapon2.png",
            "silver sword": "weapon3.png",
        }

        # Wyświetl bronie
        for weapon in self.inventory["weapons"]:
            weapon_text = font.render(weapon, True, WHITE)
            weapon_file = weapon_images.get(weapon)  # Pobierz nazwę pliku
            if weapon_file:
                weapon_img = pygame.image.load(weapon_file).convert_alpha()
                weapon_img = pygame.transform.scale(weapon_img, (32, 32))
                surface.blit(weapon_img, (x, y))
            surface.blit(weapon_text, (x + 40, y + 5))
            y += 40

        # Wyświetl aktualnie wyposażoną broń
        if self.equipped_weapon:
            equipped_text = font.render(f"Equipped: {self.equipped_weapon}", True, WHITE)
            surface.blit(equipped_text, (x, y))
            y += 30  # Przesuń na kolejną linię

        # Wyświetl tarczę
        if self.inventory["shield"]:
            shield_text = font.render(f"Shield: {self.inventory['shield']}", True, WHITE)
            shield_img = pygame.image.load("shield1.png").convert_alpha()
            shield_img = pygame.transform.scale(shield_img, (32, 32))
            surface.blit(shield_img, (x, y))
            surface.blit(shield_text, (x + 40, y + 5))

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

    def check_quest_completion(self):
        """Sprawdzanie, czy zadanie zostało ukończone."""
        if self.quest_progress >= self.quest_target:
            print(f"Quest completed! Defeat {self.quest_target} bats.")
            self.gain_exp(self.next_level_exp // 2)  # Dodaj 50% punktów do kolejnego poziomu
            self.quest_target = random.randint(5, 15)  # Nowy cel
            self.quest_progress = 0  # Zresetuj postęp
            print(f"New quest: Defeat {self.quest_target} bats!")

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

    def draw_quest_status(self, surface, minimap_x, minimap_y, minimap_width, minimap_height):
        """Rysowanie statusu zadania pod minimapą w prawym górnym rogu."""
        font = pygame.font.Font(None, 24)
        quest_x = minimap_x  # Pozycja X zgodna z minimapą
        quest_y = minimap_y + minimap_height + 10  # Pozycja Y poniżej minimapy

        quest_text = font.render(f"Quest: Defeat {self.quest_progress}/{self.quest_target} bats", True, WHITE)
        surface.blit(quest_text, (quest_x, quest_y))

    def shoot(self, projectiles, direction):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shoot_time >= 500:  # Strzał co 500 ms
            self.last_shoot_time = current_time
            dx, dy = direction

            # Ustaw kierunek patrzenia postaci na podstawie strzału
            if dx < 0:  # Strzał w lewo
                self.facing_left = True
            elif dx > 0:  # Strzał w prawo
                self.facing_left = False

            # Początkowa pozycja pocisku: środek gracza
            projectile_x = self.x * TILE_SIZE + TILE_SIZE * 2 // 2
            projectile_y = self.y * TILE_SIZE + TILE_SIZE * 2 // 2

            # Tworzenie pocisku
            projectile = Projectile(projectile_x, projectile_y, dx, dy, speed=10)
            projectiles.append(projectile)


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


    def draw(self, surface, camera):
        # Przekształć pozycję gracza w pozycję względem kamery
        screen_x, screen_y = camera.apply(self.x, self.y)

        # Rysuj obraz gracza
        surface.blit(self.image, (screen_x, screen_y))

        # Rysowanie paska HP nad postacią
        pygame.draw.rect(surface, RED, (screen_x, screen_y - 10, TILE_SIZE * 2, 5))
        pygame.draw.rect(surface, GREEN, (screen_x, screen_y - 10, TILE_SIZE * 2 * (self.hp / self.max_hp), 5))

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
                enemy.take_damage(self.damage, player)  # Dodano przekazanie player
                if enemy.hp <= 0:  # Jeśli przeciwnik zginął
                    enemies.remove(enemy)  # Usuń przeciwnika z listy
                    player.gain_exp(20)  # Przyznaj doświadczenie graczowi
                    player.quest_progress += 1  # Zwiększ postęp zadania
                    player.check_quest_completion()  # Sprawdź, czy zadanie jest ukończone

class ExplosiveBlock:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_active = True
        self.explosion_time = None  # Czas rozpoczęcia eksplozji
        self.explosion_duration = 1000  # Czas trwania eksplozji w ms
        self.explosion_tiles = []  # Pola objęte eksplozją

        # Załaduj obrazek bloku wybuchającego
        self.block_image = pygame.image.load("explo.png").convert_alpha()
        self.block_image = pygame.transform.scale(self.block_image, (TILE_SIZE, TILE_SIZE))

        # Załaduj obrazek eksplozji
        self.explosion_image = pygame.image.load("explo2.png").convert_alpha()
        self.explosion_image = pygame.transform.scale(self.explosion_image, (TILE_SIZE, TILE_SIZE))

    def draw(self, surface, camera):
        if self.is_active:
            # Rysuj blok, jeśli jest aktywny
            screen_x, screen_y = camera.apply(self.x, self.y)
            surface.blit(self.block_image, (screen_x, screen_y))
        elif self.explosion_time:
            # Rysuj eksplozję, jeśli została zainicjowana
            current_time = pygame.time.get_ticks()
            if current_time - self.explosion_time <= self.explosion_duration:
                for tile in self.explosion_tiles:
                    screen_x, screen_y = camera.apply(tile[0], tile[1])
                    surface.blit(self.explosion_image, (screen_x, screen_y))

    def explode(self, enemies, player):
        if not self.is_active:
            return

        self.is_active = False
        self.explosion_time = pygame.time.get_ticks()  # Zapisz czas rozpoczęcia eksplozji
        explosion_range = 5

        # Określ pola objęte eksplozją
        self.explosion_tiles = [
            (self.x + dx, self.y + dy)
            for dx in range(-explosion_range, explosion_range + 1)
            for dy in range(-explosion_range, explosion_range + 1)
            if 0 <= self.x + dx < MAP_WIDTH and 0 <= self.y + dy < MAP_HEIGHT
        ]

        for enemy in enemies[:]:
            if (enemy.x, enemy.y) in self.explosion_tiles:
                enemy.take_damage(50, player)  # Przekazanie player jako argument
                if enemy.hp <= 0:
                    enemies.remove(enemy)
                    player.gain_exp(20)
                    player.quest_progress += 1  # Zwiększ postęp zadania
                    player.check_quest_completion()  # Sprawdź, czy zadanie jest ukończone

    def update(self):
        """Sprawdź, czy eksplozja się zakończyła."""
        if self.explosion_time:
            current_time = pygame.time.get_ticks()
            if current_time - self.explosion_time > self.explosion_duration:
                self.explosion_time = None  # Eksplozja zakończona

class Enemy:
    def __init__(self, x, y, hp, damage):
        self.x = x
        self.y = y
        self.hp = hp
        self.damage = damage
        self.move_delay = 500  # Czas między ruchami w ms
        self.last_move_time = pygame.time.get_ticks()
        self.respawn_delay = random.randint(1000, 3000)
        self.last_respawn_time = pygame.time.get_ticks()
        self.is_dead = False  # Czy przeciwnik jest martwy
        self.drop_chance = 1  # Szansa na zrzucenie przedmiotu (30%)

        # Rozmiar docelowy dla wszystkich klatek animacji
        self.target_size = (TILE_SIZE * 2, TILE_SIZE * 2)

        # Animacja chodzenia
        self.walk_frames = [
            pygame.transform.scale(
                pygame.image.load(f"enemywalk{i}.png").convert_alpha(), self.target_size
            )
            for i in range(1, 4)  # enemywalk1.png, enemywalk2.png, enemywalk3.png
        ]
        self.current_frame = 0
        self.image = self.walk_frames[0]  # Początkowy ,obraz
        self.animation_speed = 100  # Czas między klatkami w ms
        self.last_frame_time = pygame.time.get_ticks()

    def drop_item(self, items):
        """Losowanie i dodawanie przedmiotu po śmierci."""
        print(f"Przeciwnik zginął na pozycji ({self.x}, {self.y})")
        if random.random() < self.drop_chance:
            item_type = random.choice(["weapon1", "weapon2", "weapon3", "shield1"])
            items.append(Item(self.x, self.y, item_type))
            print(f"Przedmiot {item_type} został zrzucony na pozycji ({self.x}, {self.y})")
    def update_animation(self):
        """Aktualizuje animację przeciwnika."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_time >= self.animation_speed:
            self.last_frame_time = current_time
            self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
            self.image = self.walk_frames[self.current_frame]

    def move_towards_player(self, player):
        """Poruszanie się przeciwnika w kierunku gracza."""
        if self.is_dead:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time >= self.move_delay:
            self.last_move_time = current_time
            dx = player.x - self.x
            dy = player.y - self.y

            if abs(dx) > abs(dy):
                self.x += 1 if dx > 0 else -1
            else:
                self.y += 1 if dy > 0 else -1

    def take_damage(self, damage, player):
        """Otrzymanie obrażeń"""
        if self.is_dead:
            return  # Martwy przeciwnik nie otrzymuje obrażeń

        self.hp -= damage
        print(f"Przeciwnik otrzymał {damage} obrażeń. Pozostało HP: {self.hp}")
        if self.hp <= 0:
            self.is_dead = True  # Oznacz jako martwego
            self.last_respawn_time = pygame.time.get_ticks()  # Ustaw czas "śmierci"
            player.bats_defeated += 1  # Zwiększ licznik pokonanych nietoperzy
            print(f"Przeciwnik zginął! Liczba pokonanych nietoperzy: {player.bats_defeated}")

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
        self.update_animation()  # Aktualizuj animację przed rysowaniem
        screen_x, screen_y = camera.apply(self.x, self.y)
        surface.blit(self.image, (screen_x, screen_y))


class Item:
    def __init__(self, x, y, item_type):
        self.x = x  # Pozycja na mapie (w kratkach)
        self.y = y
        self.item_type = item_type  # Typ przedmiotu, np. "weapon1", "shield1"
        # Ładowanie obrazu na podstawie typu
        self.image = pygame.image.load(f"{item_type}.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))

    def draw(self, surface, camera):
        """Rysowanie przedmiotu na mapie."""
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

def draw_map(surface, game_map, camera):
    # Załaduj obraz tła i przeskaluj go do rozmiarów całej mapy
    grass_tile = pygame.image.load("grass6.png").convert_alpha()
    grass_tile = pygame.transform.scale(grass_tile, (MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))

    # Oblicz przesunięcie kamery i wyświetl odpowiedni fragment tła
    screen_x = -camera.x_offset
    screen_y = -camera.y_offset
    surface.blit(grass_tile, (screen_x, screen_y))



def draw_minimap(surface, game_map, player, enemies, minimap_size, x, y):
    """Rysowanie minimapy w określonym miejscu na ekranie."""
    if not game_map or not game_map[0]:  # Jeśli mapa jest pusta, nie rysujemy
        return

    minimap_width, minimap_height = minimap_size
    map_width = len(game_map[0])
    map_height = len(game_map)

    # Skalowanie kratki na minimapie
    tile_width = minimap_width // map_width
    tile_height = minimap_height // map_height

    # Rysowanie mapy
    for row_y, row in enumerate(game_map):
        for col_x, tile in enumerate(row):
            color = GRAY if tile == 1 else BLACK
            pygame.draw.rect(surface, color,
                             (x + col_x * tile_width, y + row_y * tile_height, tile_width, tile_height))

    # Rysowanie gracza na minimapie
    pygame.draw.rect(surface, GREEN,
                     (x + player.x * tile_width, y + player.y * tile_height, tile_width, tile_height))

    # Rysowanie przeciwników na minimapie
    for enemy in enemies:
        if not enemy.is_dead:  # Tylko żywi przeciwnicy
            pygame.draw.rect(surface, RED,
                             (x + enemy.x * tile_width, y + enemy.y * tile_height, tile_width, tile_height))

    # Obramowanie minimapy
    pygame.draw.rect(surface, WHITE, (x, y, minimap_width, minimap_height), 2)



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


def show_weapon_selection(self):
    """Wyświetla interfejs wyboru broni."""
    font = pygame.font.Font(None, 36)
    running = True
    while running:
        screen.fill(BLACK)

        # Nagłówek
        header_text = font.render("Choose your weapon:", True, WHITE)
        screen.blit(header_text, (WIDTH // 2 - header_text.get_width() // 2, HEIGHT // 2 - 100))

        # Wyświetlanie broni
        for i, weapon in enumerate(self.inventory["weapons"]):
            weapon_text = font.render(f"{i + 1}: {weapon}", True, WHITE)
            screen.blit(weapon_text, (WIDTH // 2 - weapon_text.get_width() // 2, HEIGHT // 2 - 50 + i * 30))

        # Opcja wyjścia
        exit_text = font.render("0: Exit selection", True, WHITE)
        screen.blit(exit_text, (WIDTH // 2 - exit_text.get_width() // 2, HEIGHT // 2 + 50 + len(self.inventory["weapons"]) * 30))

        pygame.display.flip()

        # Obsługa zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_0:
                    running = False
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    if 0 <= index < len(self.inventory["weapons"]):
                        self.equipped_weapon = self.inventory["weapons"][index]
                        self.apply_weapon_effect()
                        print(f"Wybrana broń: {self.equipped_weapon}")
                        running = False





# Główna funkcja gry
def main():
    clock = pygame.time.Clock()
    last_block_bats_defeated = 0  # Śledzenie liczby pokonanych nietoperzy przy ostatnim dodaniu bloku

    MAP_WIDTH = 50  # Szerokość mapy w kafelkach
    MAP_HEIGHT = 50  # Wysokość mapy w kafelkach

    # Załaduj tło mapy
    grass_tile = pygame.image.load("grass6.png")
    grass_tile = pygame.transform.scale(grass_tile, (TILE_SIZE, TILE_SIZE))
    holy_waters = []  # Lista aktywnych Holy Water
    blocks = []

    game_map = generate_map_vampire_style(MAP_WIDTH, MAP_HEIGHT)
    player = Player(10, 10)
    enemies = [Enemy(random.randint(0, MAP_WIDTH - 1), random.randint(0, MAP_HEIGHT - 1), 50, 10) for _ in range(10)]
    camera = Camera(WIDTH, HEIGHT)

    projectiles = []  # Lista pocisków
    minimap_size = (200, 150)  # Rozmiar minimapy
    items = []

    # Sterowanie liczbą przeciwników
    max_enemies = 10
    spawn_interval = 2000  # Co ile milisekund spawnujemy nowego przeciwnika
    last_spawn_time = pygame.time.get_ticks()

    # Pętla gry
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


        # Sterowanie graczem
        moving = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            player.move(0, -1, game_map)
            moving = True
        if keys[pygame.K_DOWN]:
            player.move(0, 1, game_map)
            moving = True
        if keys[pygame.K_LEFT]:
            player.move(-1, 0, game_map)
            moving = True
        if keys[pygame.K_RIGHT]:
            player.move(1, 0, game_map)
            moving = True
        if keys[pygame.K_i]:
            show_weapon_selection(player)

        player.update_animation(moving)

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

        player.pick_item(items)

        # Aktualizacja pozycji przeciwników
        for enemy in enemies[:]:  # Iterujemy po kopii listy
            enemy.move_towards_player(player)
            if enemy.hp <= 0 and not enemy.is_dead:  # Sprawdzanie śmierci przeciwnika
                enemy.is_dead = True
                player.bats_defeated += 1

        # Ruch pocisków i sprawdzanie kolizji
        for projectile in projectiles[:]:
            projectile.move()  # Pocisk się porusza

            for block in blocks:
                if block.is_active and projectile.x // TILE_SIZE == block.x and projectile.y // TILE_SIZE == block.y:
                    block.explode(enemies, player)  # Wywołanie eksplozji
                    projectiles.remove(projectile)
                    break

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
                    enemy.take_damage(player.damage, player)  # Dodano przekazanie player
                    if enemy.hp <= 0:  # Jeśli przeciwnik zginął, usuń go
                        player.gain_exp(20)
                        enemy.drop_item(items)  # Zrzucanie przedmiotu
                        print(f"Aktualna lista przedmiotów: {[item.item_type for item in items]}")
                        enemies.remove(enemy)  # Usuwamy przeciwnika z listy
                        player.quest_progress += 1  # Zwiększ postęp zadania
                        player.check_quest_completion()
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

        for item in items:
            item.draw(screen, camera)

        for enemy in enemies:
            enemy.draw(screen, camera)

        if player.bats_defeated % 5 == 0 and player.bats_defeated > last_block_bats_defeated:
            blocks.append(ExplosiveBlock(random.randint(1, MAP_WIDTH - 2), random.randint(1, MAP_HEIGHT - 2)))
            last_block_bats_defeated = player.bats_defeated  # Aktualizacja liczby pokonanych nietoperzy

        # Rysowanie obiektów gry
        for enemy in enemies:
            enemy.draw(screen, camera)
        for projectile in projectiles:
            projectile.draw(screen, camera)
        player.draw(screen, camera)

        # Obsługa i rysowanie Holy Water
        for holy_water in holy_waters[:]:
            if holy_water.is_active():  # Sprawdzamy, czy Holy Water nadal działa
                holy_water.draw(screen, camera)  # Rysowanie obiektu Holy Water
                holy_water.check_collision(enemies, player)  # Sprawdzanie kolizji
            else:
                holy_waters.remove(holy_water)  # Usuń, jeśli czas działania upłynął

        Player.draw_xp_bar(screen,player)
        player.draw_inventory(screen)
        minimap_x = WIDTH - minimap_size[0] - 10
        minimap_y = 10
        draw_minimap(screen, game_map, player, enemies, minimap_size, minimap_x, minimap_y)

        player.draw_quest_status(screen, minimap_x, minimap_y, minimap_size[0], minimap_size[1])

        for block in blocks[:]:
            block.update()
            block.draw(screen, camera)

        # Aktualizacja wyświetlacza
        pygame.display.flip()
        clock.tick(60)
        print(blocks)

    pygame.quit()
    exit()


if __name__ == "__main__":
    main()
