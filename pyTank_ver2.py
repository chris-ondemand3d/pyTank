import pygame
import Box2D
from Box2D import b2World, b2PolygonShape, b2CircleShape, b2FixtureDef, b2BodyDef, b2_dynamicBody, b2_staticBody
import math
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PPM = 30.0  # Pixels per meter
TARGET_FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tank Artillery Game")
        self.clock = pygame.time.Clock()
        
        # Create Box2D world
        self.world = b2World(gravity=(0, -10), doSleep=True)
        
        # Game objects
        self.tank = None
        self.target = None
        self.projectiles = []
        self.mountain = None
        
        # Tank properties
        self.tank_angle = 0  # Artillery angle in degrees
        self.tank_speed = 5
        
        # Power gauge properties
        self.space_press_time = 0
        self.space_pressed = False
        self.min_power = 10
        self.max_power = 40
        self.power_charge_rate = 15  # Power increase per second
        
        self.setup_world()
        
    def setup_world(self):
        # Create mountain (static body)
        mountain_vertices = [
            (SCREEN_WIDTH/2/PPM - 100/PPM, 0),
            (SCREEN_WIDTH/2/PPM + 100/PPM, 0),
            (SCREEN_WIDTH/2/PPM + 50/PPM, 150/PPM),
            (SCREEN_WIDTH/2/PPM - 50/PPM, 150/PPM)
        ]
        
        mountain_body = self.world.CreateStaticBody(
            position=(0, 0),
            shapes=b2PolygonShape(vertices=mountain_vertices)
        )
        self.mountain = mountain_body
        
        # Create ground
        ground_body = self.world.CreateStaticBody(
            position=(0, -10/PPM),
            shapes=b2PolygonShape(box=(SCREEN_WIDTH/PPM, 10/PPM))
        )
        
        # Create tank (dynamic body)
        tank_x = 150/PPM
        tank_y = 50/PPM
        
        self.tank = self.world.CreateDynamicBody(
            position=(tank_x, tank_y),
            shapes=b2PolygonShape(box=(20/PPM, 10/PPM)),
            fixedRotation=True
        )
        self.tank.userData = "tank"
        
        # Create target
        self.spawn_new_target()
        
    def spawn_new_target(self):
        if self.target:
            self.world.DestroyBody(self.target)
            
        # Random position on the right side
        target_x = random.uniform(SCREEN_WIDTH*0.75/PPM, SCREEN_WIDTH*0.95/PPM)
        target_y = random.uniform(50/PPM, 200/PPM)
        
        self.target = self.world.CreateDynamicBody(
            position=(target_x, target_y),
            shapes=b2PolygonShape(box=(15/PPM, 15/PPM))
        )
        self.target.userData = "target"
        
    def create_projectile(self, power):
        # Create projectile at tank position
        tank_pos = self.tank.position
        projectile_x = tank_pos.x + 25/PPM * math.cos(math.radians(self.tank_angle))
        projectile_y = tank_pos.y + 25/PPM * math.sin(math.radians(self.tank_angle))
        
        projectile = self.world.CreateDynamicBody(
            position=(projectile_x, projectile_y),
            shapes=b2CircleShape(radius=3/PPM)
        )
        
        # Set projectile velocity based on power
        vel_x = power * math.cos(math.radians(self.tank_angle))
        vel_y = power * math.sin(math.radians(self.tank_angle))
        projectile.linearVelocity = (vel_x, vel_y)
        
        projectile.userData = "projectile"
        self.projectiles.append(projectile)
        
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Tank movement
        if keys[pygame.K_LEFT]:
            # Move backward
            current_vel = self.tank.linearVelocity
            self.tank.linearVelocity = (-self.tank_speed, current_vel.y)
        elif keys[pygame.K_RIGHT]:
            # Move forward
            current_vel = self.tank.linearVelocity
            self.tank.linearVelocity = (self.tank_speed, current_vel.y)
        else:
            # Stop horizontal movement
            current_vel = self.tank.linearVelocity
            self.tank.linearVelocity = (0, current_vel.y)
            
        # Artillery angle adjustment
        if keys[pygame.K_UP]:
            self.tank_angle = min(90, self.tank_angle + 2)
        elif keys[pygame.K_DOWN]:
            self.tank_angle = max(-90, self.tank_angle - 2)
            
    def update(self):
        # Update power gauge if space is being held
        if self.space_pressed:
            self.space_press_time += 1.0/TARGET_FPS
        
        # Step the physics world
        self.world.Step(1.0/TARGET_FPS, 6, 2)
        
        # Check for collisions and remove old projectiles
        for projectile in self.projectiles[:]:
            # Check if projectile is out of bounds
            pos = projectile.position
            if (pos.x < -50/PPM or pos.x > (SCREEN_WIDTH + 50)/PPM or 
                pos.y < -50/PPM or pos.y > (SCREEN_HEIGHT + 50)/PPM):
                self.world.DestroyBody(projectile)
                self.projectiles.remove(projectile)
                continue
                
            # Check collision with target
            if self.check_collision(projectile, self.target):
                self.world.DestroyBody(projectile)
                self.projectiles.remove(projectile)
                self.spawn_new_target()  # Spawn new target
                
    def check_collision(self, body1, body2):
        # Simple distance-based collision detection
        pos1 = body1.position
        pos2 = body2.position
        distance = math.sqrt((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)
        return distance < 30/PPM  # Collision threshold
        
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw mountain
        mountain_vertices = [
            (SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT - 0),
            (SCREEN_WIDTH/2 + 100, SCREEN_HEIGHT - 0),
            (SCREEN_WIDTH/2 + 50, SCREEN_HEIGHT - 150),
            (SCREEN_WIDTH/2 - 50, SCREEN_HEIGHT - 150)
        ]
        pygame.draw.polygon(self.screen, BROWN, mountain_vertices)
        
        # Draw ground
        pygame.draw.rect(self.screen, GREEN, 
                        (0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10))
        
        # Draw tank
        tank_pos = self.tank.position
        tank_screen_x = int(tank_pos.x * PPM)
        tank_screen_y = int(SCREEN_HEIGHT - tank_pos.y * PPM)
        
        # Tank body
        pygame.draw.rect(self.screen, GRAY,
                        (tank_screen_x - 20, tank_screen_y - 10, 40, 20))
        
        # Tank barrel
        barrel_length = 30
        barrel_end_x = tank_screen_x + barrel_length * math.cos(math.radians(self.tank_angle))
        barrel_end_y = tank_screen_y - barrel_length * math.sin(math.radians(self.tank_angle))
        pygame.draw.line(self.screen, GRAY, 
                        (tank_screen_x, tank_screen_y), 
                        (int(barrel_end_x), int(barrel_end_y)), 5)
        
        # Draw target
        target_pos = self.target.position
        target_screen_x = int(target_pos.x * PPM)
        target_screen_y = int(SCREEN_HEIGHT - target_pos.y * PPM)
        pygame.draw.rect(self.screen, RED,
                        (target_screen_x - 15, target_screen_y - 15, 30, 30))
        
        # Draw projectiles
        for projectile in self.projectiles:
            proj_pos = projectile.position
            proj_screen_x = int(proj_pos.x * PPM)
            proj_screen_y = int(SCREEN_HEIGHT - proj_pos.y * PPM)
            pygame.draw.circle(self.screen, YELLOW, 
                             (proj_screen_x, proj_screen_y), 3)
        
        # Draw UI
        font = pygame.font.Font(None, 36)
        angle_text = font.render(f"Artillery Angle: {self.tank_angle}°", True, WHITE)
        self.screen.blit(angle_text, (10, 10))
        
        # Draw power gauge
        if self.space_pressed:
            current_power = min(self.max_power, self.min_power + self.space_press_time * self.power_charge_rate)
            power_percentage = (current_power - self.min_power) / (self.max_power - self.min_power)
            
            # Power gauge background
            gauge_rect = pygame.Rect(10, 50, 200, 20)
            pygame.draw.rect(self.screen, WHITE, gauge_rect, 2)
            
            # Power gauge fill
            fill_width = int(196 * power_percentage)
            fill_rect = pygame.Rect(12, 52, fill_width, 16)
            
            # Color based on power level
            if power_percentage < 0.3:
                gauge_color = GREEN
            elif power_percentage < 0.7:
                gauge_color = YELLOW
            else:
                gauge_color = RED
                
            pygame.draw.rect(self.screen, gauge_color, fill_rect)
            
            # Power text
            power_text = font.render(f"Power: {current_power:.1f}", True, WHITE)
            self.screen.blit(power_text, (220, 50))
        
        instructions = [
            "Controls:",
            "Left/Right Arrow: Move tank",
            "Up/Down Arrow: Adjust artillery angle",
            "Hold Space: Charge power, Release to fire"
        ]
        
        small_font = pygame.font.Font(None, 24)
        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, WHITE)
            self.screen.blit(text, (10, 90 + i * 25))
        
        pygame.display.flip()
        
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.space_pressed:
                        self.space_pressed = True
                        self.space_press_time = 0
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE and self.space_pressed:
                        # Calculate power based on hold duration
                        current_power = min(self.max_power, self.min_power + self.space_press_time * self.power_charge_rate)
                        self.create_projectile(current_power)
                        self.space_pressed = False
                        self.space_press_time = 0
            
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(TARGET_FPS)
            
        pygame.quit()

if __name__ == "__main__":
    # Check if required modules are available
    try:
        import Box2D
        game = Game()
        game.run()
    except ImportError:
        print("This game requires PyBox2D and Pygame to be installed.")
        print("Install them with: pip install pygame Box2D")