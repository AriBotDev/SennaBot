"""
UI components for prison breakout interactions.
Provides the interactive views for breaking out prisoners from different prison tiers.
"""
import discord
import random
import time
import asyncio
from discord import app_commands, ui
from typing import List, Dict, Any, Tuple, Optional, Union
from athena.data_service import DataService
from athena.debug_tools import DebugTools
from ...economy_base import EconomyCog
from ...status.injury_system import get_injury_status, add_injury

# Setup debugger
debug = DebugTools.get_debugger("breakout_components")

class OfficerGroupBreakoutView(ui.View):
    """UI for breaking out a prisoner from the Officer Group prison."""
    
    def __init__(self, cog, interaction, target, target_prison):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction
        self.target = target
        self.target_prison = target_prison
        
        # Add door button
        self.add_item(ui.Button(emoji="🚪", style=discord.ButtonStyle.primary, custom_id="door"))
        self.children[0].callback = self.door_callback
    
    async def door_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        # Get escape chance from prison tier - use function-level import
        from ..prison_system import PRISON_TIERS
        tier = next((t for t in PRISON_TIERS if t[0] == "Officer Group"), None)
        escape_chance = tier[2] if tier else 75
        
        # Import at function level
        from ..prison_system import get_escape_chance_modifier
        escape_chance_mod = get_escape_chance_modifier(interaction.guild.id, interaction.user.id)
        escape_chance = max(5, escape_chance + escape_chance_mod)
        
        # Roll for success
        roll = random.randint(1, 100)
        if roll <= escape_chance:
            # Success
            # Free the target
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(self.target.id)
            if user_key in guild_data and guild_data[user_key].get("prison"):
                guild_data[user_key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Successful!",
                    description=f"You simply walked through the door and freed {self.target.mention} from the Officer Group.\n\n**(that was easy)**",
                    color=discord.Color.green()
                ),
                view=None
            )
        else:
            # Failure
            # Send to prison
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(interaction.user.id)
            if user_key not in guild_data:
                user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
                guild_data[user_key] = user_data
            
            # Import at function level
            from ..prison_system import PRISON_COOLDOWN
            guild_data[user_key]["prison"] = {
                "tier": "Officer Group", 
                "release_time": int(time.time()) + PRISON_COOLDOWN
            }
            DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Failed!",
                    description=f"You were caught trying to free {self.target.mention} from the Officer Group.\n\n**Now YOU have been sent to the Officer Group prison for 1 hour. (HOW????)**",
                    color=discord.Color.red()
                ),
                view=None
            )
        
        self.stop()

class OldGuardsBreakoutView(ui.View):
    """UI for breaking out a prisoner from the Old Guards prison."""
    
    def __init__(self, cog, interaction, target, target_prison):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction
        self.target = target
        self.target_prison = target_prison
        
        # Add key button
        self.add_item(ui.Button(emoji="🔑", style=discord.ButtonStyle.primary, custom_id="key"))
        self.children[0].callback = self.key_callback
    
    async def key_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        # Get escape chance from prison tier - use function-level import
        from ..prison_system import PRISON_TIERS
        tier = next((t for t in PRISON_TIERS if t[0] == "Old Guards"), None)
        escape_chance = tier[2] if tier else 65
        
        # Import at function level
        from ..prison_system import get_escape_chance_modifier
        escape_chance_mod = get_escape_chance_modifier(interaction.guild.id, interaction.user.id)
        escape_chance = max(5, escape_chance + escape_chance_mod)
        
        # Roll for success
        roll = random.randint(1, 100)
        if roll <= escape_chance:
            # Success
            # Free the target
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(self.target.id)
            if user_key in guild_data and guild_data[user_key].get("prison"):
                guild_data[user_key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Successful!",
                    description=f"You stole the keys while the Vanguard was sleeping and opened {self.target.mention}'s cell without making a noise.\n\n**You both escape from the Old Guards. (eepy zzz)**",
                    color=discord.Color.green()
                ),
                view=None
            )
        else:
            # Failure
            # Send to prison
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(interaction.user.id)
            if user_key not in guild_data:
                user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
                guild_data[user_key] = user_data
            
            # Import at function level
            from ..prison_system import PRISON_COOLDOWN
            guild_data[user_key]["prison"] = {
                "tier": "Old Guards", 
                "release_time": int(time.time()) + PRISON_COOLDOWN
            }
            DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Failed!",
                    description=f"You were caught trying to steal the keys to free {self.target.mention} from the sleeping Vanguard.\n\n**You've been sent to the Old Guards prison for 1 hour with them.**",
                    color=discord.Color.red()
                ),
                view=None
            )
        
        self.stop()

class SoldatBrigadeBreakoutView(ui.View):
    """UI for breaking out a prisoner from the Soldat Brigade prison."""
    
    def __init__(self, cog, interaction, target, target_prison):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction
        self.target = target
        self.target_prison = target_prison
        self.correct_door = random.randint(1, 2)
        
        # Add door buttons
        for i in range(1, 3):
            button = ui.Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"door_{i}")
            button.callback = self.door_callback
            self.add_item(button)
    
    async def door_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        choice = int(interaction.data["custom_id"].split("_")[1])
        
        if choice == self.correct_door:
            # Success
            # Free the target
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(self.target.id)
            if user_key in guild_data and guild_data[user_key].get("prison"):
                guild_data[user_key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Successful!",
                    description=f"You open the door to see {self.target.mention} inside!\n\n**You both escape from the Soldat Brigade.**",
                    color=discord.Color.green()
                ),
                view=None
            )
        else:
            # Failure
            # Send to prison
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(interaction.user.id)
            if user_key not in guild_data:
                user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
                guild_data[user_key] = user_data
            
            # Import at function level
            from ..prison_system import PRISON_COOLDOWN
            guild_data[user_key]["prison"] = {
                "tier": "Soldat Brigade", 
                "release_time": int(time.time()) + PRISON_COOLDOWN
            }
            DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Failed!",
                    description=f"You open the wrong door to a group of Soldats playing blackjack.\n\n**They put you in the same cell as {self.target.mention} for an hour. (womp womp)**",
                    color=discord.Color.red()
                ),
                view=None
            )
        
        self.stop()

class LancerLegionBreakoutView(ui.View):
    """UI for breaking out a prisoner from the Lancer Legion prison."""
    
    def __init__(self, cog, interaction, target, target_prison):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction
        self.target = target
        self.target_prison = target_prison
        self.correct_door = random.randint(1, 4)
        
        # Add door buttons
        for i in range(1, 5):
            button = ui.Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"door_{i}")
            button.callback = self.door_callback
            self.add_item(button)
    
    async def door_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        choice = int(interaction.data["custom_id"].split("_")[1])
        
        if choice == self.correct_door:
            # Success
            # Free the target
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(self.target.id)
            if user_key in guild_data and guild_data[user_key].get("prison"):
                guild_data[user_key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Successful!",
                    description=f"You open the door to {self.target.mention} playing cards with a wall.\n\n**You both escape from the Lancer Legion!**",
                    color=discord.Color.green()
                ),
                view=None
            )
            self.stop()
        else:
            # Second chance
            # Create new view with remaining doors
            second_view = ui.View(timeout=60)
            remaining_doors = [i for i in range(1, 5) if i != choice]
            self.correct_door = random.choice(remaining_doors)  # New correct door
            
            for i in remaining_doors:
                button = ui.Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"second_door_{i}")
                button.callback = self.second_chance_callback
                second_view.add_item(button)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Second Chance",
                    description="You open the door to an empty storage closet...\nYou overhear chatter far down the halls and soon realize the Lancer feast is about to conclude.\n\n**You do not have much time. Pick the correct door before the Legion catches on**",
                    color=discord.Color.orange()
                ),
                view=second_view
            )
    
    async def second_chance_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        choice = int(interaction.data["custom_id"].split("_")[2])
        
        if choice == self.correct_door:
            # Success
            # Free the target
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(self.target.id)
            if user_key in guild_data and guild_data[user_key].get("prison"):
                guild_data[user_key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Successful!",
                    description=f"You open the door to {self.target.mention} eating some scraps from the Lancer's feast.\n\n**You both escape from the Lancer Legion!**",
                    color=discord.Color.green()
                ),
                view=None
            )
        else:
            # Failure after second chance
            # Send to prison and add injury
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(interaction.user.id)
            if user_key not in guild_data:
                user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
                guild_data[user_key] = user_data
            
            # Import at function level
            from ..prison_system import PRISON_COOLDOWN
            guild_data[user_key]["prison"] = {
                "tier": "Lancer Legion", 
                "release_time": int(time.time()) + PRISON_COOLDOWN
            }
            
            # Add injury
            add_injury(interaction.guild.id, interaction.user)
            new_injury_status = get_injury_status(interaction.guild.id, interaction.user)
            
            DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Failed!",
                    description=f"You open the door to an empty prison cell...\n\nThe Lancers creep up behind you and push you straight into the cell as you **break your arm as you fall**.\n\n{self.target.mention} has a friend now :D\n\nYour condition is now **{new_injury_status['tier']}**.",
                    color=discord.Color.red()
                ),
                view=None
            )
        
        self.stop()

class RookDivisionBreakoutView(ui.View):
    """UI for breaking out a prisoner from the Rook Division prison."""
    
    def __init__(self, cog, interaction, target, target_prison):
        super().__init__(timeout=120)
        self.cog = cog
        self.interaction = interaction
        self.target = target
        self.target_prison = target_prison
        self.lockpick_durability = 4
        
        # Generate a sequence with UNIQUE numbers (1-4) using random.sample
        self.correct_sequence = random.sample(range(1, 5), 3)  # Generate a 3-pin sequence with unique numbers
        
        self.current_pin = 0  # Index of current pin we're trying to guess
        self.solved_pins = []  # Track which pins have been correctly guessed
        
        # Add pin buttons
        self.update_buttons()
    
    def update_buttons(self):
        """Update the buttons in the view based on remaining pins"""
        # Clear existing buttons
        self.clear_items()
        
        # Add buttons for pins not yet correctly guessed
        for i in range(1, 5):
            if i not in self.solved_pins:  # Only add buttons for pins that haven't been correctly guessed
                button = ui.Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"pin_{i}")
                button.callback = self.pin_callback
                self.add_item(button)
    
    async def pin_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        try:
            pin = int(interaction.data["custom_id"].split("_")[1])
            
            # Check if this pin matches the current position in the sequence
            if pin == self.correct_sequence[self.current_pin]:
                # Correct pin
                self.solved_pins.append(pin)  # Add to correctly guessed pins
                self.current_pin += 1  # Move to next pin in sequence
                
                if self.current_pin >= len(self.correct_sequence):
                    # All pins set correctly - success!
                    # Free the target
                    guild_data = DataService.load_guild_data(interaction.guild.id)
                    user_key = str(self.target.id)
                    if user_key in guild_data and guild_data[user_key].get("prison"):
                        guild_data[user_key]["prison"] = None
                        DataService.save_guild_data(interaction.guild.id, guild_data)
                    
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            title="Breakout Successful!",
                            description=f"After about a while, you successfully picked the lock and found {self.target.mention}'s cell.\n\n**You both break out from the Rook Division!**",
                            color=discord.Color.green()
                        ),
                        view=None
                    )
                    self.stop()
                else:
                    # Continue to next pin - update the view
                    success_embed = discord.Embed(
                        title="Lockpicking in Progress",
                        description=f"Pin set :D\n\n**Raise the next pin**\n*Lockpick Durability: ({self.lockpick_durability})*",
                        color=discord.Color.blue()
                    )
                    
                    # Update buttons in this view to reflect the solved pin
                    self.update_buttons()
                    await interaction.response.edit_message(embed=success_embed, view=self)
            else:
                # Wrong pin
                self.lockpick_durability -= 1
                
                if self.lockpick_durability <= 0:
                    # Lockpick broke - failure
                    # Send to prison and add injury
                    guild_data = DataService.load_guild_data(interaction.guild.id)
                    user_key = str(interaction.user.id)
                    if user_key not in guild_data:
                        user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
                        guild_data[user_key] = user_data
                    
                    # Import at function level
                    from ..prison_system import PRISON_COOLDOWN
                    guild_data[user_key]["prison"] = {
                        "tier": "Rook Division", 
                        "release_time": int(time.time()) + PRISON_COOLDOWN
                    }
                    
                    # Add injury
                    add_injury(interaction.guild.id, interaction.user)
                    new_injury_status = get_injury_status(interaction.guild.id, interaction.user)
                    
                    DataService.save_guild_data(interaction.guild.id, guild_data)
                    
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            title="Breakout Failed!",
                            description=f"Your lockpick broke...\n\n{self.target.mention} has been watching you do this for an hour unimpressed...\n\nThe Rook Division throws you in the cell right next to {self.target.mention} and incur an **injury while resisting**.\n\nYour condition is now **{new_injury_status['tier']}**.",
                            color=discord.Color.red()
                        ),
                        view=None
                    )
                    self.stop()
                else:
                    # Still have lockpick durability - continue trying with same buttons
                    failure_embed = discord.Embed(
                        title="Lockpicking in Progress",
                        description=f"Wrong pin D:\n\n**Try again**\n*Lockpick Durability: ({self.lockpick_durability})*",
                        color=discord.Color.orange()
                    )
                    
                    # Don't update the buttons - keep the same set
                    await interaction.response.edit_message(embed=failure_embed, view=self)
        except Exception as e:
            debug.log(f"Error in RookDivisionBreakoutView pin_callback: {e}")
            # Try to gracefully recover by sending a new message
            try:
                await interaction.followup.send(
                    "There was an error processing your lockpick attempt. Please try again.",
                    ephemeral=True
                )
            except:
                pass

class MorticianWingBreakoutView(ui.View):
    """UI for breaking out a prisoner from the Mortician Wing prison."""
    
    def __init__(self, cog, interaction, target, target_prison):
        super().__init__(timeout=120)
        self.cog = cog
        self.interaction = interaction
        self.target = target
        self.target_prison = target_prison
        
        # Drug data - Name and description pairs
        self.drugs = [
            ("Bicardine", "The prisoner you tested it on showed signs of their wounds healing."),
            ("Haloperidol", "The prisoner you tested it on became calm and focused."),
            ("Hydrocodone", "The prisoner you tested it on didn't feel pain for a bit."),
            ("Mephedrone", "The prisoner you tested it on showed signs of increased energy."),
            ("Synaptizine", "The prisoner you tested it on became restless."),
            ("Amatoxin", "The prisoner you tested it on had begun to cough and wheeze as they slowly begun to slump to the ground lifeless..")
        ]
        
        # Randomize which bottle is amatoxin and which drug is in each bottle
        self.remaining_bottles = ["red", "blue", "green", "purple", "yellow", "brown"]
        
        # Shuffle the drugs list to randomize which drug is in which bottle
        random.shuffle(self.drugs)
        
        # Create drug prompts dictionary
        self.drug_prompts = {}
        for i, bottle_color in enumerate(self.remaining_bottles):
            drug_name, drug_effect = self.drugs[i]
            self.drug_prompts[bottle_color] = f"The bottle contained **{drug_name}**.\n\n{drug_effect}"
        
        # Find which bottle has Amatoxin
        for bottle, prompt in self.drug_prompts.items():
            if "Amatoxin" in prompt:
                self.amatoxin_bottle = bottle
                break
        
        # Add color buttons
        self.color_emojis = {
            "red": "🔴", "blue": "🔵", "green": "🟢", 
            "purple": "🟣", "yellow": "🟡", "brown": "🟤"
        }
        
        for color, emoji in self.color_emojis.items():
            button = ui.Button(emoji=emoji, style=discord.ButtonStyle.secondary, custom_id=f"bottle_{color}")
            button.callback = self.bottle_callback
            self.add_item(button)
    
    async def bottle_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        color = interaction.data["custom_id"].split("_")[1]
        
        if color == self.amatoxin_bottle:
            # Picked the amatoxin - failure
            # Send to prison and set to Needs Surgery
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(interaction.user.id)
            if user_key not in guild_data:
                user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
                guild_data[user_key] = user_data
            
            # Import at function level
            from ..prison_system import PRISON_COOLDOWN
            guild_data[user_key]["prison"] = {
                "tier": "Mortician Wing", 
                "release_time": int(time.time()) + PRISON_COOLDOWN
            }
            
            # Set to Needs Surgery injury tier
            guild_data[user_key]["injuries"] = 3  # Set to Needs Surgery threshold
            guild_data[user_key]["injured"] = True
            DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Failed!",
                    description=f"You picked the {self.color_emojis[color]} bottle.\n\n{self.drug_prompts[color]}\n\nThe Morts immediately apprehend you and sticks **4 different stims into your bloodstream**.\nYou and {self.target.mention} become lab rats in the Mortician Wing.\n\nYour condition has worsened to **Needs Surgery**.",
                    color=discord.Color.red()
                ),
                view=None
            )
            self.stop()
        else:
            # Remove this bottle from options
            self.remaining_bottles.remove(color)
            
            # If only the amatoxin remains, success!
            if len(self.remaining_bottles) == 1 and self.remaining_bottles[0] == self.amatoxin_bottle:
                # Free the target
                guild_data = DataService.load_guild_data(interaction.guild.id)
                user_key = str(self.target.id)
                if user_key in guild_data and guild_data[user_key].get("prison"):
                    guild_data[user_key]["prison"] = None
                    DataService.save_guild_data(interaction.guild.id, guild_data)
                
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        title="Breakout Successful!",
                        description=f"Through process of elimination, you identified the {self.color_emojis[self.amatoxin_bottle]} bottle as Amatoxin. The Morts appeased with your performance and let you be.\n\n**Both you and {self.target.mention} escape the Mortician Wing with all the stolen stimulants.**",
                        color=discord.Color.green()
                    ),
                    view=None
                )
                self.stop()
            else:
                # Create a new view with remaining bottles
                new_view = ui.View(timeout=120)
                
                for remaining_color in self.remaining_bottles:
                    button = ui.Button(emoji=self.color_emojis[remaining_color], style=discord.ButtonStyle.secondary, custom_id=f"bottle_{remaining_color}")
                    button.callback = self.bottle_callback
                    new_view.add_item(button)
                
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        title="Pharmaceutical Test",
                        description=f"You picked the {self.color_emojis[color]} bottle.\n\n{self.drug_prompts[color]}\n\n**Pick the next bottle...**",
                        color=discord.Color.blue()
                    ),
                    view=new_view
                )

class JaegerPathBreakoutView(ui.View):
    """UI for breaking out a prisoner from the Jaeger Camp prison."""
    
    def __init__(self, cog, interaction, target, target_prison):
        super().__init__(timeout=300)
        self.cog = cog
        self.interaction = interaction
        self.target = target
        self.target_prison = target_prison
        self.path_count = 0
        
        # Safe and dangerous path messages
        self.safe_paths = [
            "You find a safe passage through the darkness.",
            "You avoid a tripwire just in time.",
            "You sidestep what appears to be a bear trap.",
            "You narrowly make it out of a triggered gas bomb.",
            "You carefully navigate around the shotshell trap in the wall."
        ]
        
        self.bad_paths = [
            "You stumble into a trip wire, a tin bomb goes off and you're knocked back.",
            "You step on a trip wire, a shotshell trap goes off and hits your arm.",
            "You walk into a bear trap, your leg is broken.",
            "You walk face-first into a lamp trap, burning your face.",
            "You trigger a gas bomb that makes it hard to breathe."
        ]
        
        # Add direction buttons
        self.add_item(ui.Button(emoji="⬅️", style=discord.ButtonStyle.primary, custom_id="left"))
        self.add_item(ui.Button(emoji="⬆️", style=discord.ButtonStyle.primary, custom_id="straight"))
        self.add_item(ui.Button(emoji="➡️", style=discord.ButtonStyle.primary, custom_id="right"))
        
        # Set up callbacks
        for item in self.children:
            item.callback = self.direction_callback
    
    async def direction_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        direction = interaction.data["custom_id"]
        
        # Get escape chance
        from ..prison_system import PRISON_TIERS
        prison_tier = next((t for t in PRISON_TIERS if t[0] == "Jaeger Camp"), None)
        path_chance = 48  # Base chance for each path
        
        from ..prison_system import get_escape_chance_modifier
        escape_chance_mod = get_escape_chance_modifier(interaction.guild.id, interaction.user.id)
        path_chance = max(8, path_chance + escape_chance_mod)
        
        # Increment path count before any checks
        self.path_count += 1
        
        # Roll for success
        roll = random.randint(1, 100)
        
        # Check if we've reached 8 paths - success regardless of last path's safety
        if self.path_count >= 8:
            # All paths traversed - success!
            guild_data = DataService.load_guild_data(interaction.guild.id)
            user_key = str(self.target.id)
            if user_key in guild_data and guild_data[user_key].get("prison"):
                guild_data[user_key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            # Determine message based on whether the last path was safe or dangerous
            if roll <= path_chance:
                # Last path was safe
                safe_message = random.choice(self.safe_paths)
                description = f"You went {direction}\n\n{safe_message}\n\n**After fighting your way out, you both run clear away from the Jaeger Camp!**"
            else:
                # Last path was dangerous but still reached 8 paths
                bad_message = random.choice(self.bad_paths)
                description = f"You went {direction}\n\n{bad_message}\n\nDespite your injuries, you finally reached {self.target.mention}!\n\n**After a brief struggle, you both escape from the Jaeger Camp!**"
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Breakout Successful!",
                    description=description,
                    color=discord.Color.green()
                ),
                view=None
            )
            self.stop()
            return
        
        # If we're still here, we haven't reached 8 paths yet
        if roll <= path_chance:
            # Safe path
            safe_message = random.choice(self.safe_paths)
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Navigating the Jaeger Camp",
                    description=f"You went {direction}\n\n{safe_message}\n\n*{self.path_count}/8 of the way there*",
                    color=discord.Color.blue()
                )
            )
        else:
            # Dangerous path
            bad_message = random.choice(self.bad_paths)
            
            # Add injury
            injury_status = get_injury_status(interaction.guild.id, interaction.user)
            add_injury(interaction.guild.id, interaction.user)
            new_injury_status = get_injury_status(interaction.guild.id, interaction.user)
            
            if new_injury_status["tier"] == "Critical Condition":
                # Ensure the view is created with a try-except block
                try:
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            title="Critical Condition!",
                            description=f"You went {direction}\n\n{bad_message}\n\nYour **Critical Condition** has made you unable to carry on...you decide to rest your eyes for a bit.\n\nYou wake up to see {self.target.mention} in a bad state across from you as well as a Jaeger with a knife to their throat.\n\nYou have been caught and the Jaegers are putting your and {self.target.mention}'s lives on the line through a sadistic game...\n\n**They present to you 4 different colored boxes:**\n\n1 box contains a **Knife**\n1 box contains a **Broken Watch**\n1 box contains stolen **Medical Supplies**\n1 box contains a **Joker Card**\n\n***Choose wisely...***",
                            color=discord.Color.orange()
                        ),
                        view=JaegerBoxesBreakoutView(self.cog, interaction, self.target)
                    )
                except Exception as e:
                    debug.log(f"Error creating JaegerBoxesBreakoutView: {e}")
                    # Try a fallback message
                    try:
                        await interaction.response.edit_message(
                            embed=discord.Embed(
                                title="Error",
                                description="Something went wrong with the game. Please try again.",
                                color=discord.Color.red()
                            ),
                            view=None
                        )
                    except:
                        pass
                self.stop()
            else:
                # Continue with new injury
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        title=f"Injured - {new_injury_status['tier']}",
                        description=f"You went {direction}\n\n{bad_message}\n\nYour condition worsened to **{new_injury_status['tier']}**.\n\n*{self.path_count}/8 of the way there*",
                        color=discord.Color.orange()
                    )
                )

class JaegerBoxesBreakoutView(ui.View):
    """UI for the Jaeger Camp final challenge with colored boxes."""
    
    def __init__(self, cog, interaction, target):
        super().__init__(timeout=120)
        self.cog = cog
        self.interaction = interaction
        self.target = target
        
        # Button colors with emojis
        self.buttons = [
            ("🟢", discord.ButtonStyle.secondary, "Green"),  # Green
            ("🔵", discord.ButtonStyle.secondary, "Blue"),   # Blue
            ("🟡", discord.ButtonStyle.secondary, "Yellow"), # Yellow
            ("🟣", discord.ButtonStyle.secondary, "Purple")  # Purple
        ]
        
        # Randomly assign outcomes to colors
        outcomes = ["knife", "broken_watch", "medical_supplies", "joker_card"]
        random.shuffle(outcomes)
        self.color_outcomes = dict(zip(["Green", "Blue", "Yellow", "Purple"], outcomes))
        
        # Add colored buttons
        for emoji, style, color in self.buttons:
            button = ui.Button(emoji=emoji, style=style, custom_id=color.lower())
            button.callback = self.box_callback
            self.add_item(button)
    
    async def box_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your breakout attempt!", ephemeral=True)
            return
        
        color = interaction.data["custom_id"]
        color_name = next((b[2] for b in self.buttons if b[2].lower() == color), "Unknown")
        outcome = self.color_outcomes[color_name]
        
        guild_data = DataService.load_guild_data(interaction.guild.id)
        user_key = str(interaction.user.id)
        target_key = str(self.target.id)
        
        if user_key not in guild_data:
            user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
            guild_data[user_key] = user_data
        
        # Import at function level
        from ..prison_system import PRISON_COOLDOWN
        
        if outcome == "knife":
            # 55% chance of target death, 45% chance of escape for both
            if random.random() < 0.55:
                # Target dies
                user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
                
                if target_key in guild_data:
                    target_pockets = self.cog.get_pockets(interaction.guild.id, self.target)
                    self.cog.update_pockets(interaction.guild.id, self.target, -target_pockets)
                    
                    # Take 25% of target's savings
                    target_savings = self.cog.get_savings(interaction.guild.id, self.target)
                    target_savings_penalty = int(target_savings * 0.25)
                    
                    # If target has no savings (zero or negative), apply a -75 medal debt
                    if target_savings <= 0:
                        self.cog.update_savings(interaction.guild.id, self.target, -75)
                        target_savings_penalty = 75
                    else:
                        self.cog.update_savings(interaction.guild.id, self.target, -target_savings_penalty)

                    # Reload guild data after updating balances
                    updated_guild_data = DataService.load_guild_data(interaction.guild.id)
                    
                    # Send user to Jaeger Camp (again)
                    updated_guild_data[user_key]["prison"] = {
                        "tier": "Jaeger Camp", 
                        "release_time": int(time.time()) + PRISON_COOLDOWN
                    }
                    
                    # Free target from prison but with penalties
                    if target_key in updated_guild_data:
                        updated_guild_data[target_key]["prison"] = None
                        updated_guild_data[target_key]["injuries"] = 0
                        updated_guild_data[target_key]["injured"] = False

                    DataService.save_guild_data(interaction.guild.id, updated_guild_data)
                
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        title="Regretful Solitude",
                        description=f"Inside the {color} box was a **Knife**...\n\nNot a second later a Jaeger plunges the **Knife** into your hand, keeping you to the table.\n\nThe Jaeger holding the knife to {self.target.mention}'s throat had pushed them to the ground pulling out a **Knell** and aims it right into {self.target.mention}'s head.\n\nPainfully trying to free yourself from the Knife, you plead with the Jaegers desperately.\n\nAfter a while of begging, you are forced to watch as **{self.target.mention} crashes to the ground as a bullet goes through their head**.\n\nAs all their pocket Medals and **{target_savings_penalty}** Medals from savings get's looted off of their corpse, you are left all alone to face the unbearable consequences of your decisions.\n\nYou now face the same fate as your friend, as your 1 hour of hell has only just begun...",
                        color=discord.Color.dark_red()
                    ),
                    view=None
                )
            else:
                # Lucky escape
                # Free both the user and target
                for key in [user_key, target_key]:
                    if key in guild_data and guild_data[key].get("prison"):
                        guild_data[key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
                
                # Choose a lucky escape story based on color
                if color == "green":
                    lucky_escape_title = "War Investment"
                    escape_msg = f"Consider yourself lucky.\n\nThis sadistic game was interrupted by knocking on the door behind you.\nA guard opens the door to a benefactor of the ***Solace Coalition***, who trades for both of your freedoms with a crate of Medals. All three of you exit the camp in silence.\n\nBefore you could ask questions about the individual, they knock both of you out with the butt of a rifle.\nYou wake up hours later with some rations, and a Jesse rifle, enough to make the trip back home together.\n\n**War is an economy. Anybody who tells you otherwise is either in on it or stupid.**"
                    embed_color = discord.Color.brand_green()
                elif color == "blue":
                    lucky_escape_title = "Organized Chaos"
                    escape_msg = f"You pick up the blue box, upon shaking it you realize you made the wrong choice.\nInside was the **Knife** and you could only feel the weight of despair as you slowly began to open it.\n\nSuddenly, the room shook. Screaming and the sound of footsteps was heard in the dark halls of the camp. Many of the guards in the room with you hurriedly ran out to address the sudden event.\n\nYou took the opportunity to take the **Knife** in the box and kill one of the guards.\nA brief tussle ensued with you coming out on top, inserting the knife into the throat of the Jaeger.\n\nQuickly taking their keys, and Union, {self.target.mention} shoots the other guards and you both take the opportunity to take their stuff too.\n\nAfter an hours worth of looting and killing, you both make it to the main hall looking like an exhausted serial killer.\nYou see multiple bodies on the ground as well as the smiles of the ***Bandits*** that caused this massacre.\n\nSeeing both of you and the amount of stolen goods you were carrying, they thought both of you were one of them, letting you all leave the camp with grins on your faces.\n\n**In the midst of chaos, there is also opportunity.**"
                    embed_color = discord.Color.dark_blue()
                elif color == "yellow":
                    lucky_escape_title = "Sacrilegious Duty"
                    escape_msg = f"Before getting the chance to open the box, the door behind you slams open.\nAn Inquisitor of the ***Golden Empire*** walks to face you and the guards.\n\nShe announces for you and {self.target.mention}'s immediate release by the order of the Queen. Due to previous deeds effectively carried out by your hands for the Empire, the Queen had deemed you a worthy servant to the glory of the crown..\n\nConfused and annoyed, a guard begins to argue with her over the new profound change of ruling.\nCursing the Inquisitor, calling the notion as one made up by a fool, the guard continues to argue. Only to be interrupted by two Armsmen, who quickly subdues and carries the guard out the room.\n\nThe Inquisitor apologizes for the many tortuous days of imprisonment the Empire had subjected {self.target.mention} and humbly bows as they leave the room.\n\nAs you both begin to walk out of the camp you notice the guard, who had bickered with the Inquisitor moments before, hanging from a wooden pole with a sign around his neck saying:\n\n**It is better to remain silent and be thought a fool than to open your mouth and remove all doubt of heresy.**"
                    embed_color = discord.Color.gold()
                elif color == "purple":
                    lucky_escape_title = "Corrupted Saints"
                    escape_msg = f"You open the box to find the **Knife** inside. The Jaegers howl and laugh at your misfortune.\n\nThey drag you to the center of a room and turn on the lights.\nAcross from you, you see a Jaeger with a mysterious looking weapon, almost as if it was a prototype made for the war.\nYou close your eyes as you prepare to depart from this hell...\n\nSuddenly, several people in dark uniforms bursts into the room, pushing one of the guards next to the door to the ground.\nAt the head of this group was a Sergeant Major of the **Royal Nation**.\n\nHe announces his bold presence with arrest orders for every and all workers of the camp for the theft and gatekeeping of this experimental weapon.\n\nThe camp's Brigadier General, who easily outranked the Sergeant Major, protested and claimed the allegations was an act of foul-play to end his career.\nA brief back and forth found the Brigadier General carried away as Privates escorted the rest of the guards away from the room.\n\nThe Sergeant Major looking down at you with a cold stare raises his Grace towards you. However, a sudden change of heart must've granted your freedom, as he lowers his Grace and exits the room with a smile knowing the promotion awaiting for his efforts.\n\n**The wicked cannot create anything new, they can only corrupt and ruin what good forces have invented or made.**"
                    embed_color = discord.Color.dark_purple()
                
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        title=lucky_escape_title,
                        description=f"{escape_msg}\n\nYou successfully free {self.target.mention}!",
                        color=embed_color
                    ),
                    view=None
                )
            
        elif outcome == "broken_watch":
            # Extend prison time for both by 15 minutes
            guild_data[user_key]["prison"] = {
                "tier": "Jaeger Camp", 
                "release_time": int(time.time()) + PRISON_COOLDOWN
            }
            
            for key in [user_key, target_key]:
                if key in guild_data and guild_data[key].get("prison"):
                    prison_time = guild_data[key]["prison"].get("release_time", int(time.time()) + PRISON_COOLDOWN)
                    prison_time += (15 * 60)  # Add 15 minutes
                    guild_data[key]["prison"]["release_time"] = prison_time
            
            DataService.save_guild_data(interaction.guild.id, guild_data)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Shared Silence",
                    description=f"Inside the {color} box was a broken watch...\n\nThe Jaegers sigh in disappointment and put both you and {self.target.mention} back in your cells.\n\nBoth your sentences have been increased by an extra **15 minutes** each.",
                    color=discord.Color.red()
                ),
                view=None
            )
            
        elif outcome == "medical_supplies":
            # Heal both users but keep them in prison
            guild_data[user_key]["prison"] = {
                "tier": "Jaeger Camp", 
                "release_time": int(time.time()) + PRISON_COOLDOWN
            }
            
            for key in [user_key, target_key]:
                if key in guild_data:
                    if guild_data[key].get("injuries", 0) > 0:
                        # Reduce by 1 injury level
                        guild_data[key]["injuries"] = max(0, guild_data[key].get("injuries", 0) - 1)
                        guild_data[key]["injured"] = guild_data[key]["injuries"] > 0
            
            DataService.save_guild_data(interaction.guild.id, guild_data)
            
            # Get new status
            user_status = get_injury_status(interaction.guild.id, interaction.user)
            target_status = get_injury_status(interaction.guild.id, self.target)
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Reluctant Gifts",
                    description=f"Inside the {color} box were medical supplies!\n\nThe Jaegers reluctantly allow you both to treat your wounds.\n\nYour condition improved to **{user_status['tier']}** and {self.target.mention}'s condition improved to **{target_status['tier']}**.\n\nHowever, both of you remain in prison for now...",
                    color=discord.Color.green()
                ),
                view=None
            )
            
        elif outcome == "joker_card":
            # Add injury to target
            if target_key in guild_data:
                add_injury(interaction.guild.id, self.target)
                
                # Reload guild data after adding injury
                updated_guild_data = DataService.load_guild_data(interaction.guild.id)
                updated_guild_data[user_key]["prison"] = {
                    "tier": "Jaeger Camp", 
                    "release_time": int(time.time()) + PRISON_COOLDOWN
                }
                
                DataService.save_guild_data(interaction.guild.id, updated_guild_data)
                new_target_status = get_injury_status(interaction.guild.id, self.target)
                
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        title="Indirect Punishment",
                        description=f"Inside the {color} box was a Joker Card.\n\nAs soon as you picked it up, the Jaegers started to laugh as they **cut a finger off of {self.target.mention}'s hand.**\n\nTheir condition has worsened to **{new_target_status['tier']}**.\n\nBoth of you remain in prison for now...",
                        color=discord.Color.red()
                    ),
                    view=None
                )
            
        self.stop()

    async def on_timeout(self):
        """Handle timeout of the component."""
        try:
            # Get current guild and user data
            guild_id = self.interaction.guild.id
            user_id = self.interaction.user.id
            user = self.interaction.user
            
            # Thread-safe data operations
            with DataService.get_guild_lock(guild_id):
                # Clear pocket money
                user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
                
                pockets_before = self.cog.get_pockets(guild_id, user)
                self.cog.update_pockets(guild_id, user, -pockets_before)
                            
                # Take 25% of savings
                savings = self.cog.get_savings(guild_id, user)
                savings_penalty = int(savings * 0.25)
                
                # Apply penalty
                if savings <= 0 or savings_penalty <= 0:
                    self.cog.update_savings(guild_id, user, -75)
                    savings_penalty = 75
                else:
                    self.cog.update_savings(guild_id, user, -savings_penalty)
                
                # Reload guild data after updates
                guild_data = DataService.load_guild_data(guild_id)
                user_key = str(user_id)
                
                # Free from prison and clear injuries
                if user_key in guild_data:
                    guild_data[user_key]["prison"] = None
                    guild_data[user_key]["injuries"] = 0
                    guild_data[user_key]["injured"] = False
                    DataService.save_guild_data(guild_id, guild_data)
            
            embed = discord.Embed(
                title="Impatient Wolves",
                description=f"The Jaeger's grew impatient of your silly games.\n\n**They have lobbed your head off.**\n\nTaking your **All** Medals from your pockets and **{savings_penalty}** Medals from savings...",
                color=discord.Color.dark_red()
            )
            
            # Safely edit message with try-except
            try:
                await self.interaction.edit_original_response(
                    content=f"<@{user_id}>",
                    embed=embed,
                    view=None
                )
            except Exception as e:
                debug.log(f"Error editing message in timeout handler: {e}")
                # Try followup message as fallback
                try:
                    await self.interaction.followup.send(
                        content=f"<@{user_id}>",
                        embed=embed
                    )
                except:
                    pass
                        
        except Exception as e:
            debug.log(f"Error in timeout handler: {e}")
            
        finally:
            # Clean up references
            self.cog = None
            self.interaction = None
            self.target = None