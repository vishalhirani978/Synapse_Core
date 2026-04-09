import os
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

class CoderAgent:
    def __init__(self, model_name="gemini-flash-latest"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_skill(self, task_description: str) -> tuple[str, str]:
        prompt = f"""You are an Agentic Coder. If you need real-time data (weather, prices, news), call the 'search_web' tool before writing your code. To do this, output EXACTLY ONE LINE in this format: `# SEARCH: <your query>`. Do not output any code when requesting a search.
CRITICAL: You are in 'One-Shot' mode. You have ONE attempt to write the skill correctly using search data. Hardcode all values. Any use of 'requests', 'urllib', or network libraries will result in immediate system failure. Be concise and accurate.
Your task is to write Standalone Python code containing a class that inherits from `BaseSkill` to solve the given task.

Task description:
{task_description}

Requirements:
1. If you are ready to write code, you MUST first generate a suggested filename for this script as the very first line of your output, in this format: `# FILENAME: suggested_filename.py`
3. You MUST then generate a 'PLAN' in python comments at the very top of the file. This plan should include: Goal, Logic Steps, and Required Libraries.
4. The code MUST explicitly define `class BaseSkill:` and its `execute(self, **kwargs)` method inside the generated string. Do NOT try to import it from `core` (no `from core import ...`).
5. Your skill class MUST be named `GeneratedSkill` and inherit from the `BaseSkill` class you defined.
6. The `GeneratedSkill` class MUST implement the `execute(self, **kwargs)` method.
7. You MUST return ONLY the raw Python code. Do not include markdown formatting such as ```python or ``` at the end. Do not include any text explanations. ONLY the raw runnable Python code.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text
        except ResourceExhausted:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            text = completion.choices[0].message.content
        
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
        if lines and lines[0].startswith("# SEARCH:"):
            query = lines[0].split(":", 1)[1].strip()
            return "SEARCH", query
        elif lines and lines[0].startswith("# FILENAME:"):
            filename = lines[0].split(":", 1)[1].strip()
            # Remove the first line from the code if we want, or just leave it as a comment.
            # Leaving it as a comment is perfectly fine for python.
            
        return filename, text + "\n"
