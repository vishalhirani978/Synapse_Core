import docker
import os

class SandboxManager:
    def __init__(self) -> None:
        """Initialize the Docker client from the environment."""
        try:
            self.client = docker.from_env()
        except Exception as e:
            print(f"❌ Docker Error: Make sure Docker Desktop is running! {e}")

    def run_in_container(self, local_dir: str, command: str) -> str:
        """
        Runs a command inside a python:3.11-slim Docker container.
        
        Args:
            local_dir (str): The local directory path to mount (e.g., your 'skills' folder).
            command (str): The full command to run (e.g., 'python3 -c "..."').
            
        Returns:
            str: The output from the container.
        """
        image_name = "python:3.11-slim"
        
        # 1. Ensure the image is available
        try:
            self.client.images.get(image_name)
        except docker.errors.ImageNotFound:
            print(f"🐳 Pulling {image_name}... please wait.")
            self.client.images.pull(image_name)
            
        # 2. Execute the command
        # We pass the command directly as a string to allow python -c flags
        try:
            output = self.client.containers.run(
                image=image_name,
                command=command,
                volumes={
                    os.path.abspath(local_dir): {
                        'bind': '/app',
                        'mode': 'rw' # Changed to 'rw' so scripts can write logs if needed
                    }
                },
                working_dir='/app',
                remove=True,
                stdout=True,
                stderr=True
            )
            
            return output.decode("utf-8").strip()
            
        except docker.errors.ContainerError as e:
            # This captures actual Python errors inside the container
            raise Exception(e.stderr.decode("utf-8"))