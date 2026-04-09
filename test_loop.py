import os
import time
import datetime
import json
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
from core.coder import CoderAgent
from core.reviewer import ReviewerAgent
from core.sandbox import SandboxManager

def get_registry_path():
    return os.path.join("skills", "skills_registry.json")

def load_registry():
    path = get_registry_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_registry(registry):
    path = get_registry_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4)

def log_session(attempt, result, error=""):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(log_dir, "session.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Attempt: {attempt} | Result: {result} | Error: {error}\n")

def find_existing_skill(task):
    skills_dir = "skills"
    if not os.path.exists(skills_dir):
        return None
        
    skills_files = [f for f in os.listdir(skills_dir) if f.endswith(".py")]
    if not skills_files:
        return None
        
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"Given these available skills: {skills_files}, does one of them directly solve the task: '{task}'? If yes, return the filename. If no, return 'NONE'. Return nothing but the filename or NONE."
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        result = completion.choices[0].message.content.strip()
        if result in skills_files:
            return result
    except Exception as e:
        print(f"⚠️ [MEMORY] Exception during memory check: {e}")
        pass
        
    return None

def start_agentic_loop(task, max_retries=3):
    skills_dir = "skills"
    os.makedirs(skills_dir, exist_ok=True)
    
    skill_file = find_existing_skill(task)
    if skill_file:
        skill_path = os.path.join(skills_dir, skill_file)
        if os.path.exists(skill_path):
            print(f"🧠 [MEMORY] Matching skill found: {skill_file}. Reusing existing logic...")
            sandbox = SandboxManager()
            try:
                module_name = skill_file[:-3] if skill_file.endswith(".py") else skill_file
                test_cmd = f'python3 -c "from {module_name} import GeneratedSkill; print(GeneratedSkill().execute())"'
                output = sandbox.run_in_container(os.path.abspath(skills_dir), test_cmd)
                print("="*30)
                print(f"📦 [CAGE RESULT (Reused)]:\n{output.strip()}")
                print("="*30)
                log_session("N/A", "ORCHESTRATED (Reused)", f"Matched skill: {skill_file}")
                return
            except Exception as e:
                print(f"❌ [CAGE FAILURE] Error running reused skill: {e}")
                log_session("N/A", "ORCHESTRATED FAILURE", str(e))

    print("🔄 [SYSTEM] No matching skill found. Proceeding with Agentic Loop...")

    coder = CoderAgent()
    sandbox = SandboxManager()
    
    print(f"\n🚀 [SYSTEM] Starting Task: {task}")
    
    attempt = 1
    error_feedback = ""
    search_context = ""
    search_count = 0
    last_attempt = 1

    while attempt <= max_retries:
        if attempt != last_attempt:
            search_count = 0
            last_attempt = attempt
        print(f"\n🧠 [ATTEMPT {attempt}] Coder is writing the skill...")
        
        # If the previous run failed, we pass the error back to the AI
        current_prompt = task + search_context
        if error_feedback:
            current_prompt += f"\n\nNOTE: Your previous code failed with this error. Please fix it:\n{error_feedback}"

        # 1. Generate the code
        suggested_filename, generated_code = coder.generate_skill(current_prompt)
        
        if suggested_filename == "SEARCH":
            if search_count >= 1:
                print(f"🚫 [SEARCH LIMIT] Coder tried to search again. Forcing it to use existing data.")
                error_feedback = "You are allowed ONLY ONE search query. You've already used it. Please write the Python code immediately using the data you already have."
                continue
                
            search_count += 1
            query = generated_code
            print(f"🔍 [SEARCH] Coder requested search for: '{query}'. Searching...")
            from core.tools.web_search import search_web
            search_results = search_web(query)
            search_context += f"\n\nWEB DATA FOR INJECTION: {search_results}\nWrite a static skill using this data.\n"
            print("✅ [SEARCH] Results retrieved. Sending back to Coder without incrementing attempt...")
            continue
        
        print(f"🕵️ [REVIEW] Sending code to the ReviewerAgent...")
        reviewer = ReviewerAgent()
        review_result = reviewer.review_code(generated_code, task)
        
        if review_result.startswith("FAILED"):
            feedback = review_result.split(":", 1)[1].strip() if ":" in review_result else review_result
            status = "REJECTED"
            print(f"🚫 [REVIEW REJECTED] {feedback}")
            error_feedback = f"Code Review Rejected your code: {feedback}"
            log_session(attempt, f"REVIEW {status}", feedback)
            attempt += 1
            continue
        
        status = "APPROVED"
        log_session(attempt, f"REVIEW {status}", "")

        print("✅ [REVIEW APPROVED] Proceeding to Sandbox execution...")

        # 2. Save it to the skills folder
        skill_file = suggested_filename
        skill_path = os.path.join(skills_dir, skill_file)
        
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
        
        print(f"✅ [SYSTEM] Code saved to {skill_path}. Sending to the Cage...")
        time.sleep(1) # Give Windows a second to breathe

        # 3. Test it in the Docker Cage
        try:
            module_name = skill_file[:-3] if skill_file.endswith(".py") else skill_file
            test_cmd = f'python3 -c "from {module_name} import GeneratedSkill; print(GeneratedSkill().execute())"'
            
            output = sandbox.run_in_container(os.path.abspath(skills_dir), test_cmd)
            
            print("="*30)
            print(f"📦 [CAGE RESULT]:\n{output.strip()}")
            print("="*30)

            # --- DYNAMIC VALIDATION ---
            if search_count >= 1 and "Traceback" not in output and "Error" not in output:
                print("🎯 [BYPASS] Search data used and cage executed cleanly. Bypassing extra QA...")
                val_status = "SUCCESS"
            else:
                print(f"🕵️ [QA] Sending output to the ReviewerAgent for dynamic validation...")
                validation_result = reviewer.verify_result(task, output.strip())
                val_status = validation_result.get("status", "FAILURE")
                val_feedback = validation_result.get("feedback", "No feedback provided.")

            if val_status == "SUCCESS":
                print("🎯 [SUCCESS] The Agentic Loop is complete and validated dynamically!")
                log_session(attempt, "GENERATED (New) - SUCCESS")
                
                # Add to registry
                registry = load_registry()
                registry[task] = skill_file
                save_registry(registry)
                
                return 
            else:
                print(f"⚠️ [LOGIC ERROR] Code executed, but QA rejected it: {val_feedback}")
                error_feedback = f"The code ran but the QA Reviewer rejected the output. QA Feedback: {val_feedback}"
                log_session(attempt, "GENERATED (New) - LOGIC ERROR", val_feedback)
                attempt += 1
            # ------------------------------------            
        except Exception as e:
            print(f"❌ [CAGE FAILURE] Error: {e}")
            error_feedback = str(e)
            log_session(attempt, "GENERATED (New) - CAGE FAILURE", error_feedback)
            attempt += 1
    print("\n💀 [FATAL] Max retries reached. The AI couldn't fix the code.")
    log_session(max_retries, "FATAL", "Max retries reached")

if __name__ == "__main__":
    # The ultimate test for a Nawabshah developer!
    my_task = "Find the current price of Bitcoin in USD and return it."
    start_agentic_loop(my_task)
