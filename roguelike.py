import pygame
import random

# Inicjalizacja Pygame
pygame.init()

# Stałe
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 32

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

        # Wygląd
        self.color = (0, 255, 0)
        # Doświadczenie
        self.exp = 0
        self.level = 1
        self.next_level_exp = 100

        # Wygląd
        self.color = GREEN

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
        """Wyświetlanie okna dialogowego wyboru nagrody"""
        font = pygame.font.Font(None, 36)
        running = True
        while running:
            screen.fill(BLACK)

            # Wyświetlanie opcji
            text = font.render("Level Up! Choose an upgrade:", True, WHITE)
            dmg_text = font.render("1: Increase Damage (+5)", True, WHITE)
            hp_text = font.render("2: Increase Max HP (+5)", True, WHITE)
            speed_text = font.render("3: Increase Attack Speed (+0.2)", True, WHITE)

            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100))
            screen.blit(dmg_text, (WIDTH // 2 - dmg_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(hp_text, (WIDTH // 2 - hp_text.get_width() // 2, HEIGHT // 2))
            screen.blit(speed_text, (WIDTH // 2 - speed_text.get_width() // 2, HEIGHT // 2 + 50))

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
                    elif event.key == pygame.K_3:
                        self.attack_speed += 0.2
                        running = False

    def shoot(self, projectiles, direction):
        """Strzelanie pociskami w określonym kierunku"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shoot_time >= 500:  # Strzał co 500 ms
            self.last_shoot_time = current_time
            dx, dy = direction
            projectile = Projectile(self.x * TILE_SIZE + TILE_SIZE // 2,
                                    self.y * TILE_SIZE + TILE_SIZE // 2,
                                    dx, dy, 5)
            projectiles.append(projectile)

    def move(self, dx, dy, game_map):
        """Metoda do poruszania się gracza z uwzględnieniem granic mapy i spowolnienia"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time >= 200:  # Ruch co 200 ms
            self.last_move_time = current_time
            new_x = self.x + dx
            new_y = self.y + dy

            # Sprawdzamy, czy nowa pozycja mieści się w granicach mapy
            if 0 <= new_x < len(game_map[0]) and 0 <= new_y < len(game_map):
                self.x = new_x
                self.y = new_y

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

    def draw(self, surface):
        """Rysowanie gracza na ekranie"""
        pygame.draw.rect(surface, self.color, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        # Rysowanie paska HP
        pygame.draw.rect(surface, RED, (self.x * TILE_SIZE, self.y * TILE_SIZE - 10, TILE_SIZE, 5))
        pygame.draw.rect(surface, GREEN, (self.x * TILE_SIZE, self.y * TILE_SIZE - 10, TILE_SIZE * (self.hp / self.max_hp), 5))
        # Rysowanie paska EXP
        pygame.draw.rect(surface, WHITE, (10, HEIGHT - 20, WIDTH - 20, 10))
        pygame.draw.rect(surface, YELLOW, (10, HEIGHT - 20, (WIDTH - 20) * (self.exp / self.next_level_exp), 10))


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

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))



class Projectile:
    def __init__(self, x, y, dx, dy, speed):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.color = (255, 255, 0)  # Żółty kolor dla pocisku
        self.size = 5

    def move(self):
        """Aktualizacja pozycji pocisku"""
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

    def draw(self, surface):
        """Rysowanie pocisku"""
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


def generate_map(width, height):
    return [[random.choice([0, 1]) for _ in range(width)] for _ in range(height)]



def draw_map(surface, game_map):
    for y, row in enumerate(game_map):
        for x, tile in enumerate(row):
            color = GRAY if tile == 1 else BLACK
            pygame.draw.rect(surface, color, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))






# Główna funkcja gry
def main():
    clock = pygame.time.Clock()
    running = True

    # Tworzenie mapy i gracza
    game_map = generate_map(WIDTH // TILE_SIZE, HEIGHT // TILE_SIZE)
    player = Player(5, 5)

    # Tworzenie listy przeciwników i pocisków
    enemies = [Enemy(random.randint(0, WIDTH // TILE_SIZE - 1),
                     random.randint(0, HEIGHT // TILE_SIZE - 1),
                     50, 5) for _ in range(5)]
    projectiles = []

    # Sterowanie liczbą przeciwników
    max_enemies = 5  # Początkowa maksymalna liczba przeciwników
    spawn_interval = 2000  # Nowy przeciwnik co 2 sekundy
    last_spawn_time = pygame.time.get_ticks()
    increase_interval = 4000  # Zwiększenie maksymalnej liczby przeciwników co 4 sekundy
    last_increase_time = pygame.time.get_ticks()

    while running:
        screen.fill(BLACK)

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

        # Dodawanie nowego przeciwnika co 10 sekund
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time >= spawn_interval and len(enemies) < max_enemies:
            last_spawn_time = current_time
            new_enemy = Enemy(random.randint(0, WIDTH // TILE_SIZE - 1),
                              random.randint(0, HEIGHT // TILE_SIZE - 1),
                              50, 5)
            enemies.append(new_enemy)
            print(f"Dodano nowego przeciwnika na pozycji ({new_enemy.x}, {new_enemy.y})")

        # Zwiększanie maksymalnej liczby przeciwników co 20 sekund
        if current_time - last_increase_time >= increase_interval:
            last_increase_time = current_time
            max_enemies += 1
            print(f"Maksymalna liczba przeciwników zwiększona do {max_enemies}")

        # Ruch przeciwników
        for enemy in enemies:
            enemy.move_towards_player(player)

        # Ruch pocisków
        for projectile in projectiles[:]:
            projectile.move()
            # Usuwanie pocisków poza ekranem
            if not (0 <= projectile.x <= WIDTH and 0 <= projectile.y <= HEIGHT):
                projectiles.remove(projectile)

        # Kolizje pocisków z przeciwnikami
        for projectile in projectiles[:]:
            for enemy in enemies:
                if abs(projectile.x - (enemy.x * TILE_SIZE + TILE_SIZE // 2)) < TILE_SIZE // 2 and \
                        abs(projectile.y - (enemy.y * TILE_SIZE + TILE_SIZE // 2)) < TILE_SIZE // 2:
                    enemy.take_damage(player.damage)
                    if enemy.hp <= 0:  # Sprawdzamy, czy przeciwnik zginął
                        player.gain_exp(20)  # EXP za zabicie przeciwnika
                        enemies.remove(enemy)
                    projectiles.remove(projectile)
                    break

        # Kolizje gracza z przeciwnikami
        current_time = pygame.time.get_ticks()
        for enemy in enemies:
            if player.x == enemy.x and player.y == enemy.y:  # Jeśli współrzędne są takie same
                if current_time - player.last_damage_time >= 1000:  # Obrażenia co 1 sekundę
                    player.take_damage(enemy.damage)  # Zadanie obrażeń
                    player.last_damage_time = current_time  # Aktualizacja czasu ostatnich obrażeń
                    print(f"Gracz otrzymał {enemy.damage} obrażeń! HP: {player.hp}/{player.max_hp}")

        # Rysowanie
        draw_map(screen, game_map)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for projectile in projectiles:
            projectile.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()






if __name__ == "__main__":
    main()
