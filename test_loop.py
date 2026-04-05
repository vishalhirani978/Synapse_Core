import os
import time
import datetime
from core.coder import CoderAgent
from core.sandbox import SandboxManager

def log_session(attempt, result, error=""):
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/session.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Attempt: {attempt} | Result: {result} | Error: {error}\n")

def start_agentic_loop(task, max_retries=3):
    skill_file = "auto_generated_skill.py"
    skill_path = os.path.join("skills", skill_file)
    success_flag_path = os.path.join("skills", ".success")

    if os.path.exists(skill_path) and os.path.exists(success_flag_path):
        choice = input("A successful auto-generated skill already exists. Do you want to reuse it? (y/n): ").strip().lower()
        if choice == 'y':
            print("🚀 [SYSTEM] Reusing existing successful skill. Running in Cage...")
            sandbox = SandboxManager()
            try:
                test_cmd = 'python3 -c "from auto_generated_skill import GeneratedSkill; print(GeneratedSkill().execute())"'
                output = sandbox.run_in_container(os.path.abspath("skills"), test_cmd)
                print("="*30)
                print(f"📦 [CAGE RESULT (Reused)]:\n{output.strip()}")
                print("="*30)
            except Exception as e:
                print(f"❌ [CAGE FAILURE] Error: {e}")
            return
        else:
            print("🔄 [SYSTEM] Regenerating skill...")
            if os.path.exists(success_flag_path):
                os.remove(success_flag_path)
    coder = CoderAgent()
    sandbox = SandboxManager()
    
    print(f"\n🚀 [SYSTEM] Starting Task: {task}")
    
    attempt = 1
    error_feedback = ""

    while attempt <= max_retries:
        print(f"\n🧠 [ATTEMPT {attempt}] Coder is writing the skill...")
        
        # If the previous run failed, we pass the error back to the AI
        current_prompt = task
        if error_feedback:
            current_prompt = f"{task}\n\nNOTE: Your previous code failed with this error. Please fix it:\n{error_feedback}"

        # 1. Generate the code
        generated_code = coder.generate_skill(current_prompt)
        
        # 2. Save it to the skills folder
        os.makedirs("skills", exist_ok=True)
        skill_file = "auto_generated_skill.py"
        skill_path = os.path.join("skills", skill_file)
        
        with open(skill_path, "w") as f:
            f.write(generated_code)
        
        print(f"✅ [SYSTEM] Code saved to {skill_path}. Sending to the Cage...")
        time.sleep(1) # Give Windows a second to breathe

        # 3. Test it in the Docker Cage
        # 3. Test it in the Docker Cage
        try:
            test_cmd = 'python3 -c "from auto_generated_skill import GeneratedSkill; print(GeneratedSkill().execute())"'
            
            output = sandbox.run_in_container(os.path.abspath("skills"), test_cmd)
            
            print("="*30)
            print(f"📦 [CAGE RESULT]:\n{output.strip()}")
            print("="*30)

            # --- DAY 4 LOGIC GATE: VALIDATION ---
            # We check if the expected answer (55) is actually in the string
            if "55" in output:
                print("🎯 [SUCCESS] The Agentic Loop is complete and validated!")
                log_session(attempt, "SUCCESS")
                with open(success_flag_path, "w") as f:
                    f.write("success")
                return 
            else:
                print("⚠️ [LOGIC ERROR] Output received, but 55 was not found. Retrying...")
                error_feedback = f"The code ran but the answer was wrong. I expected 55, but got: {output}"
                log_session(attempt, "LOGIC ERROR", error_feedback)
                attempt += 1
            # ------------------------------------
            
        except Exception as e:
            print(f"❌ [CAGE FAILURE] Error: {e}")
            error_feedback = str(e)
            log_session(attempt, "CAGE FAILURE", error_feedback)
            attempt += 1
    print("\n💀 [FATAL] Max retries reached. The AI couldn't fix the code.")
    log_session(max_retries, "FATAL", "Max retries reached")

if __name__ == "__main__":
    # The ultimate test for a Nawabshah developer!
    my_task = "Create a skill that takes a list of numbers [10, 20, 30, 40, 50] and returns only the ones that are divisible by 3, formatted as a bulleted list"
    start_agentic_loop(my_task)