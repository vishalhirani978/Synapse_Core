import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ReviewerAgent:
    def __init__(self, model_name="gemini-flash-latest"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def review_code(self, code: str, task: str) -> dict:
        prompt = f"""You are a Senior Security Engineer and Expert Python Reviewer.
Your task is to review the following Python code that was generated to solve a specific task.
You must strictly return a JSON object with two fields: "status" and "feedback".
If the code is safe, logical, and correctly addresses the task without obvious security issues or critical logic flaws, set "status" to "APPROVED" and "feedback" to "".
If the code has security risks, unsafe OS commands, or fails to logically address the task cleanly, set "status" to "REJECTED" and provide the reason in "feedback".

Do not wrap your response in markdown code blocks. Return ONLY the raw JSON object.

Task:
{task}

Code to Review:
{code}
"""
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up markdown if the model returns it
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            result = json.loads(text)
            if "status" not in result:
                result["status"] = "REJECTED"
                result["feedback"] = "Reviewer returned invalid response missing 'status'."
            return result
        except json.JSONDecodeError as e:
            return {
                "status": "REJECTED",
                "feedback": f"Reviewer failed to return valid JSON. Raw output: {text}. Error: {e}"
            }

    def verify_result(self, task: str, actual_output: str) -> dict:
        prompt = f"""You are an Expert QA Tester.
Your task is to verify if the actual output from a Python script successfully solves the given task.
You must strictly return a JSON object.
If the actual output indicates that the task was solved correctly, return {{"status": "SUCCESS"}}.
If the output is incorrect, missing, or shows an error, return {{"status": "FAILURE", "feedback": "Explanation of why it failed or what is missing"}}.

Do not wrap your response in markdown code blocks. Return ONLY the raw JSON object.

Task:
{task}

Actual Output:
{actual_output}
"""
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up markdown if the model returns it
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            result = json.loads(text)
            if "status" not in result:
                result["status"] = "FAILURE"
                result["feedback"] = "Reviewer returned invalid response missing 'status'."
            return result
        except json.JSONDecodeError as e:
            return {
                "status": "FAILURE",
                "feedback": f"Reviewer failed to return valid JSON. Raw output: {text}. Error: {e}"
            }
