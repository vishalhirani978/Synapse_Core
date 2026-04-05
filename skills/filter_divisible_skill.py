# FILENAME: filter_divisible_skill.py

# PLAN
# Goal: Filter a list of numbers [10, 20, 30, 40, 50] to find those divisible by 3 and return them as a bulleted list.
# Logic Steps:
# 1. Define the input list containing [10, 20, 30, 40, 50].
# 2. Use a list comprehension to filter the list for numbers where number % 3 == 0.
# 3. Format the resulting numbers into a string where each number is on a new line, prefixed by a hyphen and a space.
# 4. Return the final formatted string.
# Required Libraries: None.

class BaseSkill:
    def execute(self, **kwargs):
        """
        Base execute method to be overridden by subclasses.
        """
        raise NotImplementedError("The execute method must be implemented by the subclass.")

class GeneratedSkill(BaseSkill):
    def execute(self, **kwargs):
        """
        Filters the specific list [10, 20, 30, 40, 50] for divisibility by 3
        and returns the results as a bulleted string.
        """
        # Define the target list
        numbers = [10, 20, 30, 40, 50]
        
        # Filter for numbers divisible by 3
        divisible_by_three = [num for num in numbers if num % 3 == 0]
        
        # Format the numbers as a bulleted list string
        # Each item will be prefixed with '- ' and joined by newlines
        bulleted_list = "\n".join(f"- {num}" for num in divisible_by_three)
        
        return bulleted_list
