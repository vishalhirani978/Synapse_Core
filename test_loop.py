import os
import sys
import time
import datetime
import json
from groq import Groq
from dotenv import load_dotenv

# Ensure stdout can handle emojis without throwing UnicodeEncodeError
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
from core.coder import CoderAgent
from core.reviewer import ReviewerAgent
from core.sandbox import SandboxManager
from core.tools.file_manager import read_local_file, write_local_file
from core.tools.web_search import search_web


def log_session(attempt, result, error=""):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(log_dir, "session.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Attempt: {attempt} | Result: {result} | Error: {error}\n")

def find_existing_skill(user_task):
    skills_dir = "skills"
    if not os.path.exists(skills_dir):
        return "NONE"
        
    skills_files = [f for f in os.listdir(skills_dir) if f.endswith(".py")]
    if not skills_files:
        return "NONE"
        
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"You are the Synapse Core Librarian. Given the task [{user_task}] and these scripts [{skills_files}], return ONLY the filename if a match exists, or \"NONE\"."
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        result = completion.choices[0].message.content.strip()
        # Some models might still return quotes or a path, clean it up
        result = result.strip("'\"")
        if result in skills_files:
            return result
        return "NONE"
    except Exception as e:
        print(f"⚠️ [MEMORY] Exception during memory check: {e}")
        return "NONE"

def start_agentic_loop(task, max_retries=3):
    skills_dir = "skills"
    os.makedirs(skills_dir, exist_ok=True)
    
    # --- PART 3: THE INTEGRATED DISPATCHER ---
    
    # 1. THE META-PATH (Self-Analysis)
    # Check if the user wants to explain/analyze a project file
    meta_prompt = f"You are the Synapse Core Meta-Analyst. Determine if the following task is asking to 'read', 'explain', or 'analyze' a specific project file: [{task}]. If yes, return ONLY the filepath of that file (no extra text, no reasoning). If no, return NONE."
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": meta_prompt}],
            temperature=0.0
        )
        meta_result = completion.choices[0].message.content.strip().strip("'\"")
        
        # Stricter cleaning of LLM output
        if "\n" in meta_result: meta_result = meta_result.split("\n")[0].strip()
        if ":" in meta_result and not (meta_result.startswith("/") or meta_result[1:3] == ":\\"): 
             # Catch things like "Filepath is: core/coder.py"
             meta_result = meta_result.split(":")[-1].strip()

        if meta_result != "NONE":
            print(f"📂 [FILE SYSTEM] Meta-Path triggered for: {meta_result}")
            content = read_local_file(meta_result)
            
            if content == "Access Denied":
                print(f"🚫 [SECURITY] Access Denied to file: {meta_result}")
                log_session("N/A", "META-PATH REJECTED", f"Security violation for {meta_result}")
                return # Exit early on security violation
            
            if content.startswith("Error reading file:"):
                print(f"❌ [FILE SYSTEM] {content}")
                # Let it fall through to regular loops if it's just a read error
            else:
                print(f"✅ [FILE SYSTEM] File read successfully. Providing LLM explanation...")
                explain_prompt = f"As the Synapse Core Expert, explain the following code from '{meta_result}' in the context of the task '{task}':\n\n{content}"
                # Use Gemini for explanation if possible, fallback to Groq
                try:
                    coder = CoderAgent()
                    response = coder.model.generate_content(explain_prompt)
                    explanation = response.text
                except Exception:
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": explain_prompt}]
                    )
                    explanation = completion.choices[0].message.content
                
                print("="*30)
                print(f"🤖 [META-ANALYSIS RESULT]:\n{explanation.strip()}")
                print("="*30)
                log_session("N/A", "META-PATH SUCCESS", f"Analyzed {meta_result}")
                return
    except Exception as e:
        print(f"⚠️ [META-PATH] Exception during check: {e}")

    # 2. THE MEMORY-PATH (Efficiency)
    skill_file = find_existing_skill(task)
    if skill_file != "NONE":
        skill_path = os.path.join(skills_dir, skill_file)
        if os.path.exists(skill_path):
            print(f"🔍 [MEMORY] Match found: {skill_file}. Bypassing Coder...")
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

    # 3. THE CREATION-PATH (Agentic Loop)
    print("🔄 [DISPATCHER] No Meta or Memory match. Initializing Agentic Loop...")

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
            search_results = search_web(query)
            search_context += f"\n\nWEB DATA FOR INJECTION: {search_results}\nWrite a static skill using this data.\n"
            print("✅ [SEARCH] Results retrieved. Sending back to Coder without incrementing attempt...")
            continue
            
        elif suggested_filename == "READ":
            filepath = generated_code.strip()
            print(f"📄 [READ] Coder requested to read file: '{filepath}'")
            try:
                content = read_local_file(filepath)
                print(f"✅ [READ] File '{filepath}' retrieved. Asking LLM for explanation...")
                explain_prompt = f"Given the user task: '{task}', analyze and explain the following file content from '{filepath}':\n\n{content}"
                try:
                    response_text = coder.model.generate_content(explain_prompt).text
                except Exception as ex:
                    client_inner = Groq(api_key=os.environ.get("GROQ_API_KEY"))
                    completion = client_inner.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": explain_prompt}]
                    )
                    response_text = completion.choices[0].message.content
                print("="*30)
                print(f"🤖 [EXPLANATION (Bypassing Cage)]:\n{response_text.strip()}")
                print("="*30)
                log_session(attempt, "READ & EXPLAIN SUCCESS")
                return
            except Exception as e:
                print(f"❌ [READ FAILURE] Error reading file: {e}")
                error_feedback = f"Failed to read local file '{filepath}': {e}"
                attempt += 1
                continue
                
        elif suggested_filename.startswith("WRITE:"):
            filepath = suggested_filename.split(":", 1)[1].strip()
            code_content = generated_code.strip()
            print(f"💾 [WRITE] Coder requested to write to file: '{filepath}'")
            try:
                write_local_file(filepath, code_content)
                print(f"✅ [WRITE] File '{filepath}' successfully saved! Bypassing Cage.")
                log_session(attempt, "WRITE SUCCESS")
                return
            except Exception as e:
                print(f"❌ [WRITE FAILURE] Error writing file: {e}")
                error_feedback = f"Failed to write local file '{filepath}': {e}"
                attempt += 1
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
    my_task = "Write a skill called bitcoin_price_skill.py that uses the requests library to fetch the live Bitcoin price in USD from the CoinGecko API. Ensure it prints only the numeric price"
    start_agentic_loop(my_task)
    
