import pygame
import sys
import random
import os
from enum import Enum

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
FONT_SIZE = 24

# Gender Enum
class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"

# Age Enum
class Age(Enum):
    YOUNG = "Young"
    OLD = "Old"

# Person class
class Person:
    def __init__(self, gender=Gender.MALE, age=Age.YOUNG):
        self.gender = gender
        self.age = age
        self.image = None
        self.load_image()
    
    def load_image(self):
        # Define image path based on gender and age
        image_filename = f"{self.gender.value.lower()}_{self.age.value.lower()}_v2.png"
        image_path = os.path.join("images", image_filename)
        
        # Try to load the image if it exists, otherwise use a placeholder
        try:
            if os.path.exists(image_path):
                self.image = pygame.image.load(image_path)
                # Scale the image to a reasonable size
                self.image = pygame.transform.scale(self.image, (150, 150))
            else:
                # Create a placeholder image with text
                self.image = self.create_placeholder_image()
        except pygame.error:
            self.image = self.create_placeholder_image()
    
    def create_placeholder_image(self):
        # Create a surface for the placeholder
        surface = pygame.Surface((150, 150))
        
        # Choose background color based on gender
        if self.gender == Gender.MALE:
            bg_color = (180, 200, 255)  # Light blue for male
        else:
            bg_color = (255, 180, 200)  # Light pink for female
        
        surface.fill(bg_color)
        
        # Draw a simple person silhouette
        # Head
        head_color = (80, 80, 80)
        pygame.draw.circle(surface, head_color, (75, 50), 25)
        
        # Body
        body_color = (100, 100, 100)
        pygame.draw.rect(surface, body_color, (60, 75, 30, 50))
        
        # Add age-specific details
        if self.age == Age.OLD:
            # Draw gray hair or wrinkles for old
            pygame.draw.line(surface, (200, 200, 200), (55, 40), (70, 35), 3)
            pygame.draw.line(surface, (200, 200, 200), (80, 35), (95, 40), 3)
            # Walking stick
            pygame.draw.line(surface, (139, 69, 19), (45, 75), (55, 125), 3)
        else:
            # Younger appearance
            # Maybe a hat or different hairstyle
            pygame.draw.rect(surface, (50, 50, 50), (60, 25, 30, 10))
        
        # Add text labels
        font = pygame.font.SysFont(None, 20)
        gender_text = font.render(self.gender.value, True, (0, 0, 0))
        age_text = font.render(self.age.value, True, (0, 0, 0))
        
        # Position the text
        surface.blit(gender_text, (75 - gender_text.get_width() // 2, 130))
        surface.blit(age_text, (75 - age_text.get_width() // 2, 110))
        
        # Add a border
        pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 2)
        
        return surface
    
    def __str__(self):
        return f"{self.gender.value}, {self.age.value}"

# Medicine class
class Medicine:
    def __init__(self, name, effective_rates):
        self.name = name
        # Dictionary with (gender, age) tuples as keys and effective rates as values
        self.effective_rates = effective_rates
    
    def get_effective_rate(self, person):
        return self.effective_rates.get((person.gender, person.age), 0.5)
    
    def apply(self, person):
        effective_rate = self.get_effective_rate(person)
        # Bernoulli distribution: 1 (survive) with probability effective_rate, 0 (die) otherwise
        return random.random() < effective_rate
    
    def __str__(self):
        return self.name

# Game Session
class GameSession:
    def __init__(self, num_persons, medicines):
        self.num_persons = num_persons
        self.medicines = medicines
        self.persons = []
        self.results = {"survived": 0, "died": 0}
        self.current_person_index = 0
        self.generate_persons()
        self.game_over = False
        self.selected_medicine = None
        self.current_result = None
    
    def generate_persons(self):
        # Generate random persons
        for _ in range(self.num_persons):
            gender = random.choice(list(Gender))
            age = random.choice(list(Age))
            self.persons.append(Person(gender, age))
    
    def get_current_person(self):
        if self.current_person_index < len(self.persons):
            return self.persons[self.current_person_index]
        return None
    
    def apply_medicine(self, medicine_index):
        person = self.get_current_person()
        if person:
            medicine = self.medicines[medicine_index]
            self.selected_medicine = medicine
            survived = medicine.apply(person)
            self.current_result = "Survived" if survived else "Died"
            
            if survived:
                self.results["survived"] += 1
            else:
                self.results["died"] += 1
            
            self.current_person_index += 1
            
            if self.current_person_index >= len(self.persons):
                self.game_over = True
            
            return survived
        return False

# Game UI
class GameUI:
    def __init__(self, screen, session):
        self.screen = screen
        self.session = session
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.title_font = pygame.font.SysFont(None, FONT_SIZE * 2)
        self.button_rects = []
    
    def draw_text(self, text, font, color, x, y, centered=False):
        text_surface = font.render(text, True, color)
        if centered:
            text_rect = text_surface.get_rect(center=(x, y))
        else:
            text_rect = text_surface.get_rect(topleft=(x, y))
        self.screen.blit(text_surface, text_rect)
        return text_rect
    
    def draw_button(self, text, x, y, width, height, color, hover=False):
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, color, button_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, button_rect, 2, border_radius=5)
        
        if hover:
            # Draw a highlight effect when hovering
            pygame.draw.rect(self.screen, (255, 255, 200), button_rect, 3, border_radius=5)
        
        # Center the text on the button
        self.draw_text(text, self.font, BLACK, x + width // 2, y + height // 2, centered=True)
        return button_rect
    
    def draw_game_screen(self, mouse_pos):
        self.screen.fill(WHITE)
        self.button_rects = []
        
        # Draw title
        self.draw_text("Bandit Game - Medicine Selection", self.title_font, BLACK, SCREEN_WIDTH // 2, 50, centered=True)
        
        if self.session.game_over:
            self.draw_game_over_screen()
        elif self.session.current_result is not None:
            self.draw_result_screen()
        else:
            self.draw_medicine_selection_screen(mouse_pos)
    
    def draw_medicine_selection_screen(self, mouse_pos):
        person = self.session.get_current_person()
        
        # Draw person info
        self.draw_text(f"Person {self.session.current_person_index + 1} of {self.session.num_persons}:", 
                      self.font, BLACK, 50, 120)
        self.draw_text(f"Gender: {person.gender.value}", self.font, BLACK, 50, 150)
        self.draw_text(f"Age: {person.age.value}", self.font, BLACK, 50, 180)
        
        # Draw person image
        if person.image:
            image_rect = person.image.get_rect(center=(SCREEN_WIDTH - 150, 150))
            self.screen.blit(person.image, image_rect)
        
        # Draw instructions
        self.draw_text("Select a medicine to administer:", self.font, BLACK, 50, 230)
        
        # Draw medicine buttons
        for i, medicine in enumerate(self.session.medicines):
            y_pos = 280 + i * 60
            hover = pygame.Rect(200, y_pos, 400, 50).collidepoint(mouse_pos)
            button_rect = self.draw_button(f"{medicine.name}", 200, y_pos, 400, 50, 
                                         GRAY if not hover else (220, 220, 220))
            self.button_rects.append(button_rect)
    
    def draw_result_screen(self):
        person = self.session.persons[self.session.current_person_index - 1]
        
        # Draw person info
        self.draw_text(f"Person {self.session.current_person_index} of {self.session.num_persons}:", 
                      self.font, BLACK, 50, 120)
        self.draw_text(f"Gender: {person.gender.value}", self.font, BLACK, 50, 150)
        self.draw_text(f"Age: {person.age.value}", self.font, BLACK, 50, 180)
        
        # Draw person image
        if person.image:
            image_rect = person.image.get_rect(center=(SCREEN_WIDTH - 150, 150))
            self.screen.blit(person.image, image_rect)
        
        # Draw medicine info
        self.draw_text(f"Medicine: {self.session.selected_medicine.name}", self.font, BLACK, 50, 230)
        
        # Draw result
        result_color = GREEN if self.session.current_result == "Survived" else RED
        self.draw_text(f"Result: {self.session.current_result}", self.font, result_color, 50, 260)
        
        # Draw continue button
        hover = pygame.Rect(300, 350, 200, 50).collidepoint(pygame.mouse.get_pos())
        button_rect = self.draw_button("Continue", 300, 350, 200, 50, 
                                     GRAY if not hover else (220, 220, 220))
        self.button_rects = [button_rect]
    
    def draw_game_over_screen(self):
        # Draw title
        self.draw_text("Game Over", self.title_font, BLACK, SCREEN_WIDTH // 2, 150, centered=True)
        
        # Draw results
        self.draw_text(f"Total Persons: {self.session.num_persons}", self.font, BLACK, 
                      SCREEN_WIDTH // 2, 220, centered=True)
        self.draw_text(f"Survived: {self.session.results['survived']}", self.font, GREEN, 
                      SCREEN_WIDTH // 2, 250, centered=True)
        self.draw_text(f"Died: {self.session.results['died']}", self.font, RED, 
                      SCREEN_WIDTH // 2, 280, centered=True)
        
        # Draw survival rate
        survival_rate = (self.session.results['survived'] / self.session.num_persons) * 100
        self.draw_text(f"Survival Rate: {survival_rate:.1f}%", self.font, BLUE, 
                      SCREEN_WIDTH // 2, 320, centered=True)
        
        # Draw restart button
        hover = pygame.Rect(300, 400, 200, 50).collidepoint(pygame.mouse.get_pos())
        button_rect = self.draw_button("Play Again", 300, 400, 200, 50, 
                                     GRAY if not hover else (220, 220, 220))
        self.button_rects = [button_rect]
    
    def handle_click(self, pos):
        for i, rect in enumerate(self.button_rects):
            if rect.collidepoint(pos):
                if self.session.game_over:
                    return "restart"
                elif self.session.current_result is not None:
                    self.session.current_result = None
                    return "continue"
                else:
                    self.session.apply_medicine(i)
                    return "medicine_applied"
        return None

# Main function
def main():
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bandit Game")
    clock = pygame.time.Clock()
    
    # Define medicines with their effective rates
    medicines = [
        Medicine("Medicine A", {
            (Gender.MALE, Age.YOUNG): 0.8,    # effective_rate_1
            (Gender.MALE, Age.OLD): 0.6,      # effective_rate_2
            (Gender.FEMALE, Age.YOUNG): 0.7,  # effective_rate_3
            (Gender.FEMALE, Age.OLD): 0.5     # effective_rate_4
        }),
        Medicine("Medicine B", {
            (Gender.MALE, Age.YOUNG): 0.6,
            (Gender.MALE, Age.OLD): 0.7,
            (Gender.FEMALE, Age.YOUNG): 0.8,
            (Gender.FEMALE, Age.OLD): 0.5
        }),
        Medicine("Medicine C", {
            (Gender.MALE, Age.YOUNG): 0.5,
            (Gender.MALE, Age.OLD): 0.5,
            (Gender.FEMALE, Age.YOUNG): 0.6,
            (Gender.FEMALE, Age.OLD): 0.8
        })
    ]
    
    # Create game session
    session = GameSession(10, medicines)  # 10 persons
    ui = GameUI(screen, session)
    
    # Main game loop
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                action = ui.handle_click(event.pos)
                if action == "restart":
                    # Create a new game session
                    session = GameSession(10, medicines)
                    ui.session = session
        
        # Draw the game screen
        ui.draw_game_screen(mouse_pos)
        
        # Update the display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
