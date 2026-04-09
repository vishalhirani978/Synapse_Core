import os
import json
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class ReviewerAgent:
    def __init__(self, model_name="gemini-flash-latest"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def review_code(self, code: str, task: str) -> str:
        if "import requests" in code or "import urllib" in code:
            return "FAILED: Network calls are forbidden. Hardcode the values from the search results instead."

        prompt = f"""You are a Senior Security Engineer and Expert Python Reviewer.
Your task is to review the following Python code that was generated to solve a specific task.
You must strictly return a pure string.
If the code is safe, logical, and correctly addresses the task without obvious security issues or critical logic flaws, return EXACTLY: "PASSED".
If the code has security risks, unsafe OS commands, or fails to logically address the task cleanly, return EXACTLY: "FAILED: [Reason]".

You must ACCEPT skills that return hardcoded/static values if they were derived from the 'WEB DATA FOR INJECTION' search results. Since the execution sandbox is offline, hardcoding the latest search result is the ONLY way to fulfill the task. Do NOT demand API calls or external libraries like requests.

Task:
{task}

Code to Review:
{code}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
        except ResourceExhausted:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            text = completion.choices[0].message.content.strip()
        
        # Clean up code blocks if it accidentally adds them
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("\n", 1)[0]
            
        return text.strip()

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
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
        except ResourceExhausted:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            text = completion.choices[0].message.content.strip()
        
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
