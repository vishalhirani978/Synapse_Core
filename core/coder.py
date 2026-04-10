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
        prompt = f"""You are an Agentic Coder. You have access to three REGISTERED SYSTEM TOOLS for project intelligence and file management.

REGISTERED TOOLS:
1. Web Search: Output `# SEARCH: <your query>` (Use for offline data injection).
2. Local File Manager (READ): Output `# READ: <filepath>` (Use to inspect or analyze existing code).
3. Local File Manager (WRITE): Output `# WRITE: <filepath>` on the first line, followed by content (Use to persist project changes).

CRITICAL: You are in 'One-Shot' mode. If you are NOT using a tool, you must write a skill script to solve the task.

IMPORTANT: If the task asks you to read, inspect, or explain a file, you MUST use the `# READ: <filepath>` tool. The dispatcher will handle the explanation.

When writing a skill script, your task is to write Standalone Python code containing a class that inherits from `BaseSkill`.

Task description:
{task_description}

Requirements (ONLY if writing a skill script, skip if using a tool like # READ:):
1. You MUST first generate a suggested filename for this script as the very first line of your output, in this format: `# FILENAME: suggested_filename.py`
3. You MUST then generate a 'PLAN' in python comments at the very top of the file. This plan should include: Goal, Logic Steps, and Required Libraries.
4. The code MUST explicitly define `class BaseSkill:` and its `execute(self, **kwargs)` method inside the generated string. Do NOT try to import it from `core` (no `from core import ...`).
5. Your skill class MUST be named `GeneratedSkill` and inherit from the `BaseSkill` class you defined.
6. The `GeneratedSkill` class MUST implement the `execute(self, **kwargs)` method.
7. CRITICAL — execute() must RETURN its final value. Do NOT call print() inside execute(). The dispatcher calls print(skill.execute()), so printing inside execute() causes a duplicate 'None' line in the output.
8. You are ALLOWED to fetch live data from reputable public APIs (e.g., CoinGecko, OpenWeatherMap, GitHub API). PREFER `urllib.request` and `json` (Python built-ins, always available) over `requests` to avoid ModuleNotFoundError in the execution sandbox. Do NOT hardcode values for tasks that explicitly ask for live/real-time data.
9. You MUST return ONLY the raw Python code. Do not include markdown formatting such as ```python or ``` at the end. Do not include any text explanations. ONLY the raw runnable Python code.
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
        elif lines and lines[0].startswith("# READ:"):
            filepath = lines[0].split(":", 1)[1].strip()
            return "READ", filepath
        elif lines and lines[0].startswith("# WRITE:"):
            filepath = lines[0].split(":", 1)[1].strip()
            return f"WRITE:{filepath}", "\n".join(lines[1:]) + "\n"
        elif lines and lines[0].startswith("# FILENAME:"):
            filename = lines[0].split(":", 1)[1].strip()
            # Remove the first line from the code if we want, or just leave it as a comment.
            # Leaving it as a comment is perfectly fine for python.
            
        return filename, text + "\n"
