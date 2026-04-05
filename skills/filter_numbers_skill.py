# FILENAME: filter_numbers_skill.py

# PLAN
# Goal: Filter the list [10, 20, 30, 40, 50] to find numbers divisible by 3 and format them as a bulleted list.
# Logic Steps:
# 1. Define the input list of numbers: [10, 20, 30, 40, 50].
# 2. Use a list comprehension to identify numbers where the remainder of division by 3 is zero.
# 3. Format the identified numbers into a string where each number is preceded by a bullet point (dash and space) and followed by a newline.
# 4. Return the resulting formatted string.
# Required Libraries: None.

class BaseSkill:
    def execute(self, **kwargs):
        """Base method to be overridden by subclasses."""
        pass

class GeneratedSkill(BaseSkill):
    def execute(self, **kwargs):
        """
        Filters a hardcoded list for numbers divisible by 3 and returns a bulleted string.
        """
        # Input data
        numbers = [10, 20, 30, 40, 50]
        
        # Filter logic: check if number % 3 == 0
        divisible_by_three = [num for num in numbers if num % 3 == 0]
        
        # Formatting logic: create bulleted list
        # Using a list comprehension to create strings like "- 30"
        bulleted_items = [f"- {num}" for num in divisible_by_three]
        
        # Join items with newlines to form the final list string
        result = "\n".join(bulleted_items)
        
        return result

# Example usage:
# skill = GeneratedSkill()
# print(skill.execute())
[Output: - 30]
