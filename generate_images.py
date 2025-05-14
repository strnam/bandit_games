import pygame
import os

# Initialize pygame
pygame.init()

# Ensure images directory exists
if not os.path.exists("images"):
    os.makedirs("images")

# Constants
WIDTH, HEIGHT = 150, 150
MALE_COLOR = (180, 200, 255)  # Light blue for male
FEMALE_COLOR = (255, 180, 200)  # Light pink for female
YOUNG_HAIR = (50, 50, 50)  # Dark hair for young
OLD_HAIR = (200, 200, 200)  # Gray hair for old

def create_person_image(gender, age):
    # Create a surface for the image
    surface = pygame.Surface((WIDTH, HEIGHT))
    
    # Choose background color based on gender
    bg_color = MALE_COLOR if gender == "male" else FEMALE_COLOR
    surface.fill(bg_color)
    
    # Draw a simple person silhouette
    # Head
    head_color = (80, 80, 80)
    pygame.draw.circle(surface, head_color, (75, 50), 25)
    
    # Body
    body_color = (100, 100, 100)
    pygame.draw.rect(surface, body_color, (60, 75, 30, 50))
    
    # Legs
    pygame.draw.line(surface, body_color, (65, 125), (55, 145), 3)
    pygame.draw.line(surface, body_color, (85, 125), (95, 145), 3)
    
    # Arms
    pygame.draw.line(surface, body_color, (60, 85), (40, 95), 3)
    pygame.draw.line(surface, body_color, (90, 85), (110, 95), 3)
    
    # Add gender-specific details
    if gender == "male":
        # Male features (e.g., shorter hair)
        hair_color = OLD_HAIR if age == "old" else YOUNG_HAIR
        pygame.draw.rect(surface, hair_color, (60, 25, 30, 10))
    else:
        # Female features (e.g., longer hair)
        hair_color = OLD_HAIR if age == "old" else YOUNG_HAIR
        pygame.draw.rect(surface, hair_color, (50, 25, 50, 15))
        pygame.draw.rect(surface, hair_color, (45, 40, 10, 20))
        pygame.draw.rect(surface, hair_color, (95, 40, 10, 20))
    
    # Add age-specific details
    if age == "old":
        # Draw wrinkles for old
        pygame.draw.line(surface, (0, 0, 0), (65, 45), (70, 45), 1)
        pygame.draw.line(surface, (0, 0, 0), (80, 45), (85, 45), 1)
        # Walking stick
        pygame.draw.line(surface, (139, 69, 19), (45, 75), (55, 125), 3)
    else:
        # Younger appearance
        # Maybe a hat or different hairstyle for young
        if gender == "male":
            pygame.draw.rect(surface, (50, 50, 50), (60, 25, 30, 10))
    
    # Add text labels
    font = pygame.font.SysFont(None, 20)
    gender_text = font.render(gender.capitalize(), True, (0, 0, 0))
    age_text = font.render(age.capitalize(), True, (0, 0, 0))
    
    # Position the text
    surface.blit(gender_text, (75 - gender_text.get_width() // 2, 130))
    surface.blit(age_text, (75 - age_text.get_width() // 2, 110))
    
    # Add a border
    pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 2)
    
    return surface

# Generate images for all combinations
for gender in ["male", "female"]:
    for age in ["young", "old"]:
        image = create_person_image(gender, age)
        filename = f"{gender}_{age}.png"
        filepath = os.path.join("images", filename)
        pygame.image.save(image, filepath)
        print(f"Created {filepath}")

print("All images generated successfully!")
