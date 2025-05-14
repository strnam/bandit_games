import pygame
import sys
import os
import yaml
import numpy as np
from enum import Enum

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 900
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
FONT_SIZE = 28

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
                # Scale the image to a larger size
                self.image = pygame.transform.scale(self.image, (200, 200))
            else:
                # Create a placeholder image with text
                self.image = self.create_placeholder_image()
        except pygame.error:
            self.image = self.create_placeholder_image()
    
    def create_placeholder_image(self):
        # Create a surface for the placeholder
        surface = pygame.Surface((200, 200))
        
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
        return np.random.random() < effective_rate
    
    def __str__(self):
        return self.name

# Greedy Algorithm for medicine selection
def greedy_choice(arm_counts):
    """
    Greedy choice uses the empirical estimate to choose an arm.
    
    Args:
        arm_counts - n_arms x 2 - array of observed counts [successes, failures]
    
    Returns:
        choice - int - arm to be pulled at the next timestep (0 index)
    """
    p_max = -1
    choice = -1
    for i in range(len(arm_counts)):
        n_pull = arm_counts[i][0] + arm_counts[i][1]
        if n_pull < 0.5:  # No pulls yet
            p_hat = 0.5    # Default probability
        else:
            p_hat = arm_counts[i][0] / n_pull  # Success rate
        
        if p_hat > p_max:
            p_max = p_hat
            choice = i
    
    return choice

# Game Session
class GameSession:
    def __init__(self, num_persons, medicines, person_probabilities=None):
        self.num_persons = num_persons
        self.medicines = medicines
        self.persons = []
        self.results = {"survived": 0, "died": 0}
        self.current_person_index = 0
        self.person_probabilities = person_probabilities or {
            "male_young": 0.25, "male_old": 0.25, 
            "female_young": 0.25, "female_old": 0.25
        }
        self.generate_persons()
        self.game_over = False
        self.selected_medicine = None
        self.current_result = None
        # Add history tracking for each person
        self.history = []  # Will contain True for survived, False for died
        
        # Initialize arm counts for greedy algorithm
        # For each medicine, track [successes, failures] for each person type
        self.arm_counts = {}
        for gender in Gender:
            for age in Age:
                self.arm_counts[(gender, age)] = [[0, 0] for _ in range(len(medicines))]
        
        # Run baseline simulation in the background
        self.baseline_results = self.run_baseline_simulation()
    
    def generate_persons(self):
        # Generate persons based on configured probabilities
        for _ in range(self.num_persons):
            # Create weighted choices based on probabilities
            choices = []
            weights = []
            
            # Add each person type with its weight
            if self.person_probabilities["male_young"] > 0:
                choices.append((Gender.MALE, Age.YOUNG))
                weights.append(self.person_probabilities["male_young"])
            
            if self.person_probabilities["male_old"] > 0:
                choices.append((Gender.MALE, Age.OLD))
                weights.append(self.person_probabilities["male_old"])
            
            if self.person_probabilities["female_young"] > 0:
                choices.append((Gender.FEMALE, Age.YOUNG))
                weights.append(self.person_probabilities["female_young"])
            
            if self.person_probabilities["female_old"] > 0:
                choices.append((Gender.FEMALE, Age.OLD))
                weights.append(self.person_probabilities["female_old"])
            
            # If no valid probabilities, use default equal distribution
            if not choices:
                choices = [
                    (Gender.MALE, Age.YOUNG),
                    (Gender.MALE, Age.OLD),
                    (Gender.FEMALE, Age.YOUNG),
                    (Gender.FEMALE, Age.OLD)
                ]
                weights = [0.25, 0.25, 0.25, 0.25]
            
            # Normalize weights to sum to 1
            weights = np.array(weights) / np.sum(weights)
            
            # Choose a person type based on weights using NumPy
            idx = np.random.choice(len(choices), p=weights)
            gender, age = choices[idx]
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
            
            # Add to history
            self.history.append(survived)
            
            # Update arm counts for the greedy algorithm
            person_type = (person.gender, person.age)
            if person_type in self.arm_counts:
                if survived:
                    self.arm_counts[person_type][medicine_index][0] += 1  # Success
                else:
                    self.arm_counts[person_type][medicine_index][1] += 1  # Failure
            
            if survived:
                self.results["survived"] += 1
            else:
                self.results["died"] += 1
            
            self.current_person_index += 1
            
            if self.current_person_index >= len(self.persons):
                self.game_over = True
            
            return survived
        return False
        
    def get_greedy_recommendation(self, person, arm_counts):
        """Get medicine recommendation using the greedy algorithm for a specific person"""
        person_type = (person.gender, person.age)
        if person_type in arm_counts:
            return greedy_choice(arm_counts[person_type])
        
        # Default to first medicine if no recommendation
        return 0
        
    def run_baseline_simulation(self):
        """Run a simulation using the greedy algorithm as a baseline"""
        # Create a copy of the persons list for simulation
        sim_persons = self.persons.copy()
        
        # Initialize results and arm counts for simulation
        sim_results = {"survived": 0, "died": 0}
        sim_arm_counts = {}
        for gender in Gender:
            for age in Age:
                sim_arm_counts[(gender, age)] = [[0, 0] for _ in range(len(self.medicines))]
        
        # Run simulation for each person
        for person in sim_persons:
            # Get recommendation from greedy algorithm
            medicine_index = self.get_greedy_recommendation(person, sim_arm_counts)
            medicine = self.medicines[medicine_index]
            
            # Apply medicine and get result
            survived = medicine.apply(person)
            
            # Update arm counts
            person_type = (person.gender, person.age)
            if person_type in sim_arm_counts:
                if survived:
                    sim_arm_counts[person_type][medicine_index][0] += 1  # Success
                else:
                    sim_arm_counts[person_type][medicine_index][1] += 1  # Failure
            
            # Update results
            if survived:
                sim_results["survived"] += 1
            else:
                sim_results["died"] += 1
        
        return sim_results

# Game UI
class GameUI:
    def __init__(self, screen, session):
        self.screen = screen
        self.session = session
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.title_font = pygame.font.SysFont(None, FONT_SIZE * 2)
        self.button_rects = []
        # History matrix settings
        self.history_cell_size = 60  # Even larger cells
        self.history_margin = 15     # Margin between cells
        self.history_start_x = SCREEN_WIDTH - 450  # Position on the right side
        self.history_start_y = 400   # Position below the person image
    
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
            
        # Always draw the history matrix
        self.draw_history_matrix()
    
    def draw_medicine_selection_screen(self, mouse_pos):
        person = self.session.get_current_person()
        
        # Draw person info
        self.draw_text(f"Person {self.session.current_person_index + 1} of {self.session.num_persons}:", 
                      self.font, BLACK, 80, 140)
        self.draw_text(f"Gender: {person.gender.value}", self.font, BLACK, 80, 180)
        self.draw_text(f"Age: {person.age.value}", self.font, BLACK, 80, 220)
        
        # Draw person image
        if person.image:
            image_rect = person.image.get_rect(center=(SCREEN_WIDTH - 250, 180))
            self.screen.blit(person.image, image_rect)
        
        # Draw instructions
        self.draw_text("Select a medicine to administer:", self.font, BLACK, 80, 280)
        
        # Draw medicine buttons
        for i, medicine in enumerate(self.session.medicines):
            y_pos = 340 + i * 80
            hover = pygame.Rect(200, y_pos, 550, 60).collidepoint(mouse_pos)
            button_rect = self.draw_button(f"{medicine.name}", 200, y_pos, 550, 60, 
                                          GRAY if not hover else (220, 220, 220))
            self.button_rects.append(button_rect)
    
    def draw_result_screen(self):
        person = self.session.persons[self.session.current_person_index - 1]
        
        # Draw person info
        self.draw_text(f"Person {self.session.current_person_index} of {self.session.num_persons}:", 
                      self.font, BLACK, 80, 140)
        self.draw_text(f"Gender: {person.gender.value}", self.font, BLACK, 80, 180)
        self.draw_text(f"Age: {person.age.value}", self.font, BLACK, 80, 220)
        
        # Draw person image
        if person.image:
            image_rect = person.image.get_rect(center=(SCREEN_WIDTH - 250, 180))
            self.screen.blit(person.image, image_rect)
        
        # Draw medicine info
        self.draw_text(f"Medicine: {self.session.selected_medicine.name}", self.font, BLACK, 80, 280)
        
        # Draw result
        result_color = GREEN if self.session.current_result == "Survived" else RED
        self.draw_text(f"Result: {self.session.current_result}", self.font, result_color, 80, 320)
        
        # Draw continue button
        hover = pygame.Rect(350, 400, 250, 70).collidepoint(pygame.mouse.get_pos())
        button_rect = self.draw_button("Continue", 350, 400, 250, 70, 
                                      GRAY if not hover else (220, 220, 220))
        self.button_rects = [button_rect]
    
    def draw_game_over_screen(self):
        # Draw title
        self.draw_text("Game Over", self.title_font, BLACK, SCREEN_WIDTH // 2, 150, centered=True)
        
        # Draw user results
        self.draw_text("Your Results:", self.font, BLACK, SCREEN_WIDTH // 2, 220, centered=True)
        self.draw_text(f"Survived: {self.session.results['survived']}", self.font, GREEN, 
                      SCREEN_WIDTH // 2, 250, centered=True)
        self.draw_text(f"Died: {self.session.results['died']}", self.font, RED, 
                      SCREEN_WIDTH // 2, 280, centered=True)
        
        # Draw user survival rate
        user_survival_rate = (self.session.results['survived'] / self.session.num_persons) * 100
        self.draw_text(f"Your Survival Rate: {user_survival_rate:.1f}%", self.font, BLUE, 
                      SCREEN_WIDTH // 2, 310, centered=True)
        
        # Draw baseline results
        self.draw_text("Greedy Algorithm Baseline:", self.font, BLACK, SCREEN_WIDTH // 2, 360, centered=True)
        self.draw_text(f"Survived: {self.session.baseline_results['survived']}", self.font, GREEN, 
                      SCREEN_WIDTH // 2, 390, centered=True)
        self.draw_text(f"Died: {self.session.baseline_results['died']}", self.font, RED, 
                      SCREEN_WIDTH // 2, 420, centered=True)
        
        # Draw baseline survival rate
        baseline_survival_rate = (self.session.baseline_results['survived'] / self.session.num_persons) * 100
        self.draw_text(f"Baseline Survival Rate: {baseline_survival_rate:.1f}%", self.font, BLUE, 
                      SCREEN_WIDTH // 2, 450, centered=True)
        
        # Draw comparison
        diff = user_survival_rate - baseline_survival_rate
        comparison_text = ""
        comparison_color = BLACK
        if abs(diff) < 0.01:  # Almost equal
            comparison_text = "Your performance equals the baseline"
            comparison_color = BLUE
        elif diff > 0:
            comparison_text = f"You outperformed the baseline by {abs(diff):.1f}%"
            comparison_color = GREEN
        else:
            comparison_text = f"Baseline outperformed you by {abs(diff):.1f}%"
            comparison_color = RED
            
        self.draw_text(comparison_text, self.font, comparison_color, SCREEN_WIDTH // 2, 500, centered=True)
        
        # Draw restart button
        hover = pygame.Rect(SCREEN_WIDTH // 2 - 125, 570, 250, 70).collidepoint(pygame.mouse.get_pos())
        button_rect = self.draw_button("Play Again", SCREEN_WIDTH // 2 - 125, 570, 250, 70, 
                                      GRAY if not hover else (220, 220, 220))
        self.button_rects = [button_rect]
    
    def draw_history_matrix(self):
        # Draw the history title
        self.draw_text("Treatment History", self.font, BLACK, self.history_start_x + 180, self.history_start_y - 40, centered=True)
        
        # Calculate how many cells per row (max 6)
        cells_per_row = min(6, self.session.num_persons)
        if cells_per_row == 0:  # Avoid division by zero
            return
            
        # Calculate total rows needed
        total_rows = (self.session.num_persons + cells_per_row - 1) // cells_per_row
        
        # Draw the matrix of results
        for i, result in enumerate(self.session.history):
            row = i // cells_per_row
            col = i % cells_per_row
            
            x = self.history_start_x + col * (self.history_cell_size + self.history_margin)
            y = self.history_start_y + row * (self.history_cell_size + self.history_margin)
            
            # Draw cell background
            cell_rect = pygame.Rect(x, y, self.history_cell_size, self.history_cell_size)
            pygame.draw.rect(self.screen, GRAY, cell_rect)
            pygame.draw.rect(self.screen, BLACK, cell_rect, 1)  # Border
            
            # Draw the result symbol (green V or red X)
            if result:  # Survived
                # Draw a green V
                pygame.draw.line(self.screen, GREEN, (x + 10, y + 30), (x + 25, y + 45), 5)
                pygame.draw.line(self.screen, GREEN, (x + 25, y + 45), (x + 50, y + 15), 5)
            else:  # Died
                # Draw a red X
                pygame.draw.line(self.screen, RED, (x + 10, y + 10), (x + 50, y + 50), 5)
                pygame.draw.line(self.screen, RED, (x + 10, y + 50), (x + 50, y + 10), 5)
            
            # Draw person number
            small_font = pygame.font.SysFont(None, 18)
            num_text = small_font.render(str(i + 1), True, BLACK)
            self.screen.blit(num_text, (x + 3, y + 3))
        
        # Draw empty cells for future persons
        for i in range(len(self.session.history), self.session.num_persons):
            row = i // cells_per_row
            col = i % cells_per_row
            
            x = self.history_start_x + col * (self.history_cell_size + self.history_margin)
            y = self.history_start_y + row * (self.history_cell_size + self.history_margin)
            
            # Draw empty cell
            cell_rect = pygame.Rect(x, y, self.history_cell_size, self.history_cell_size)
            pygame.draw.rect(self.screen, GRAY, cell_rect, 1)  # Just the border
            
            # Draw person number
            small_font = pygame.font.SysFont(None, 18)
            num_text = small_font.render(str(i + 1), True, BLACK)
            self.screen.blit(num_text, (x + 3, y + 3))
    
    def handle_click(self, pos):
        for i, rect in enumerate(self.button_rects):
            if rect.collidepoint(pos):
                if self.session.game_over:
                    return "restart"
                elif self.session.current_result is not None:
                    self.session.current_result = None
                    return "continue"
                else:
                    # Apply medicine but wait for continue button
                    self.session.apply_medicine(i)
                    return "medicine_applied"
        return None

# Load configuration from YAML file
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config file: {e}")
        # Return default configuration if file can't be loaded
        return {
            'game': {'num_persons': 10},
            'medicines': [
                {
                    'name': 'Medicine A',
                    'effective_rates': {
                        'male_young': 0.8, 'male_old': 0.6,
                        'female_young': 0.7, 'female_old': 0.5
                    }
                },
                {
                    'name': 'Medicine B',
                    'effective_rates': {
                        'male_young': 0.6, 'male_old': 0.7,
                        'female_young': 0.8, 'female_old': 0.5
                    }
                },
                {
                    'name': 'Medicine C',
                    'effective_rates': {
                        'male_young': 0.5, 'male_old': 0.5,
                        'female_young': 0.6, 'female_old': 0.8
                    }
                }
            ]
        }

# Convert YAML config to game objects
def create_medicines_from_config(config):
    medicines = []
    for med_config in config['medicines']:
        # Convert string keys to enum tuple keys
        effective_rates = {}
        for key, value in med_config['effective_rates'].items():
            # Parse the key (e.g., 'male_young' -> (Gender.MALE, Age.YOUNG))
            parts = key.split('_')
            gender = Gender.MALE if parts[0] == 'male' else Gender.FEMALE
            age = Age.YOUNG if parts[1] == 'young' else Age.OLD
            effective_rates[(gender, age)] = value
        
        medicines.append(Medicine(med_config['name'], effective_rates))
    return medicines

# Main function
def main():
    # Set NumPy random seed for reproducibility
    np.random.seed(42)
    
    # Load configuration
    config = load_config()
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bandit Game")
    clock = pygame.time.Clock()
    
    # Create medicines from config
    medicines = create_medicines_from_config(config)
    
    # Get number of persons from config
    num_persons = config['game']['num_persons']
    
    # Get person probabilities from config
    person_probabilities = config.get('person_probabilities', {
        "male_young": 0.25, "male_old": 0.25, 
        "female_young": 0.25, "female_old": 0.25
    })
    
    # Create game session
    session = GameSession(num_persons, medicines, person_probabilities)
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
                    # Create a new game session with config values
                    num_persons = config['game']['num_persons']
                    person_probabilities = config.get('person_probabilities', {
                        "male_young": 0.25, "male_old": 0.25, 
                        "female_young": 0.25, "female_old": 0.25
                    })
                    session = GameSession(num_persons, medicines, person_probabilities)
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
