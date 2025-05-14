# Bandit Game

A simple Pygame-based game where you must choose medicines for different people, with survival rates based on the person's attributes and the medicine's effectiveness.

## Game Rules

1. Each person has two attributes:
   - Gender: Male or Female
   - Age: Young or Old

2. Each medicine has different effectiveness rates for different types of people:
   - (Male, Young): effective_rate_1
   - (Male, Old): effective_rate_2
   - (Female, Young): effective_rate_3
   - (Female, Old): effective_rate_4

3. Game session is defined by:
   - Number of persons (default: 10)
   - Number of medicines (default: 3)

4. Gameplay:
   - For each person, you choose a medicine
   - Based on the person's attributes, the game calculates the probability of survival
   - The result (Survived or Died) is determined by a Bernoulli distribution
   - At the end, the game shows statistics of how many survived and died

## Installation

1. Make sure you have Python installed (Python 3.6 or higher recommended)
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## How to Run

```
python bandit_game.py
```

## Controls

- Use the mouse to click on buttons
- Select medicines by clicking on them
- Click "Continue" to move to the next person
- Click "Play Again" at the end to restart the game
