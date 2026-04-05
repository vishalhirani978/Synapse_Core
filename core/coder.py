import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

class CoderAgent:
    def __init__(self, model_name="gemini-flash-latest"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_skill(self, task_description: str) -> tuple[str, str]:
        prompt = f"""You are an expert Python developer.
Your task is to write Standalone Python code containing a class that inherits from `BaseSkill` to solve the given task.

Task description:
{task_description}

Requirements:
1. You MUST first generate a suggested filename for this script as the very first line of your output, in this exact format: `# FILENAME: suggested_filename.py`
2. You MUST then generate a 'PLAN' in python comments at the very top of the file. This plan should include: Goal, Logic Steps, and Required Libraries.
3. The code MUST explicitly define `class BaseSkill:` and its `execute(self, **kwargs)` method inside the generated string. Do NOT try to import it from `core` (no `from core import ...`).
4. Your skill class MUST be named `GeneratedSkill` and inherit from the `BaseSkill` class you defined.
5. The `GeneratedSkill` class MUST implement the `execute(self, **kwargs)` method.
6. You MUST return ONLY the raw Python code. Do not include markdown formatting such as ```python or ``` at the end. Do not include any text explanations. ONLY the raw runnable Python code.
"""
        response = self.model.generate_content(prompt)
        text = response.text
        
        # Clean up potential markdown formatting if the model fails to follow instructions
        text = text.strip()
        if text.startswith("```python"):
            text = text[9:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
            
        text = text.strip()
        lines = text.split("\n")
        filename = "auto_generated_skill.py"
        if lines and lines[0].startswith("# FILENAME:"):
            filename = lines[0].split(":", 1)[1].strip()
            # Remove the first line from the code if we want, or just leave it as a comment.
            # Leaving it as a comment is perfectly fine for python.
            
        return filename, text + "\n"
