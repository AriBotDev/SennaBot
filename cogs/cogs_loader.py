"""
Dynamic cog loader for SennaBot.
Handles cog discovery and loading.
"""
import asyncio
import importlib
import os
import sys
import pkgutil
from discord.ext import commands
from athena.debug_tools import DebugTools

# Setup debugger
debug = DebugTools.get_debugger("cogs_loader")

async def setup(bot: commands.Bot):
    """
    Main entry point for loading all cogs.
    Called when bot.load_extension("cogs") is executed.
    """
    debug.log("Beginning cog loading process")
    
    # Load base cog class first
    try:
        from .cog_base import BotCog
        debug.log("Loaded base cog class")
    except Exception as e:
        debug.log(f"Error loading base cog class: {e}")
        return
    
    # Load cogs from directories
    loaded_count = 0
    
    # Define base cog directories to search
    cog_dirs = [
        "cogs.general",
        "cogs.admin",
        "cogs.economy"
    ]
    
    # Load cogs from each directory
    for cog_dir in cog_dirs:
        try:
            # Try to load the module directory
            try:
                module = importlib.import_module(cog_dir)
                debug.log(f"Loaded module directory {cog_dir}")
            except ImportError:
                debug.log(f"Module directory {cog_dir} doesn't exist yet, creating...")
                
                # Create directory if it doesn't exist yet
                parts = cog_dir.split('.')
                current_path = parts[0]
                for part in parts[1:]:
                    current_path = os.path.join(current_path, part)
                    os.makedirs(current_path, exist_ok=True)
                    init_file = os.path.join(current_path, "__init__.py")
                    if not os.path.exists(init_file):
                        with open(init_file, "w") as f:
                            f.write("# Cog package\n")
                
                # Try again to import
                try:
                    module = importlib.import_module(cog_dir)
                    debug.log(f"Created and loaded module directory {cog_dir}")
                except ImportError:
                    debug.log(f"Still can't load module directory {cog_dir}, skipping")
                    continue
            
            # Check for module file (e.g., general_module.py)
            module_name = f"{cog_dir}.{cog_dir.split('.')[-1]}_module"
            try:
                await bot.load_extension(module_name)
                debug.log(f"Loaded module file {module_name}")
                loaded_count += 1
            except Exception as e:
                debug.log(f"Could not load module file {module_name}: {e}")
                
                # Create the module file if it doesn't exist
                try:
                    parts = module_name.split('.')
                    file_path = os.path.join(*parts[:-1], f"{parts[-1]}.py")
                    if not os.path.exists(file_path):
                        with open(file_path, "w") as f:
                            f.write(f"""\"\"\"
{parts[-2].capitalize()} module initialization.
Handles setup for {parts[-2]} cogs.
\"\"\"
from discord.ext import commands
from athena.debug_tools import DebugTools

# Setup debugger
debug = DebugTools.get_debugger("{parts[-2]}_module")

async def setup(bot: commands.Bot):
    \"\"\"Set up the {parts[-2]} module.\"\"\"
    debug.log("Setting up {parts[-2]} module")
    
    # This will be populated with actual cogs later
    debug.log("{parts[-2]} module setup complete")
""")
                        debug.log(f"Created module file {file_path}")
                except Exception as create_err:
                    debug.log(f"Error creating module file: {create_err}")
            
        except Exception as e:
            debug.log(f"Error loading cog directory {cog_dir}: {e}")
    
    debug.log(f"Loaded {loaded_count} cogs")