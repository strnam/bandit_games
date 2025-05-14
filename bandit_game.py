import pygame
import sys
import os
import yaml
import numpy as np
# Set matplotlib to use non-GUI backend to avoid Qt dependency issues
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend (non-GUI)
import matplotlib.pyplot as plt
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

def epsilon_greedy_choice(arm_counts):
    """
    Epsilon-Greedy algorithm for arm selection.
    
    Args:
        arm_counts: n_arms x 2 array of observed counts [successes, failures]
        
    Returns:
        choice: int - arm to be pulled at the next timestep (0 index)
    """
    epsilon = 0.1  # Probability of random action
    
    if np.random.random() < epsilon:
        # Explore: choose a random arm
        choice = np.random.randint(0, len(arm_counts))
    else:
        # Exploit: choose the best arm according to greedy policy
        choice = greedy_choice(arm_counts)
        
    return choice

# Game Session
class GameSession:
    def __init__(self, num_persons, medicines, person_probabilities=None):
        self.num_persons = num_persons
        self.medicines = medicines
        self.persons = []
        self.results = {"survived": 0, "died": 0}
        self.baseline_results = {"survived": 0, "died": 0}
        self.baseline2_results = {"survived": 0, "died": 0}  # For epsilon-greedy
        self.game_over = False
        self.arm_counts = [[0, 0] for _ in range(len(medicines))]
        self.arm_counts_epsilon = [[0, 0] for _ in range(len(medicines))]  # Separate counts for epsilon-greedy
        self.accumulated_survival = [0]  # Track accumulated survival
        self.baseline_accumulated_survival = [0]  # Track baseline accumulated survival
        self.baseline2_accumulated_survival = [0]  # Track epsilon-greedy accumulated survival
        self.current_person_index = 0
        self.person_probabilities = person_probabilities or {
            "male_young": 0.25, "male_old": 0.25, 
            "female_young": 0.25, "female_old": 0.25
        }
        self.generate_persons()
        self.selected_medicine = None
        self.current_result = None
        # Add history tracking for each person
        self.history = []  # Will contain True for survived, False for died
        
        # Run baseline simulation in the background
        self.baseline_results, self.baseline_accumulated_survival = self.run_baseline_simulation()
        self.baseline2_results, self.baseline2_accumulated_survival = self.run_baseline2_simulation()
    
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
            if survived:
                self.arm_counts[medicine_index][0] += 1  # Success
            else:
                self.arm_counts[medicine_index][1] += 1  # Failure
            
            # Update arm counts for the epsilon-greedy algorithm
            if survived:
                self.arm_counts_epsilon[medicine_index][0] += 1  # Success
            else:
                self.arm_counts_epsilon[medicine_index][1] += 1  # Failure
            
            if survived:
                self.results["survived"] += 1
            else:
                self.results["died"] += 1
                
            # Update accumulated survival count
            self.accumulated_survival.append(self.results["survived"])
            
            self.current_person_index += 1
            
            if self.current_person_index >= len(self.persons):
                self.game_over = True
                # Generate survival comparison graph
                self.generate_survival_graph()
            
            return survived
        return False
        
    def generate_survival_graph(self):
        """Generate a graph comparing user performance with baseline algorithms"""
        plt.figure(figsize=(10, 6))
        x = range(len(self.accumulated_survival))
        
        # Plot user performance
        plt.plot(x, self.accumulated_survival, 'b-', linewidth=2, label='Your Performance')
        
        # Plot baseline 1 performance (greedy)
        plt.plot(x, self.baseline_accumulated_survival, 'r--', linewidth=2, label='Greedy Algorithm')
        
        # Plot baseline 2 performance (epsilon-greedy)
        plt.plot(x, self.baseline2_accumulated_survival, 'g-.', linewidth=2, label='Epsilon-Greedy Algorithm')
        
        plt.xlabel('Person Number')
        plt.ylabel('Accumulated Survival Count')
        plt.title('Performance Comparison: You vs. Baseline Algorithms')
        plt.legend()
        plt.grid(True)
        
        # Save the graph
        plt.savefig('survival_comparison.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        return 'survival_comparison.png'
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
        sim_arm_counts = [[0, 0] for _ in range(len(self.medicines))]
        
        # Track accumulated survival for baseline
        accumulated_survival = [0]
        
        # Run simulation for each person
        for person in sim_persons:
            # Get recommendation from greedy algorithm
            medicine_index = greedy_choice(sim_arm_counts)
            medicine = self.medicines[medicine_index]
            
            # Apply medicine and get result
            effectiveness = medicine.get_effective_rate(person)
            survived = np.random.random() < effectiveness
            
            # Update arm counts
            if survived:
                sim_arm_counts[medicine_index][0] += 1  # Success
            else:
                sim_arm_counts[medicine_index][1] += 1  # Failure
            
            # Update results
            if survived:
                sim_results["survived"] += 1
            else:
                sim_results["died"] += 1
                
            # Update accumulated survival
            accumulated_survival.append(sim_results["survived"])
        
        return sim_results, accumulated_survival
        
    def run_baseline2_simulation(self):
        """Run a simulation using the epsilon-greedy algorithm as a second baseline"""
        # Create a copy of the persons list for simulation
        sim_persons = self.persons.copy()
        
        # Initialize results and arm counts for simulation
        sim_results = {"survived": 0, "died": 0}
        sim_arm_counts = [[0, 0] for _ in range(len(self.medicines))]
        
        # Track accumulated survival for baseline
        accumulated_survival = [0]
        
        # Run simulation for each person
        for person in sim_persons:
            # Get recommendation from epsilon-greedy algorithm
            medicine_index = epsilon_greedy_choice(sim_arm_counts)
            medicine = self.medicines[medicine_index]
            
            # Apply medicine and get result
            effectiveness = medicine.get_effective_rate(person)
            survived = np.random.random() < effectiveness
            
            # Update arm counts
            if survived:
                sim_arm_counts[medicine_index][0] += 1  # Success
            else:
                sim_arm_counts[medicine_index][1] += 1  # Failure
            
            # Update results
            if survived:
                sim_results["survived"] += 1
            else:
                sim_results["died"] += 1
                
            # Update accumulated survival
            accumulated_survival.append(sim_results["survived"])
        
        return sim_results, accumulated_survival

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
        
        # Scrolling settings
        self.scroll_y = 0  # Current scroll position
        self.scroll_speed = 20  # Pixels per scroll event
        self.max_scroll = 0  # Will be calculated based on content height
    
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
        # Create a scrollable surface that can be larger than the screen
        # First, determine the total height needed
        total_height = 1500  # Start with a large value to accommodate all content
        
        # Create a surface for the scrollable content
        scroll_surface = pygame.Surface((SCREEN_WIDTH, total_height))
        scroll_surface.fill(WHITE)
        
        # Draw all content on the scroll surface with adjusted positions
        # Draw title
        self.draw_text_on_surface(scroll_surface, "Game Over", self.title_font, BLACK, SCREEN_WIDTH // 2, 150, centered=True)
        
        # Draw user results
        self.draw_text_on_surface(scroll_surface, "Your Results:", self.font, BLACK, SCREEN_WIDTH // 2, 220, centered=True)
        self.draw_text_on_surface(scroll_surface, f"Survived: {self.session.results['survived']}", self.font, GREEN, 
                      SCREEN_WIDTH // 2, 250, centered=True)
        self.draw_text_on_surface(scroll_surface, f"Died: {self.session.results['died']}", self.font, RED, 
                      SCREEN_WIDTH // 2, 280, centered=True)
        
        # Draw user survival rate
        user_survival_rate = (self.session.results['survived'] / self.session.num_persons) * 100
        self.draw_text_on_surface(scroll_surface, f"Your Survival Rate: {user_survival_rate:.1f}%", self.font, BLUE, 
                      SCREEN_WIDTH // 2, 310, centered=True)
        
        # Draw greedy baseline results
        self.draw_text_on_surface(scroll_surface, "Greedy Algorithm Baseline:", self.font, BLACK, SCREEN_WIDTH // 2, 360, centered=True)
        self.draw_text_on_surface(scroll_surface, f"Survived: {self.session.baseline_results['survived']}", self.font, GREEN, 
                      SCREEN_WIDTH // 2, 390, centered=True)
        self.draw_text_on_surface(scroll_surface, f"Died: {self.session.baseline_results['died']}", self.font, RED, 
                      SCREEN_WIDTH // 2, 420, centered=True)
        
        # Draw greedy baseline survival rate
        baseline_survival_rate = (self.session.baseline_results['survived'] / self.session.num_persons) * 100
        self.draw_text_on_surface(scroll_surface, f"Greedy Survival Rate: {baseline_survival_rate:.1f}%", self.font, BLUE, 
                      SCREEN_WIDTH // 2, 450, centered=True)
        
        # Draw epsilon-greedy baseline results
        self.draw_text_on_surface(scroll_surface, "Epsilon-Greedy Algorithm Baseline:", self.font, BLACK, SCREEN_WIDTH // 2, 500, centered=True)
        self.draw_text_on_surface(scroll_surface, f"Survived: {self.session.baseline2_results['survived']}", self.font, GREEN, 
                      SCREEN_WIDTH // 2, 530, centered=True)
        self.draw_text_on_surface(scroll_surface, f"Died: {self.session.baseline2_results['died']}", self.font, RED, 
                      SCREEN_WIDTH // 2, 560, centered=True)
        
        # Draw epsilon-greedy baseline survival rate
        baseline2_survival_rate = (self.session.baseline2_results['survived'] / self.session.num_persons) * 100
        self.draw_text_on_surface(scroll_surface, f"Epsilon-Greedy Survival Rate: {baseline2_survival_rate:.1f}%", self.font, BLUE, 
                      SCREEN_WIDTH // 2, 590, centered=True)
        
        # Draw comparison with greedy
        diff_greedy = user_survival_rate - baseline_survival_rate
        comparison_text_greedy = ""
        comparison_color_greedy = BLACK
        if abs(diff_greedy) < 0.01:  # Almost equal
            comparison_text_greedy = "Your performance equals the Greedy baseline"
            comparison_color_greedy = BLUE
        elif diff_greedy > 0:
            comparison_text_greedy = f"You outperformed Greedy by {abs(diff_greedy):.1f}%"
            comparison_color_greedy = GREEN
        else:
            comparison_text_greedy = f"Greedy outperformed you by {abs(diff_greedy):.1f}%"
            comparison_color_greedy = RED
            
        self.draw_text_on_surface(scroll_surface, comparison_text_greedy, self.font, comparison_color_greedy, SCREEN_WIDTH // 2, 640, centered=True)
        
        # Draw comparison with epsilon-greedy
        diff_egreedy = user_survival_rate - baseline2_survival_rate
        comparison_text_egreedy = ""
        comparison_color_egreedy = BLACK
        if abs(diff_egreedy) < 0.01:  # Almost equal
            comparison_text_egreedy = "Your performance equals the Epsilon-Greedy baseline"
            comparison_color_egreedy = BLUE
        elif diff_egreedy > 0:
            comparison_text_egreedy = f"You outperformed Epsilon-Greedy by {abs(diff_egreedy):.1f}%"
            comparison_color_egreedy = GREEN
        else:
            comparison_text_egreedy = f"Epsilon-Greedy outperformed you by {abs(diff_egreedy):.1f}%"
            comparison_color_egreedy = RED
            
        self.draw_text_on_surface(scroll_surface, comparison_text_egreedy, self.font, comparison_color_egreedy, SCREEN_WIDTH // 2, 670, centered=True)
        
        # Load and display the survival comparison graph
        graph_path = os.path.join(os.path.dirname(__file__), 'survival_comparison.png')
        graph_y = 550
        if os.path.exists(graph_path):
            try:
                graph_image = pygame.image.load(graph_path)
                # Scale the graph to fit the screen width
                graph_width = min(SCREEN_WIDTH - 100, 800)
                graph_height = int(graph_width * 0.6)  # Maintain aspect ratio
                graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))
                
                # Position the graph below the text
                graph_rect = graph_image.get_rect(center=(SCREEN_WIDTH // 2, graph_y + graph_height // 2))
                scroll_surface.blit(graph_image, graph_rect)
                
                # Move the restart button below the graph
                button_y = graph_rect.bottom + 30
            except pygame.error:
                # If there's an error loading the graph, position the button at the default position
                button_y = graph_y + 300
        else:
            button_y = graph_y + 300
        
        # Calculate the maximum scroll value based on content height
        self.max_scroll = max(0, button_y + 100 - SCREEN_HEIGHT)
        
        # Draw restart button on the scroll surface
        hover = pygame.Rect(SCREEN_WIDTH // 2 - 125, button_y, 250, 70).collidepoint(
            pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] + self.scroll_y)
        button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 125, button_y, 250, 70)
        pygame.draw.rect(scroll_surface, GRAY if not hover else (220, 220, 220), button_rect, border_radius=5)
        pygame.draw.rect(scroll_surface, BLACK, button_rect, 2, border_radius=5)
        
        # Center the text on the button
        button_text = self.font.render("Play Again", True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        scroll_surface.blit(button_text, button_text_rect)
        
        # Store the button rect for click detection, adjusted for scroll position
        self.button_rects = [pygame.Rect(button_rect.x, button_rect.y - self.scroll_y, button_rect.width, button_rect.height)]
        
        # Draw scroll instructions
        self.draw_text_on_surface(scroll_surface, "Use mouse wheel to scroll", self.font, BLUE, 
                               SCREEN_WIDTH // 2, button_y + 100, centered=True)
        
        # Draw scrollbar
        if self.max_scroll > 0:
            scrollbar_height = min(SCREEN_HEIGHT * SCREEN_HEIGHT / total_height, SCREEN_HEIGHT)
            scrollbar_pos = (self.scroll_y / self.max_scroll) * (SCREEN_HEIGHT - scrollbar_height)
            scrollbar_rect = pygame.Rect(SCREEN_WIDTH - 20, scrollbar_pos, 10, scrollbar_height)
            pygame.draw.rect(scroll_surface, (150, 150, 150), scrollbar_rect, border_radius=5)
        
        # Blit the visible portion of the scroll surface to the screen
        self.screen.blit(scroll_surface, (0, 0), (0, self.scroll_y, SCREEN_WIDTH, SCREEN_HEIGHT))
        
    def draw_text_on_surface(self, surface, text, font, color, x, y, centered=False):
        """Draw text on a specific surface"""
        text_surface = font.render(text, True, color)
        if centered:
            text_rect = text_surface.get_rect(center=(x, y))
        else:
            text_rect = text_surface.get_rect(topleft=(x, y))
        surface.blit(text_surface, text_rect)
        return text_rect
    
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
    # Set NumPy random seed based on current time for different outcomes each run
    np.random.seed(int(pygame.time.get_ticks()) % 10000000)
    
    # Load configuration
    config = load_config()
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bandit Game")
    clock = pygame.time.Clock()
    
    # Enable mouse wheel events
    pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL])
    
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
                    # Reset scroll position
                    ui.scroll_y = 0
            elif event.type == pygame.MOUSEWHEEL:
                # Handle scrolling in game over screen
                if session.game_over:
                    # Scroll up or down based on wheel direction
                    ui.scroll_y = max(0, min(ui.max_scroll, ui.scroll_y - event.y * ui.scroll_speed))
        
        # Draw the game screen
        ui.draw_game_screen(mouse_pos)
        
        # Update the display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
