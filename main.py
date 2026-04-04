from core.plugin_manager import PluginManager

def main():
    print("Initializing PluginManager...")
    manager = PluginManager(plugin_package="skills")
    
    print("Loading skills...")
    manager.load_plugins()
    
    plugins = manager.get_plugins()
    print(f"Loaded {len(plugins)} skill(s).")
    
    skill_name = "DummySkill"
    if skill_name in plugins:
        print(f"Running {skill_name}...")
        skill = plugins[skill_name]
        result = skill.execute()
        print(result)
    else:
        print(f"Error: {skill_name} not found.")

if __name__ == "__main__":
    main()
