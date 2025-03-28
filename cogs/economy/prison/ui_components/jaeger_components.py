"""
UI components for Jaeger Camp prison interactions.
"""
import discord
import random
import time
from discord import app_commands, ui
from athena.data_service import DataService
from athena.debug_tools import DebugTools
from ...status.injury_system import add_injury, get_injury_status
from ...economy_base import EconomyCog

# Debug logger
debug = DebugTools.get_debugger("jaeger_components")

class EscapeJaegerView(ui.View):
    """UI for the Jaeger Camp escape challenge."""
    
    def __init__(self, cog, interaction, user_id):
        super().__init__(timeout=1800)  # 30 minute timeout
        self.cog = cog
        self.original_interaction = interaction
        self.user_id = user_id
        
        # Button colors with emojis and outcomes
        self.buttons = [
            ("🟢", discord.ButtonStyle.secondary, "Green"),  # Green
            ("🔵", discord.ButtonStyle.secondary, "Blue"),   # Blue
            ("🟡", discord.ButtonStyle.secondary, "Yellow"), # Yellow
            ("🟣", discord.ButtonStyle.secondary, "Purple")  # Purple
        ]
        
        # Randomly assign outcomes to buttons
        outcomes = ["death", "injury", "heal", "broken_watch"]
        random.shuffle(outcomes)
        self.button_outcomes = {i: outcome for i, outcome in enumerate(outcomes)}
        
        # Add buttons
        for i, (emoji, style, _) in enumerate(self.buttons):
            button = ui.Button(style=style, emoji=emoji, custom_id=f"jaeger_button_{i}")
            button.callback = self.button_callback
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        # Check if the interaction user is the one who needs to escape
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("All you can do is watch as the Jaegers laugh hysterically over the torture of your friend...\n\nthere is no saving them :<", ephemeral=True)
            return
        
        # Get button index and color from custom_id
        button_idx = int(interaction.data["custom_id"].split("_")[-1])
        button_color = self.buttons[button_idx][2]
        outcome = self.button_outcomes[button_idx]
        
        guild_data = DataService.load_guild_data(interaction.guild.id)
        user_key = str(interaction.user.id)
        
        # Get or create user data
        user_data = DataService.get_user_data(interaction.guild.id, interaction.user.id, interaction.user.display_name)
        
        # Process different outcomes
        if outcome == "death":
            # Check for special escape chance (45% chance)
            if random.random() < 0.45:  # 45% chance of escape
                # Success!
                guild_data[user_key]["prison"] = None
                DataService.save_guild_data(interaction.guild.id, guild_data)
                
                # Custom responses based on button color
                if button_color == "Green":
                    lucky_escape_title = "War Investment"
                    escape_msg = "Consider yourself lucky.\n\nThis sadistic game was interrupted by knocking on the door behind you.\nA guard opens the door to a benefactor of the ***Solace Coalition***, who trades for your release with a crate of Medals. Both of you exit the camp in silence.\n\nBefore you could ask questions about the individual, they knock you out with the butt of a rifle.\nYou wake up hours later with some rations, and a Jesse rifle, enough to make the trip back home.\n\n**War is an economy. Anybody who tells you otherwise is either in on it or stupid.**"
                    embed_color = discord.Color.brand_green()
                elif button_color == "Blue":
                    lucky_escape_title = "Organized Chaos"
                    escape_msg = "You pick up the blue box, upon shaking it you realize you made the wrong choice.\nInside was the **Knife** and you could only feel the weight of despair as you slowly began to open it.\n\nSuddenly, the room shook. Screaming and the sound of footsteps was heard in the dark halls of the camp. Many of the guards in the room with you hurriedly ran out to address the sudden event.\n\nYou took the opportunity to take the knife in the box and kill one of the guards.\nA brief tussle ensued with you coming out on top, inserting the knife into the throat of one of the guards.\n\nQuickly taking their keys, and Union, you shoot the other guards and take the opportunity to take their stuff too.\nAfter an hours worth of looting and killing, you make it to the main hall looking like an exhausted serial killer.\n\nYou see multiple bodies on the ground as well as the smiles of the ***Bandits*** that caused this massacre.\nSeeing you and the amount of stolen goods you were carrying, they had thought you were one of them. Letting you leave the camp with a grin on your face.\n\n**In the midst of chaos, there is also opportunity.**"
                    embed_color = discord.Color.dark_blue()
                elif button_color == "Yellow":
                    lucky_escape_title = "Sacrilegious Duty"
                    escape_msg = "Before getting the chance to open the box, the door behind you slams open.\nAn Inquisitor of the ***Golden Empire*** walks to face you and the guards.\n\nShe announces for your immediate release by the order of the Queen. Due to previous deeds effectively carried out by your hands for the Empire, the Queen had deemed you a worthy servant to the glory of the crown..\n\nConfused and annoyed, a guard begins to argue with her over the new profound change of ruling.\nCursing the Inquisitor, calling the notion as one made up by a fool, the guard continues to argue. Only to be interrupted by two Armsmen, who quickly subdue and carry the guard out the room.\n\nThe Inquisitor apologizes for the many tortuous days of imprisonment the Empire had subjected you and humbly bows as they leave the room.\n\nAs you begin to walk out of the camp you notice the guard, who had bickered with the Inquisitor moments before, hanging from a wooden pole with a sign around his neck saying:\n\n**It is better to remain silent and be thought a fool than to open your mouth and remove all doubt of heresy.**"
                    embed_color = discord.Color.gold()
                elif button_color == "Purple":
                    lucky_escape_title = "Corrupted Saints"
                    escape_msg = "You open the box to find the **Knife** inside. The Jaegers howl and laugh at your misfortune.\n\nThey drag you to the center of a room and turn on the lights.\nAcross from you, you see a Jaeger with a mysterious looking weapon, almost as if it was a prototype made for the war.\nYou close your eyes as you prepare to depart from this hell...\n\nSuddenly, several people in dark uniforms bursts into the room, pushing one of the guards next to the door to the ground.\nAt the head of this group was a Sergeant Major of the **Royal Nation**.\n\nHe announces his bold presence with arrest orders for every and all workers of the camp for the theft and gatekeeping of this experimental weapon.\n\nThe camp's Brigadier General, who easily outranked the Sergeant Major, protested and claimed the allegations was an act of foul-play to end his career.\nA brief back and forth found the Brigadier General carried away as Privates escorted the rest of the guards away from the room.\n\nThe Sergeant Major looking down at you with a cold stare raises his Grace towards you. However, a sudden change of heart must've granted your freedom, as he lowers his Grace and exits the room with a smile knowing the promotion awaiting for his efforts.\n\n**The wicked cannot create anything new, they can only corrupt and ruin what good forces have invented or made.**"
                    embed_color = discord.Color.dark_purple()
                
                embed = discord.Embed(
                    title=lucky_escape_title,
                    description=f"{escape_msg}",
                    color=embed_color
                )
                await interaction.response.edit_message(content=f"{interaction.user.mention}", embed=embed, view=None)
            else:
                # Normal death outcome - 55% chance
                # Get pocket and savings values
                pockets_before = self.cog.get_pockets(interaction.guild.id, interaction.user)
                # Clear pockets
                self.cog.update_pockets(interaction.guild.id, interaction.user, -pockets_before)
                
                # Take 25% of savings
                savings = self.cog.get_savings(interaction.guild.id, interaction.user)
                savings_penalty = int(savings * 0.25)
                
                # If user has no savings (zero or negative), apply a -75 medal debt
                if savings <= 0 or savings_penalty <= 0:
                    self.cog.update_savings(interaction.guild.id, interaction.user, -75)
                    savings_penalty = 75
                else:
                    self.cog.update_savings(interaction.guild.id, interaction.user, -savings_penalty)

                guild_data = DataService.load_guild_data(interaction.guild.id)
                user_key = str(interaction.user.id)
                
                # Clear prison and injuries
                guild_data[user_key]["prison"] = None
                guild_data[user_key]["injuries"] = 0
                guild_data[user_key]["injured"] = False
                DataService.save_guild_data(interaction.guild.id, guild_data)
                
                # Get death message
                try:
                    death_msg = self.cog.get_response("escape_death_jaeger_camp", amount=pockets_before, savings_penalty=savings_penalty)
                except Exception as e:
                    # Fallback death message
                    death_msg = f"You chose the box with the **Knife**. The Jaegers forced you to fight to the death in an arena.\n\nYou didn't survive...\n\nYou lost **{pockets_before}** Medals from your pockets and **{savings_penalty}** Medals from your savings."
                
                embed = discord.Embed(
                    title="The Knife",
                    description=f"{death_msg}",
                    color=discord.Color.dark_red()
                )
                await interaction.response.edit_message(content=f"{interaction.user.mention}", embed=embed, view=None)
            
        elif outcome == "injury":
            # Injury and extended prison time
            # Check if already at critical condition
            injury_status = get_injury_status(interaction.guild.id, interaction.user)
            if injury_status["tier"] != "Critical Condition":
                add_injury(interaction.guild.id, interaction.user)
            new_status = get_injury_status(interaction.guild.id, interaction.user)
            
            # Extend prison time
            if "prison" in guild_data[user_key] and guild_data[user_key]["prison"]:
                prison_time = guild_data[user_key]["prison"].get("release_time", int(time.time()) + 3600)
                prison_time += (30 * 60)  # Add 30 minutes
                guild_data[user_key]["prison"]["release_time"] = prison_time
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            # Get injury message
            try:
                injury_msg = self.cog.get_response("escape_injury_jaeger_camp")
            except Exception as e:
                # Fallback injury message
                injury_msg = "You chose the box with the **Card**. The Jaegers took this as their cue to play a game with your body.\n\nThey break your bones, one by one, as they lay out a deck of cards. Each card drawn determines which bone gets broken next."
            
            embed = discord.Embed(
                title=f"Bad Hand - {new_status['tier']}!",
                description=f"{injury_msg}\n\nYour condition is now **{new_status['tier']}** and your prison time was extended by **30 minutes**.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(content=f"{interaction.user.mention}", embed=embed, view=None)
            
        elif outcome == "heal":
            # Heal one injury tier and take -20 medals from savings
            self.cog.update_savings(interaction.guild.id, interaction.user, -20)
            
            # Reduce injury tier by 1 level
            injury_status = get_injury_status(interaction.guild.id, interaction.user)
            if injury_status["injuries"] > 0:
                guild_data[user_key]["injuries"] = max(0, guild_data[user_key]["injuries"] - 1)
                guild_data[user_key]["injured"] = guild_data[user_key]["injuries"] > 0
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            new_status = get_injury_status(interaction.guild.id, interaction.user)
            
            # Custom heal response
            heal_msg = "The Jaegers scowl in disappointment as the box you have opened contained **medical supplies**.\n\nThey let you return to your cell to treat your wounds, but not without taking a fee of **20** Medals.."
            
            embed = discord.Embed(
                title="Displeased Mercy",
                description=f"{heal_msg}\n\nYour condition improved to **{new_status['tier']}**.",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(content=f"{interaction.user.mention}", embed=embed, view=None)
            
        elif outcome == "broken_watch":
            # Always extend prison time by 15 minutes (100% chance)
            if "prison" in guild_data[user_key] and guild_data[user_key]["prison"]:
                prison_time = guild_data[user_key]["prison"].get("release_time", int(time.time()) + 3600)
                prison_time += (15 * 60)  # Add 15 minutes
                guild_data[user_key]["prison"]["release_time"] = prison_time
                DataService.save_guild_data(interaction.guild.id, guild_data)
            
            embed = discord.Embed(
                title="Prolonged Silence",
                description=f"Inside the box was a **broken watch**...\n\nThe Jaegers sighs in disappointment and puts you back in your cell.\n\nYour sentence has increased an extra **15 minutes**.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(content=f"{interaction.user.mention}", embed=embed, view=None)
        
        # Disable the view after use
        self.stop()

    async def on_timeout(self):
        try:
            # Get current guild and user data
            guild_id = self.interaction.guild.id
            user_id = self.interaction.user.id
            user = self.interaction.user
            
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