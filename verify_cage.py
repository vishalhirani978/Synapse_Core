import os
from core.sandbox import SandboxManager

def verify():
    print("[SYSTEM] Talking to the Docker Whale...")
    try:
        # Create a dummy test file
        test_file = "test_script.py"
        with open(test_file, "w") as f:
            f.write("import sys; print('Python ' + sys.version.split()[0])\n")
            
        sb = SandboxManager()
        # We're asking the container to run our test script from the current directory
        local_dir = os.path.abspath(os.path.dirname(__file__))
        
        output = sb.run_in_container(local_dir, test_file)
        print(f"[SUCCESS] Container is alive! Output: {output.strip()}")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print(f"[FAILURE] The Cage is broken: {e}")

if __name__ == "__main__":
    verify()