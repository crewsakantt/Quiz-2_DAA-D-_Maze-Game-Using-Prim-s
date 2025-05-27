import pygame
import random
import sys
import math
from collections import defaultdict

pygame.init()

CELL_SIZE = 25
MAZE_WIDTH = 25  
MAZE_HEIGHT = 17  
SCREEN_WIDTH = MAZE_WIDTH * CELL_SIZE + 200  
SCREEN_HEIGHT = MAZE_HEIGHT * CELL_SIZE + 100
SIDEBAR_WIDTH = 200

COLORS = {
    'bg': (15, 15, 25),
    'wall': (45, 55, 85),
    'wall_highlight': (65, 75, 105),
    'path': (25, 30, 45),
    'player': (255, 100, 100),
    'player_glow': (255, 150, 150),
    'goal': (100, 255, 150),
    'goal_glow': (150, 255, 200),
    'ui_bg': (35, 40, 60),
    'ui_border': (85, 95, 125),
    'text_primary': (255, 255, 255),
    'text_secondary': (180, 190, 220),
    'accent': (100, 200, 255),
    'success': (100, 255, 100),
    'particle': (255, 200, 100)
}

class Particle:
    def __init__(self, x, y, color, velocity, life):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.life = life
        self.max_life = life
        self.size = random.uniform(2, 5)
    
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.life -= 1
        self.velocity = (self.velocity[0] * 0.98, self.velocity[1] * 0.98)
    
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            color = (*self.color, alpha)
            size = int(self.size * (self.life / self.max_life))
            if size > 0:
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (size, size), size)
                screen.blit(surf, (int(self.x - size), int(self.y - size)))

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_explosion(self, x, y, color, count=10):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            life = random.randint(30, 60)
            self.particles.append(Particle(x, y, color, velocity, life))
    
    def add_trail(self, x, y, color):
        for _ in range(3):
            velocity = (random.uniform(-1, 1), random.uniform(-1, 1))
            life = random.randint(15, 30)
            self.particles.append(Particle(x, y, color, velocity, life))
    
    def update(self):
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)

class MazeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maze = [[1 for _ in range(width)] for _ in range(height)]
        
    def generate_maze_prims(self):
        """Generate maze using Prim's Algorithm"""
        self.maze = [[1 for _ in range(self.width)] for _ in range(self.height)]
        
        start_x = random.randrange(1, self.width, 2)
        start_y = random.randrange(1, self.height, 2)
        
        self.maze[start_y][start_x] = 0
        walls = []
        self.add_walls(start_x, start_y, walls)
        
        while walls:
            wall = random.choice(walls)
            walls.remove(wall)
            
            wx, wy = wall
            cells = self.get_divided_cells(wx, wy)
            
            if len(cells) == 2:
                cell1, cell2 = cells
                c1x, c1y = cell1
                c2x, c2y = cell2
                
                if (self.maze[c1y][c1x] == 0) != (self.maze[c2y][c2x] == 0):
                    self.maze[wy][wx] = 0
                    
                    if self.maze[c1y][c1x] == 1:
                        self.maze[c1y][c1x] = 0
                        self.add_walls(c1x, c1y, walls)
                    else:
                        self.maze[c2y][c2x] = 0
                        self.add_walls(c2x, c2y, walls)
        
        return self.maze
    
    def add_walls(self, x, y, walls):
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        for dx, dy in directions:
            wall_x = x + dx // 2
            wall_y = y + dy // 2
            if (0 < wall_x < self.width - 1 and 0 < wall_y < self.height - 1 and
                (wall_x, wall_y) not in walls):
                walls.append((wall_x, wall_y))
    
    def get_divided_cells(self, wall_x, wall_y):
        cells = []
        if wall_y % 2 == 0:
            if wall_y > 0:
                cells.append((wall_x, wall_y - 1))
            if wall_y < self.height - 1:
                cells.append((wall_x, wall_y + 1))
        
        if wall_x % 2 == 0:
            if wall_x > 0:
                cells.append((wall_x - 1, wall_y))
            if wall_x < self.width - 1:
                cells.append((wall_x + 1, wall_y))
        
        return cells

class MazeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("MAZE-RAOUI")
        self.clock = pygame.time.Clock()
 
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
    
        self.generator = MazeGenerator(MAZE_WIDTH, MAZE_HEIGHT)
        self.maze = self.generator.generate_maze_prims()

        self.player_x = 1
        self.player_y = 1
        self.player_visual_x = 1.0
        self.player_visual_y = 1.0
        self.player_target_x = 1.0
        self.player_target_y = 1.0
        self.animation_speed = 0.3
 
        self.goal_x = MAZE_WIDTH - 2
        self.goal_y = MAZE_HEIGHT - 2
        self.maze[self.goal_y][self.goal_x] = 0

        self.game_won = False
        self.moves = 0
        self.start_time = pygame.time.get_ticks()
        self.end_time = None 

        self.particle_system = ParticleSystem()
        self.glow_time = 0
        self.win_animation_time = 0

        self.ui_hover = {}
        
    def draw_rounded_rect(self, surface, color, rect, radius):
        """Draw a rounded rectangle"""
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    
    def draw_glow_circle(self, surface, color, center, radius, glow_radius=None):
        """Draw a glowing circle effect"""
        if glow_radius is None:
            glow_radius = radius + 10

        glow_surf = pygame.Surface((glow_radius * 4, glow_radius * 4), pygame.SRCALPHA)
        for i in range(glow_radius, 0, -2):
            alpha = int(30 * (i / glow_radius))
            glow_color = (*color[:3], alpha)
            pygame.draw.circle(glow_surf, glow_color, (glow_radius * 2, glow_radius * 2), i)
        
        surface.blit(glow_surf, (center[0] - glow_radius * 2, center[1] - glow_radius * 2))
        pygame.draw.circle(surface, color, center, radius)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()
                elif not self.game_won:
                    if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                                   pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                        self.handle_movement(event.key)
        return True
    
    def handle_movement(self, key):
        new_x, new_y = self.player_x, self.player_y

        if key == pygame.K_UP or key == pygame.K_w:
            new_y -= 1
        elif key == pygame.K_DOWN or key == pygame.K_s:
            new_y += 1
        elif key == pygame.K_LEFT or key == pygame.K_a:
            new_x -= 1
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            new_x += 1
        else:
            return  

        if (0 <= new_x < MAZE_WIDTH and 0 <= new_y < MAZE_HEIGHT and
            self.maze[new_y][new_x] == 0):
            
            old_center_x = self.player_x * CELL_SIZE + CELL_SIZE // 2
            old_center_y = self.player_y * CELL_SIZE + CELL_SIZE // 2
            self.particle_system.add_trail(old_center_x, old_center_y, COLORS['player'])
            
            self.player_x = new_x
            self.player_y = new_y
            self.player_target_x = float(new_x)
            self.player_target_y = float(new_y)
            self.moves += 1  

            if self.player_x == self.goal_x and self.player_y == self.goal_y:
                self.game_won = True
                self.end_time = pygame.time.get_ticks()  
                self.win_animation_time = pygame.time.get_ticks()
                center_x = self.goal_x * CELL_SIZE + CELL_SIZE // 2
                center_y = self.goal_y * CELL_SIZE + CELL_SIZE // 2
                self.particle_system.add_explosion(center_x, center_y, COLORS['success'], 20)
    
    def update_animations(self):
        self.player_visual_x += (self.player_target_x - self.player_visual_x) * self.animation_speed
        self.player_visual_y += (self.player_target_y - self.player_visual_y) * self.animation_speed
        
        self.glow_time += 0.1
        
        self.particle_system.update()
        
        if random.random() < 0.3:
            center_x = self.goal_x * CELL_SIZE + CELL_SIZE // 2
            center_y = self.goal_y * CELL_SIZE + CELL_SIZE // 2
            offset_x = random.uniform(-CELL_SIZE//3, CELL_SIZE//3)
            offset_y = random.uniform(-CELL_SIZE//3, CELL_SIZE//3)
            self.particle_system.add_trail(center_x + offset_x, center_y + offset_y, COLORS['goal'])
    
    def reset_game(self):
        self.maze = self.generator.generate_maze_prims()
        self.player_x = 1
        self.player_y = 1
        self.player_visual_x = 1.0
        self.player_visual_y = 1.0
        self.player_target_x = 1.0
        self.player_target_y = 1.0
        self.goal_x = MAZE_WIDTH - 2
        self.goal_y = MAZE_HEIGHT - 2
        self.maze[self.goal_y][self.goal_x] = 0
        self.game_won = False
        self.moves = 0
        self.start_time = pygame.time.get_ticks()
        self.end_time = None  
        self.particle_system = ParticleSystem()
        
        self.particle_system.add_explosion(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, COLORS['accent'], 15)
    
    def draw_maze(self):
        """Draw the maze with 3D effect"""
        for y in range(MAZE_HEIGHT):
            for x in range(MAZE_WIDTH):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if self.maze[y][x] == 1:  
                    pygame.draw.rect(self.screen, COLORS['wall'], rect)
                    pygame.draw.line(self.screen, COLORS['wall_highlight'], 
                                   (rect.left, rect.top), (rect.right, rect.top), 2)
                    pygame.draw.line(self.screen, COLORS['wall_highlight'], 
                                   (rect.left, rect.top), (rect.left, rect.bottom), 2)
                else:  
                    pygame.draw.rect(self.screen, COLORS['path'], rect)
    
    def draw_entities(self):
        """Draw player and goal with effects"""
        goal_center_x = self.goal_x * CELL_SIZE + CELL_SIZE // 2
        goal_center_y = self.goal_y * CELL_SIZE + CELL_SIZE // 2
        glow_intensity = abs(math.sin(self.glow_time)) * 0.5 + 0.5
        goal_radius = int(CELL_SIZE // 3 + glow_intensity * 5)
        
        self.draw_glow_circle(self.screen, COLORS['goal'], 
                             (goal_center_x, goal_center_y), goal_radius)

        player_center_x = int(self.player_visual_x * CELL_SIZE + CELL_SIZE // 2)
        player_center_y = int(self.player_visual_y * CELL_SIZE + CELL_SIZE // 2)
        player_radius = CELL_SIZE // 3
        
        self.draw_glow_circle(self.screen, COLORS['player'], 
                             (player_center_x, player_center_y), player_radius)
    
    def draw_sidebar(self):
        """Draw sidebar with game info"""
        sidebar_x = MAZE_WIDTH * CELL_SIZE + 10
        
        sidebar_rect = pygame.Rect(sidebar_x, 0, SIDEBAR_WIDTH - 10, SCREEN_HEIGHT)
        self.draw_rounded_rect(self.screen, COLORS['ui_bg'], sidebar_rect, 15)
        pygame.draw.rect(self.screen, COLORS['ui_border'], sidebar_rect, 3, border_radius=15)
        
        y_offset = 30

        title_text = self.font_medium.render("MAZE-RAOUI", True, COLORS['accent'])
        title_rect = title_text.get_rect(centerx=sidebar_x + SIDEBAR_WIDTH // 2)
        title_rect.y = y_offset
        self.screen.blit(title_text, title_rect)
        y_offset += 60
        
        if self.game_won and self.end_time:
            elapsed_time = (self.end_time - self.start_time) // 1000
        else:
            elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000
        
        stats = [
            ("Moves", str(self.moves)),
            ("Time", f"{elapsed_time}s"),
        ]
        
        for label, value in stats:

            label_text = self.font_small.render(label, True, COLORS['text_secondary'])
            self.screen.blit(label_text, (sidebar_x + 20, y_offset))
            
            value_text = self.font_medium.render(value, True, COLORS['text_primary'])
            value_rect = pygame.Rect(sidebar_x + 20, y_offset + 25, SIDEBAR_WIDTH - 50, 35)
            self.draw_rounded_rect(self.screen, COLORS['path'], value_rect, 8)
            
            value_text_rect = value_text.get_rect(center=value_rect.center)
            self.screen.blit(value_text, value_text_rect)
            
            y_offset += 80

        y_offset += 20
        controls_title = self.font_small.render("CONTROLS", True, COLORS['accent'])
        self.screen.blit(controls_title, (sidebar_x + 20, y_offset))
        y_offset += 30
        
        controls = [
            "WASD / Arrows - Move",
            "R - New Maze"
        ]
        
        for control in controls:
            control_text = self.font_small.render(control, True, COLORS['text_secondary'])
            self.screen.blit(control_text, (sidebar_x + 20, y_offset))
            y_offset += 25

        if self.game_won:
            y_offset += 30
            win_bg = pygame.Rect(sidebar_x + 10, y_offset, SIDEBAR_WIDTH - 30, 80)
            self.draw_rounded_rect(self.screen, COLORS['success'], win_bg, 10)
            
            win_text1 = self.font_medium.render("YOU WIN!", True, COLORS['bg'])
            win_text2 = self.font_small.render("Press R for new maze", True, COLORS['bg'])
            
            win_text1_rect = win_text1.get_rect(center=(win_bg.centerx, win_bg.centery - 15))
            win_text2_rect = win_text2.get_rect(center=(win_bg.centerx, win_bg.centery + 15))
            
            self.screen.blit(win_text1, win_text1_rect)
            self.screen.blit(win_text2, win_text2_rect)
    
    def draw(self):
        self.screen.fill(COLORS['bg'])
        
        self.draw_maze()

        self.particle_system.draw(self.screen)

        self.draw_entities()

        self.draw_sidebar()
        
        pygame.display.flip()
    
    def run(self):
        print("Starting MAZE-RAOUI Puzzle Game!")
        print("Goal: Navigate to the glowing green circle!")
        print()
        
        running = True
        while running:
            running = self.handle_events()
            self.update_animations()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = MazeGame()
    game.run()
