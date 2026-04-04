import importlib
import inspect
import os
from core.base_skill import BaseSkill

class PluginManager:
    def __init__(self, plugin_package="skills"):
        self.plugin_package = plugin_package
        self.plugins = {}

    def load_plugins(self):
        # Determine the path to the skills directory relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        package_dir = os.path.join(base_dir, self.plugin_package)
        
        if not os.path.exists(package_dir):
            print(f"Plugin directory '{package_dir}' does not exist.")
            return

        for filename in os.listdir(package_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = f"{self.plugin_package}.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                            # Instantiate the skill class
                            self.plugins[name] = obj()
                except Exception as e:
                    print(f"Error loading module {module_name}: {e}")

    def get_plugins(self):
        return self.plugins
