import pygame
import sys
import random
import math
import os

# Initialize Pygame
pygame.init()

# Set up game window
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Pygame Game")

# Grid size
grid_width, grid_height = 10, 10
cell_width, cell_height = screen_width // grid_width, screen_height // grid_height

# Initialize font for score and health
pygame.font.init()
font = pygame.font.Font(None, 36)

# Get the current working directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load and scale images
try:
    background_image = pygame.image.load(os.path.join(current_dir, "images/background.png")).convert()
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
    player_image = pygame.image.load(os.path.join(current_dir, "images/player.png"))
    player_image = pygame.transform.scale(player_image, (cell_width, cell_height))
    enemy_image = pygame.image.load(os.path.join(current_dir, "images/enemy.png"))
    enemy_image = pygame.transform.scale(enemy_image, (cell_width, cell_height))
    bullet_image = pygame.image.load(os.path.join(current_dir, "images/bullet.png"))
    bullet_image = pygame.transform.scale(bullet_image, (10, 10))
    power_up_image = pygame.image.load(os.path.join(current_dir, "images/power_up.png"))
    power_up_image = pygame.transform.scale(power_up_image, (cell_width // 4, cell_height // 4))
    turret_image = pygame.image.load(os.path.join(current_dir, "images/turret.png"))
    turret_image = pygame.transform.scale(turret_image, (cell_width, cell_height))
except pygame.error as e:
    print(f"Error loading images: {e}")
    sys.exit(1)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_image
        self.rect = self.image.get_rect(center=(screen_width / 2, screen_height / 2))
        self.speed = cell_width // 10
        self.health = 100
        self.shotgun_level = 0
        self.shield_level = 0
        self.turret_level = 0
        self.lightning_gun_level = 1  # Assuming starting with level 1 for demonstration
        self.angle = 0

    def update(self, keys):
        if keys[pygame.K_w] and self.rect.y > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_s] and self.rect.y < screen_height - cell_height:
            self.rect.y += self.speed
        if keys[pygame.K_a] and self.rect.x > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_d] and self.rect.x < screen_width - cell_height:
            self.rect.x += self.speed

    def rotate(self, mouse_pos):
        rel_x, rel_y = mouse_pos[0] - self.rect.centerx, mouse_pos[1] - self.rect.centery
        self.angle = (180 / math.pi) * -math.atan2(rel_y, rel_x)
        self.image = pygame.transform.rotate(player_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, damage):
        super().__init__()
        self.image = pygame.transform.rotate(bullet_image, -angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = angle
        self.speed = 20
        self.dx = math.cos(math.radians(angle)) * self.speed
        self.dy = -math.sin(math.radians(angle)) * self.speed
        self.damage = damage

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.right < 0 or self.rect.left > screen_width or self.rect.bottom < 0 or self.rect.top > screen_height:
            self.kill()

class LightningChain:
    def __init__(self, origin_x, origin_y, damage, chain_count, angle):
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.damage = damage
        self.chain_count = chain_count
        self.angle = angle
        self.chained_enemies = []

    def update(self):
        for enemy in enemies:
            if enemy not in self.chained_enemies:
                distance = math.sqrt((enemy.rect.centerx - self.origin_x) ** 2 + (enemy.rect.centery - self.origin_y) ** 2)
                if distance < 200:
                    self.chained_enemies.append(enemy)
                    pygame.draw.line(screen, (255, 255, 255), (self.origin_x, self.origin_y), enemy.rect.center, 2)
                    enemy.take_damage(self.damage)
                    if self.chain_count > 1:
                        new_chain = LightningChain(enemy.rect.centerx, enemy.rect.centery, self.damage, self.chain_count - 1, self.angle)
                        lightning_chains.append(new_chain)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = enemy_image
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 1
        self.health = 50 + (level - 1) * 10

    def update(self):
        dx, dy = player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        dx, dy = dx / distance, dy / distance
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        if self.rect.colliderect(player.rect):
            player.take_damage(1)
            self.kill()

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = power_up_image
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        if self.rect.colliderect(player.rect):
            player.health += 10
            self.kill()

class Turret(pygame.sprite.Sprite):
    def __init__(self, x, y, turret_level, base_shoot_delay):
        super().__init__()
        self.image = turret_image
        self.rect = self.image.get_rect(center=(x, y))
        self.base_shoot_delay = base_shoot_delay
        self.turret_level = turret_level
        self.shoot_delay = self.base_shoot_delay / (1.5 ** self.turret_level)
        self.last_shot_time = 0

    def update(self):
        self.shoot()
        print(f"Turret shoot delay: {self.shoot_delay} ms")

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.shoot_delay:
            self.last_shot_time = current_time
            closest_enemy = self.find_closest_enemy()
            if closest_enemy:
                bullet_damage = 10 + 5 * self.turret_level
                bullet = Bullet(self.rect.centerx, self.rect.centery, self.calculate_angle(closest_enemy), bullet_damage)
                bullets.add(bullet)

    def find_closest_enemy(self):
        closest_enemy = None
        closest_distance = float('inf')
        for enemy in enemies:
            distance = math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
            if distance < closest_distance:
                closest_enemy = enemy
                closest_distance = distance
        return closest_enemy

    def calculate_angle(self, enemy):
        dx = enemy.rect.centerx - self.rect.centerx
        dy = enemy.rect.centery - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx))
        return angle

class PauseButton(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((120, 40))
        self.image.fill((80, 80, 80))
        self.rect = self.image.get_rect(topright=(screen_width - 20, 20))
        self.font = pygame.font.Font(None, 28)
        self.text = "Pause/Shop"
        self.clicked = False

    def update(self):
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.image.get_width() // 2, self.image.get_height() // 2))
        self.image.fill((80, 80, 80))
        self.image.blit(text_surface, text_rect)
        if self.clicked:
            global paused
            paused = not paused
            self.clicked = False

class ShopButton(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((100, 50))
        self.image.fill((100, 100, 255))
        self.rect = self.image.get_rect(center=(screen_width / 2, screen_height - 50))
        self.clicked = False

    def update(self):
        if self.clicked:
            shop_menu()

def shop_menu():
    global score
    shop_running = True
    selected_item = 0
    while shop_running:
        shop_surface = pygame.Surface((400, 600))
        shop_surface.fill((240, 240, 240))
        pygame.draw.rect(shop_surface, (200, 200, 200), shop_surface.get_rect(), 2)

        title_text = font.render("Shop Menu", True, (0, 0, 0))
        shop_surface.blit(title_text, (shop_surface.get_width() // 2 - title_text.get_width() // 2, 20))

        shop_items = [
            {"name": "Blue Glowing Shield", "price": 300, "description": "Activates a protective blue glow", "icon": power_up_image, "level": player.shield_level},
            {"name": "Health Boost", "price": 100, "description": "Increase player health by 50", "icon": power_up_image},
            {"name": "Shotgun Upgrade", "price": 200, "description": "Increase shotgun damage by 50%", "icon": power_up_image, "level": player.shotgun_level},
            {"name": "Turret", "price": 500, "description": "Spawns a turret that automatically shoots enemies", "icon": turret_image, "level": player.turret_level},
            {"name": "Lightning Gun Upgrade", "price": 400, "description": "Increases chain count of lightning bolts", "icon": bullet_image, "level": player.lightning_gun_level}
        ]

        for i, item in enumerate(shop_items):
            item_surface = pygame.Surface((380, 100))
            item_surface.fill((220, 220, 220))
            pygame.draw.rect(item_surface, (200, 200, 200), item_surface.get_rect(), 1)

            item_text = font.render(f"{item['name']}", True, (0, 0, 0))
            item_price = font.render(f"Price: {item['price']}", True, (0, 0, 0))
            item_description = font.render(item['description'], True, (0, 0, 0))

            if "level" in item:
                level_text = font.render(f"Level: {item['level']}", True, (0, 0, 0))
                item_surface.blit(level_text, (item_surface.get_width() // 2 - level_text.get_width() // 2, 60))

            buy_button = pygame.Surface((100, 40))
            buy_button.fill((0, 200, 0))
            buy_text = font.render("Buy", True, (255, 255, 255))
            buy_button.blit(buy_text, (buy_button.get_width() // 2 - buy_text.get_width() // 2, buy_button.get_height() // 2 - buy_text.get_height() // 2))

            item_surface.blit(item['icon'], (20, item_surface.get_height() // 2 - item['icon'].get_height() // 2))
            item_surface.blit(item_text, (item_surface.get_width() // 2 - item_text.get_width() // 2, 10))
            item_surface.blit(item_price, (item_surface.get_width() // 2 - item_price.get_width() // 2, 40))
            item_surface.blit(buy_button, (item_surface.get_width() - 120, item_surface.get_height() // 2 - 20))

            if i == selected_item:
                pygame.draw.rect(item_surface, (255, 255, 0), item_surface.get_rect(), 2)

            shop_surface.blit(item_surface, (10, 120 * i + 60))

        close_button = pygame.Surface((100, 40))
        close_button.fill((200, 0, 0))
        close_text = font.render("Close", True, (255, 255, 255))
        close_button.blit(close_text, (close_button.get_width() // 2 - close_text.get_width() // 2, close_button.get_height() // 2 - close_text.get_height() // 2))
        shop_surface.blit(close_button, (shop_surface.get_width() // 2 - close_button.get_width() // 2, shop_surface.get_height() - 60))

        screen.blit(shop_surface, (screen_width // 2 - 200, screen_height // 2 - 300))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                shop_running = False
                global running
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for i, item in enumerate(shop_items):
                    item_rect = pygame.Rect(screen_width // 2 - 190, screen_height // 2 - 240 + 120 * i, 380, 100)
                    buy_button_rect = pygame.Rect(item_rect.right - 120, item_rect.centery - 20, 100, 40)
                    if buy_button_rect.collidepoint(mouse_pos):
                        if score >= item['price']:
                            score -= item['price']
                            if item['name'] == "Lightning Gun Upgrade":
                                player.lightning_gun_level += 1
                                print(f"Lightning Gun Level: {player.lightning_gun_level}")
                            elif item['name'] == "Blue Glowing Shield":
                                player.shield_level += 1
                                print(f"Shield Level: {player.shield_level}")
                            elif item['name'] == "Health Boost":
                                player.health += 50
                                print(f"Health: {player.health}")
                            elif item['name'] == "Shotgun Upgrade":
                                player.shotgun_level += 1
                                print(f"Shotgun Level: {player.shotgun_level}")
                                for bullet in bullets:
                                    bullet.damage += 10
                            elif item['name'] == "Turret":
                                if len(turrets) < 1:
                                    turret_x = random.randint(50, screen_width - 50)
                                    turret_y = random.randint(50, screen_height - 50)
                                    base_shoot_delay = 1000
                                    turret = Turret(turret_x, turret_y, player.turret_level, base_shoot_delay)
                                    turrets.add(turret)
                                else:
                                    for turret in turrets:
                                        turret.shoot_delay = turret.base_shoot_delay / (1.5 ** player.turret_level)
                                player.turret_level += 1
                                print(f"Turret Level: {player.turret_level}")
                            break
                
                close_button_rect = pygame.Rect(screen_width // 2 - 50, screen_height // 2 + 240, 100, 40)
                if close_button_rect.collidepoint(mouse_pos):
                    shop_running = False

def draw_health_bar(screen, pos, size, borderC, backC, healthC, progress):
    pygame.draw.rect(screen, backC, (*pos, *size))
    pygame.draw.rect(screen, borderC, (*pos, *size), 1)
    innerPos = (pos[0] + 1, pos[1] + 1)
    innerSize = ((size[0] - 2) * progress, size[1] - 2)
    pygame.draw.rect(screen, healthC, (*innerPos, *innerSize))

def draw_player_health_bar():
    health_rect = pygame.Rect(0, 0, 100, 10)
    health_rect.topleft = player.rect.bottomleft
    health_progress = player.health / 100
    draw_health_bar(screen, health_rect.topleft, health_rect.size, (0, 0, 0), (255, 0, 0), (0, 255, 0), health_progress)

def draw_enemy_health_bar(enemy):
    health_rect = pygame.Rect(0, 0, 40, 5)
    health_rect.midbottom = enemy.rect.centerx, enemy.rect.top - 5
    health_progress = enemy.health / (50 + (level - 1) * 10)
    health_width = int(health_rect.width * health_progress)
    health_rect.width = health_width
    draw_health_bar(screen, health_rect.topleft, health_rect.size, (0, 0, 0), (255, 0, 0), 255, 1)

player = Player()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
power_ups = pygame.sprite.Group()
turrets = pygame.sprite.Group()
lightning_chains = []
score = 0
level = 1

def spawn_enemies():
    if len(enemies) < 10:
        x = random.randint(50, screen_width - 50)
        y = random.randint(50, screen_height - 50)
        enemies.add(Enemy(x, y))

def spawn_power_ups():
    if len(power_ups) < 2:
        x = random.randint(50, screen_width - 50)
        y = random.randint(50, screen_height - 50)
        power_ups.add(PowerUp(x, y))

running = True
paused = False
shop_button = ShopButton()
pause_button = PauseButton()
background = pygame.transform.scale(background_image, (screen_width, screen_height))

while running:
    spawn_enemies()
    spawn_power_ups()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not paused:
                if player.lightning_gun_level > 0:
                    for i in range(3 + player.shotgun_level):
                        bullet_angle = player.angle + (i - 2 - player.shotgun_level // 2) * 10
                        bullet = Bullet(player.rect.centerx, player.rect.centery, bullet_angle, 10 + 5 * player.shotgun_level)
                        bullets.add(bullet)
                        lightning_chain = LightningChain(player.rect.centerx, player.rect.centery, 10 + 5 * player.shotgun_level, player.lightning_gun_level, bullet_angle)
                        lightning_chains.append(lightning_chain)
                else:
                    bullet = Bullet(player.rect.centerx, player.rect.centery, player.angle, 10)
                    bullets.add(bullet)
            if pause_button.rect.collidepoint(event.pos):
                pause_button.clicked = True
            if shop_button.rect.collidepoint(event.pos):
                shop_button.clicked = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
                if paused:
                    shop_menu()

    screen.blit(background, (0, 0))

    if not paused:
        keys = pygame.key.get_pressed()
        player.update(keys)
        player.rotate(pygame.mouse.get_pos())
        screen.blit(player.image, player.rect)
        draw_player_health_bar()

        enemies.update()
        for enemy in enemies:
            screen.blit(enemy.image, enemy.rect)
            draw_enemy_health_bar(enemy)

        bullets.update()
        for bullet in bullets:
            screen.blit(bullet.image, bullet.rect)

        hits = pygame.sprite.groupcollide(bullets, enemies, True, False)
        for enemy_list in hits.values():
            for enemy in enemy_list:
                enemy.take_damage(bullet.damage)
                score += 10
                if score % 500 == 0:
                    level += 1

        collided_enemies = pygame.sprite.spritecollide(player, enemies, False)
        for enemy in collided_enemies:
            player.take_damage(1)
            enemy.kill()

        power_ups.update()
        for power_up in power_ups:
            screen.blit(power_up.image, power_up.rect)

        if player.shield_level > 0:
            pygame.draw.circle(screen, (0, 0, 255), (player.rect.centerx, player.rect.centery), 60 * player.shield_level, 5)

        turrets.update()
        for turret in turrets:
            screen.blit(turret.image, turret.rect)

        for chain in lightning_chains:
            chain.update()

        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        health_text = font.render(f"Health: {player.health}", True, (255, 255, 255))
        level_text = font.render(f"Level: {level}", True, (255, 255, 255))

        power_up_text = ""
        if player.shotgun_level > 0:
            power_up_text += f"Shotgun Level: {player.shotgun_level}\n"
        if player.turret_level > 0:
            power_up_text += f"Turret Level: {player.turret_level}\n"

        text_box_surface = pygame.Surface((200, 200))
        text_box_surface.fill((30, 30, 30))
        text_box_surface.set_alpha(180)

        text_box_surface.blit(score_text, (10, 10))
        text_box_surface.blit(health_text, (10, 50))
        text_box_surface.blit(level_text, (10, 90))
        text_box_surface.blit(font.render(power_up_text, True, (255, 255, 255)), (10, 130))

        pygame.draw.rect(text_box_surface, (200, 200, 200), text_box_surface.get_rect(), 2)
        screen.blit(text_box_surface, (10, 10))

    pause_button.update()
    screen.blit(pause_button.image, pause_button.rect)

    if paused:
        paused_text = font.render("Paused", True, (255, 255, 255))
        screen.blit(paused_text, (screen_width / 2 - 50, screen_height / 2))
        shop_button.update()
        screen.blit(shop_button.image, shop_button.rect)
        if shop_button.clicked:
            shop_button.clicked = False

    pygame.display.flip()
    pygame.time.Clock().tick(60)

pygame.quit()
sys.exit()
