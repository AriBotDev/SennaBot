"""
Balance challenge implementation.
Enforces wealth cap by challenging users who exceed a threshold.
"""
import discord
import random
import asyncio
import time
import threading
from typing import Dict, Optional, List, Tuple, Union

from discord.ext import commands
from discord import app_commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from athena.debug_tools import DebugTools
from ..economy_base import EconomyCog

# Constants
SENNABOT_BALANCE = 15000  # Threshold to trigger balance challenge
CHALLENGE_BET = 1000      # Bet amount for the challenge
SENNABOT_ID = 1349242668672090253  # SennaBot's user ID
CHALLENGE_TIMEOUT = 120   # Timeout for challenge interactions

# Blackjack game constants
SUITS = ['♠️', '♥️', '♦️', '♣️']
CARD_VALUES = {
    'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10
}
CARD_FACES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
_active_challenges = {}
_challenges_lock = threading.Lock()

# Global instance of the balance challenge manager
class BalanceChallengeManager:
    """Manager for the balance challenge system"""

    def __init__(self):
        self.active_challenges = {}  # Dictionary to track active challenges
        self.challenges_in_progress = set()  # Set to track challenges being processed
        self.debug = DebugTools.get_debugger("balance_challenge_manager")
    
    def is_in_challenge(self, user_id: int) -> bool:
        """Check if a user is currently in an active challenge"""
        return user_id in self.active_challenges
    
    def add_to_challenge(self, user_id: int, guild_id: int) -> None:
        """Mark a user as being in a challenge"""
        self.active_challenges[user_id] = guild_id
        self.debug.log(f"Added user {user_id} to active challenges in guild {guild_id}")
    
    def remove_from_challenge(self, user_id: int) -> None:
        """Remove user from active challenges"""
        if user_id in self.active_challenges:
            self.debug.log(f"Removed user {user_id} from active challenges")
            del self.active_challenges[user_id]
    
    def should_trigger_challenge(self, guild_id: int, user: discord.Member) -> bool:
        """Check if user should face the balance challenge"""
        # Get user's data
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        
        # Skip if user already beaten the challenge
        if user_data.get("beat_balance_challenge", False):
            return False
        
        # Skip if user is already in an active challenge
        if self.is_in_challenge(user.id):
            return False
        
        # Get user's total balance
        pockets = user_data.get("pockets", 0)
        savings = user_data.get("savings", 0)
        user_total = pockets + savings
        
        # Trigger if balance exceeds threshold
        return user_total > SENNABOT_BALANCE
    
    def mark_challenge_beaten(self, guild_id: int, user: discord.Member) -> None:
        """Mark that user has beaten the challenge"""
        user_data = DataService.get_user_data(guild_id, user.id, user.display_name)
        user_data["beat_balance_challenge"] = True
        
        guild_data = DataService.load_guild_data(guild_id)
        guild_data[str(user.id)] = user_data
        DataService.save_guild_data(guild_id, guild_data)
        self.debug.log(f"User {user.id} has beaten the balance challenge")
    
    async def trigger_balance_challenge(self, bot, interaction: discord.Interaction) -> bool:
        """Check and trigger the balance challenge if conditions are met"""
        if not interaction.guild:
            return False
            
        guild_id = interaction.guild.id
        user = interaction.user
        
        if self.should_trigger_challenge(guild_id, user):
            # Start the challenge
            await self.start_challenge(bot, interaction)
            return True
            
        return False
    
    async def trigger_challenge_for_donation_target(self, bot, guild: discord.Guild, target: discord.Member) -> bool:
        """Check if a donation target now meets the challenge threshold"""
        if not target or not guild:
            self.debug.log("Cannot trigger challenge: target or guild is None")
            return False
            
        if target.bot:
            self.debug.log(f"Cannot trigger challenge: {target.display_name} is a bot")
            return False
            
        guild_id = guild.id
        
        # Get user's total balance for better debugging
        user_data = DataService.get_user_data(guild_id, target.id, target.display_name)
        pockets = user_data.get("pockets", 0)
        savings = user_data.get("savings", 0)
        user_total = pockets + savings
        
        self.debug.log(f"Donation target {target.display_name} balance: {user_total} medals (threshold: {SENNABOT_BALANCE})")
        
        # Check if target should face the challenge
        if self.should_trigger_challenge(guild_id, target):
            self.debug.log(f"Target {target.display_name} meets challenge criteria, starting challenge...")
            
            # Find a usable channel
            channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages]
            if not channels:
                self.debug.log(f"No suitable channel found in guild {guild.name}")
                return False
            
            channel = channels[0]
            
            # Make sure the target isn't already in a challenge
            if self.is_in_challenge(target.id):
                self.debug.log(f"Target {target.display_name} is already in a challenge")
                return False
                
            # Add user to challenge list BEFORE starting challenge to prevent command use
            self.add_to_challenge(target.id, guild_id)
            
            try:
                # Send initial challenge message
                challenge_msg = (
                    f"This is not the first time we have crossed paths {target.mention}!\n\n"
                    f"You have become richer than me once more.\n\n"
                    f"**...My programming was designed to kill any individual who surpasses my wealth.**"
                    f"\n\n**IF you beat me in a game of Blackjack**, consider yourself the richest individual in these caves..."
                    f"\n\n**ELSE IF you lose to me**, not only will you lose **{CHALLENGE_BET}** Medals but you will also be sent to the **Jaeger Camps** where you may rot in hell."
                    f"\n\nIn addition, **ALL WHO HAVE STOOD BESIDE YOU, WILL STAND NO LONGER**"
                    f"\n\n\nLet us begin..."
                )
                
                embed = discord.Embed(
                    title="🔪 DEFEAT SENNABOT 🔪",
                    description=challenge_msg,
                    color=discord.Color.gold()
                )
                
                await channel.send(content=target.mention, embed=embed)
                
                # Wait a moment for dramatic effect
                await asyncio.sleep(3)
                
                # Start the challenge directly
                challenge = ChallengeGame(bot, None, guild_id, target, channel)
                await challenge.start_challenge()
                
                return True
            except Exception as e:
                self.debug.log(f"Error starting challenge for donation target: {e}")
                # Remove from challenge if it failed to start
                self.remove_from_challenge(target.id)
                return False
                
        return False
    
    async def start_challenge(self, bot, interaction: discord.Interaction) -> None:
        """Start the balance challenge"""
        user = interaction.user
        channel = interaction.channel
        
        # Mark user as in challenge
        self.add_to_challenge(user.id, interaction.guild.id)
        
        # Send initial challenge message
        challenge_msg = (
            f"This is not the first time we have crossed paths {user.mention}!\n\n"
            f"You have become richer than me once more.\n\n"
            f"**...My programming was designed to kill any individual who surpasses my wealth.**"
            f"\n\n**IF you beat me in a game of Blackjack**, consider yourself the richest individual in these caves..."
            f"\n\n**ELSE IF you lose to me**, not only will you lose **{CHALLENGE_BET}** Medals but you will also be sent to the **Jaeger Camps** where you may rot in hell."
            f"\n\nIn addition, **ALL WHO HAVE STOOD BESIDE YOU, WILL STAND NO LONGER**"
            f"\n\n\nLet us begin..."
        )
        
        embed = discord.Embed(
            title="🔪 DEFEAT SENNABOT 🔪",
            description=challenge_msg,
            color=discord.Color.gold()
        )
        
        await channel.send(content=user.mention, embed=embed)
        
        # Wait a moment for dramatic effect
        await asyncio.sleep(3)
        
        # Start the multi-game challenge
        challenge = ChallengeGame(bot, interaction)
        await challenge.start_challenge()


class ChallengeGame:
    """Manages the best-of-5 blackjack challenge"""
    
    def __init__(self, bot, interaction, guild_id=None, user=None, channel=None):
        self.bot = bot
        self.interaction = interaction
        self.debug = DebugTools.get_debugger("challenge_game")
        
        # Handle either an interaction or direct parameters
        if interaction:
            self.guild_id = interaction.guild.id
            self.user = interaction.user
            self.channel = interaction.channel
        else:
            self.guild_id = guild_id
            self.user = user
            self.channel = channel
        
        # Track wins
        self.user_wins = 0
        self.bot_wins = 0
        self.games_played = 0
        
        # We need 3 wins to win the challenge
        self.wins_needed = 3
    
    async def start_challenge(self):
        """Start the best-of-5 challenge"""
        self.debug.log(f"Starting challenge for {self.user.display_name}")
        # Start the first game
        await self.play_next_game()
    
    async def play_next_game(self):
        """Play the next game in the series"""
        self.games_played += 1
        self.debug.log(f"Starting game {self.games_played} of challenge")
        
        # Create a new deck and shuffle
        deck = [(face, suit) for suit in SUITS for face in CARD_FACES]
        random.shuffle(deck)
        
        # Deal initial cards
        user_hand = [deck.pop(), deck.pop()]
        bot_hand = [deck.pop(), deck.pop()]
        
        # Show initial state
        user_value = calculate_hand_value(user_hand)
        bot_visible_value = CARD_VALUES[bot_hand[0][0]]
        
        user_cards = " ".join([f"{face}{suit}" for face, suit in user_hand])
        bot_visible_card = f"{bot_hand[0][0]}{bot_hand[0][1]}"
        
        embed = discord.Embed(
            title=f"DEFEAT SENNABOT - Round {self.games_played}",
            description=f"The stakes: **{CHALLENGE_BET}** Medals",
            color=discord.Color.gold()
        )
        
        # Add scoreboard to the game message
        embed.add_field(
            name="Current Score",
            value=f"{self.user.mention}: {self.user_wins} wins\nSennaBot: {self.bot_wins} wins\n\nFirst to {self.wins_needed} wins!",
            inline=False
        )
        
        embed.add_field(
            name=f"Your Hand ({user_value})",
            value=user_cards,
            inline=False
        )
        
        embed.add_field(
            name=f"SennaBot's Hand (Showing {bot_visible_value})",
            value=f"{bot_visible_card} 🂠",
            inline=False
        )
        
        # Create buttons for Hit and Stand with longer timeout
        view = BlackjackChallengeView(self, user_hand, bot_hand, deck)
        
        # Send game message - always with a ping
        await self.channel.send(content=self.user.mention, embed=embed, view=view)
    
    async def show_game_result(self, message, user_hand, bot_hand, user_win, is_tie):
        """Update the current game message with the results"""
        user_value = calculate_hand_value(user_hand)
        bot_value = calculate_hand_value(bot_hand)
        
        user_cards = " ".join([f"{face}{suit}" for face, suit in user_hand])
        bot_cards = " ".join([f"{face}{suit}" for face, suit in bot_hand])
        
        # Determine result message
        if is_tie:
            result = "**It's a tie!** This round will be replayed."
        elif user_win:
            result = f"**{self.user.mention} wins this round! :D**"
            if bot_value > 21:
                result = f"SennaBot busted! {result}"
            elif user_value > bot_value:
                result = f"{self.user.mention}'s hand is higher! {result}"
        else:
            result = "**SennaBot wins this round! D:**"
            if user_value > 21:
                result = f"{self.user.mention} busted! {result}"
            elif bot_value > user_value:
                result = f"SennaBot's hand is higher! {result}"
        
        # Update scores if not a tie
        if not is_tie:
            if user_win:
                self.user_wins += 1
            else:
                self.bot_wins += 1
        
        # Create updated embed
        embed = discord.Embed(
            title=f"Round {self.games_played} - Results",
            description=f"The stakes: **{CHALLENGE_BET}** Medals",
            color=discord.Color.gold()
        )
        
        # Add updated scoreboard
        embed.add_field(
            name="Current Score",
            value=f"{self.user.display_name}: **{self.user_wins}** wins\nSennaBot: **{self.bot_wins}** wins\n\nFirst to ***{self.wins_needed} wins!***",
            inline=False
        )
        
        embed.add_field(
            name=f"Your Hand ({user_value})",
            value=user_cards,
            inline=False
        )
        
        embed.add_field(
            name=f"SennaBot's Hand ({bot_value})",
            value=bot_cards,
            inline=False
        )
        
        embed.add_field(
            name="Result",
            value=result,
            inline=False
        )
        
        # Update the message with the results
        try:
            await message.edit(embed=embed, view=None)
        except Exception as e:
            self.debug.log(f"Error editing game result message: {e}")
            # If message can't be edited, send a new one
            await self.channel.send(content=self.user.mention, embed=embed)
        
        # Short delay
        await asyncio.sleep(1)
        
        # Check if the challenge is over or continue
        if self.user_wins >= self.wins_needed:
            await self.end_challenge(True)
        elif self.bot_wins >= self.wins_needed:
            await self.end_challenge(False)
        else:
            # If it's a tie, don't count this game
            if is_tie:
                self.games_played -= 1
            # Start next game
            await self.play_next_game()
    
    async def end_challenge(self, user_win):
        """Handle the end of the entire challenge"""
        # Remove user from active challenges
        balance_challenge_manager.remove_from_challenge(self.user.id)
        
        # Get user data
        user_data = DataService.get_user_data(self.guild_id, self.user.id, self.user.display_name)
        
        if user_win:
            # User wins - add 1000 medals to savings, mark challenge as beaten
            user_data["savings"] = user_data.get("savings", 0) + CHALLENGE_BET
            
            # Save the updated user data
            guild_data = DataService.load_guild_data(self.guild_id)
            guild_data[str(self.user.id)] = user_data
            DataService.save_guild_data(self.guild_id, guild_data)
            
            # Mark as beaten
            balance_challenge_manager.mark_challenge_beaten(self.guild_id, self.user)
            
            win_msg = (
                f"I concede {self.user.mention}...\n\n"
                f"**But I shall return. Next time with higher stakes on the line**"
                f"\n\n{self.user.mention} has beat SennaBot and was rewarded **{CHALLENGE_BET}** Medals for their victory and the ensured safety of everyone within the caves."
            )
            
            embed = discord.Embed(
                title="SennaBot Defeated",
                description=win_msg,
                color=discord.Color.green()
            )
            
            await self.channel.send(content=self.user.mention, embed=embed)
        else:
            # SennaBot wins - take 1000 medals from user and give to SennaBot
            
            # Take medals from user
            user_data["savings"] = user_data.get("savings", 0) - CHALLENGE_BET
            
            # Get or create SennaBot data
            sennabot_data = DataService.get_user_data(self.guild_id, SENNABOT_ID, "SennaBot")
            sennabot_data["savings"] = sennabot_data.get("savings", 0) + CHALLENGE_BET
            
            # Send user to Jaeger Camp
            user_data["prison"] = {
                "tier": "Jaeger Camp", 
                "release_time": int(time.time()) + 3600  # 1 hour
            }
            
            # Save user and sennabot data
            guild_data = DataService.load_guild_data(self.guild_id)
            guild_data[str(self.user.id)] = user_data
            guild_data[str(SENNABOT_ID)] = sennabot_data
            
            # Send everyone else to Rook Division (only if they have data)
            for member_id, member_data in guild_data.items():
                # Skip non-user entries, SennaBot, and the challenger
                if not member_id.isdigit() or member_id in [str(self.user.id), str(SENNABOT_ID)]:
                    continue
                
                # Ensure this is valid user data
                if not isinstance(member_data, dict):
                    continue
                
                # Send to prison
                member_data["prison"] = {
                    "tier": "Rook Division", 
                    "release_time": int(time.time()) + 21600  # 6 hours
                }
            
            # Save all changes
            DataService.save_guild_data(self.guild_id, guild_data)
            
            # Send loss message
            loss_msg = (
                f"***The house always wins...***\n\n"
                f"**{CHALLENGE_BET}** Medals was taken from your savings and you have been thrown into the **Jaeger Camp**.\n\n"
                f"Everyone you have considered a friend has been transported to spend time with the **Rook Division** for this gamble. :<"
            )
            
            embed = discord.Embed(
                title=f"{self.user.display_name} Failed",
                description=loss_msg,
                color=discord.Color.red()
            )
            
            await self.channel.send(content=self.user.mention, embed=embed)


class BlackjackChallengeView(discord.ui.View):
    def __init__(self, challenge_manager, user_hand, bot_hand, deck):
        super().__init__(timeout=CHALLENGE_TIMEOUT)  # Longer timeout
        self.challenge_manager = challenge_manager
        self.user_hand = user_hand
        self.bot_hand = bot_hand
        self.deck = deck
        self.game_over = False
        self.message = None  # Will store the message this view is attached to
        self.debug = DebugTools.get_debugger("blackjack_challenge_view")
    
    async def on_timeout(self):
        if not self.game_over:
            # On timeout, bot automatically wins the round
            self.game_over = True
            
            # If we have a message reference, update it
            if self.message:
                try:
                    await self.message.edit(
                        embed=discord.Embed(
                            title="Timeout!",
                            description=f"You took too long to respond! **SennaBot wins this round. :/**",
                            color=discord.Color.red()
                        ),
                        view=None
                    )
                except Exception as e:
                    self.debug.log(f"Error updating message on timeout: {e}")
                
                # Update the challenge manager score
                self.challenge_manager.bot_wins += 1
                
                # Check if bot has won the challenge
                if self.challenge_manager.bot_wins >= self.challenge_manager.wins_needed:
                    await self.challenge_manager.end_challenge(False)
                else:
                    # Continue to next game
                    await self.challenge_manager.play_next_game()
            else:
                # If we don't have a message reference, send a new one
                await self.challenge_manager.channel.send(
                    content=self.challenge_manager.user.mention,
                    embed=discord.Embed(
                        title="Timeout!",
                        description=f"You took too long to respond! **SennaBot wins this round. :/**",
                        color=discord.Color.red()
                    )
                )
                
                # Update the challenge manager score
                self.challenge_manager.bot_wins += 1
                
                # Check if bot has won the challenge
                if self.challenge_manager.bot_wins >= self.challenge_manager.wins_needed:
                    await self.challenge_manager.end_challenge(False)
                else:
                    # Continue to next game
                    await self.challenge_manager.play_next_game()
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the interaction user is the challenge user
        if interaction.user.id != self.challenge_manager.user.id:
            await interaction.response.send_message("**Your fate is in their hands now.**", ephemeral=True)
            return
        
        # Store the message if not already stored
        if not self.message:
            self.message = interaction.message
        
        # Draw a card
        self.user_hand.append(self.deck.pop())
        user_value = calculate_hand_value(self.user_hand)
        
        # Update the embed
        user_cards = " ".join([f"{face}{suit}" for face, suit in self.user_hand])
        bot_visible_card = f"{self.bot_hand[0][0]}{self.bot_hand[0][1]}"
        
        embed = discord.Embed(
            title=f"Defeat SennaBot - Round {self.challenge_manager.games_played}",
            description=f"The stakes: **{CHALLENGE_BET}** Medals",
            color=discord.Color.gold()
        )
        
        # Include scoreboard
        embed.add_field(
            name="Current Score",
            value=f"{self.challenge_manager.user.display_name}: {self.challenge_manager.user_wins} wins\nSennaBot: {self.challenge_manager.bot_wins} wins\n\nFirst to {self.challenge_manager.wins_needed} wins!",
            inline=False
        )
        
        embed.add_field(
            name=f"Your Hand ({user_value})",
            value=user_cards,
            inline=False
        )
        
        embed.add_field(
            name=f"SennaBot's Hand (Showing {CARD_VALUES[self.bot_hand[0][0]]})",
            value=f"{bot_visible_card} 🂠",
            inline=False
        )
        
        # Check if user busted
        if user_value > 21:
            self.game_over = True
            await interaction.response.edit_message(embed=embed, view=None)
            
            # Directly integrate the game result
            await self.challenge_manager.show_game_result(
                interaction.message, 
                self.user_hand, 
                self.bot_hand, 
                False,  # User loses
                False   # Not a tie
            )
            return
        
        # Update the timeout with each response
        self.timeout = CHALLENGE_TIMEOUT
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the interaction user is the challenge user
        if interaction.user.id != self.challenge_manager.user.id:
            await interaction.response.send_message("**Your fate is in their hands now.**", ephemeral=True)
            return
        
        # Store the message if not already stored
        if not self.message:
            self.message = interaction.message
        
        # Bot's turn
        bot_value = calculate_hand_value(self.bot_hand)
        
        # Bot draws until 17 or higher
        while bot_value < 17:
            self.bot_hand.append(self.deck.pop())
            bot_value = calculate_hand_value(self.bot_hand)
        
        # Game is over
        self.game_over = True
        
        # Determine winner
        user_value = calculate_hand_value(self.user_hand)
        user_win = False
        is_tie = False
        
        if bot_value > 21:
            user_win = True
        elif user_value > 21:
            user_win = False
        elif user_value > bot_value:
            user_win = True
        elif bot_value > user_value:
            user_win = False
        else:
            is_tie = True
        
        await interaction.response.edit_message(view=None)
        
        # Show the game result integrated with the current message
        await self.challenge_manager.show_game_result(
            interaction.message,
            self.user_hand,
            self.bot_hand,
            user_win,
            is_tie
        )


def calculate_hand_value(hand):
    """Calculate the value of a blackjack hand"""
    value = 0
    aces = 0
    
    for card in hand:
        face, _ = card
        value += CARD_VALUES[face]
        if face == 'A':
            aces += 1
    
    # Adjust for aces
    while value > 21 and aces > 0:
        value -= 10  # Convert Ace from 11 to 1
        aces -= 1
        
    return value


# Global instance of the balance challenge manager - initialize properly
balance_challenge_manager = BalanceChallengeManager()


# Utility function to check if a user is in a challenge
def is_in_challenge(user_id: int) -> bool:
    """Check if a user is currently in an active challenge"""
    global balance_challenge_manager
    return balance_challenge_manager.is_in_challenge(user_id)


@CommandRegistry.register_cog("economy")
class BalanceChallengeCog(EconomyCog):
    """Enforces wealth cap by challenging users who exceed a threshold."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing BalanceChallengeCog")
        self.donation_check_locks = {}  # Track which users we're checking to avoid duplicates
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return []  # No direct commands for this cog
    
    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction, command):
        try:
            # Special handling for donate command 
            if interaction.command and interaction.command.name == "donate":
                # Extract the target from options
                target = None
                
                try:
                    options = interaction.data.get("options", [])
                    for option in options:
                        if option.get("name") == "target":
                            target_id = option.get("value")
                            self.debug.log(f"Found target ID: {target_id}")
                            
                            # Try to resolve the target using fetch_user first
                            target = await self.bot.fetch_user(int(target_id))
                            if not target:
                                self.debug.log(f"Failed to fetch user with ID {target_id}")
                                continue
                                
                            # Try to resolve as member if possible
                            try:
                                member = await interaction.guild.fetch_member(int(target_id))
                                if member:
                                    target = member
                            except:
                                # Continue with the user object if we can't get the member
                                pass
                                
                            self.debug.log(f"Resolved target: {target.display_name if target else 'None'}")
                            break
                except Exception as e:
                    self.debug.log(f"Error extracting or resolving target from donate command: {e}")
                
                if target and target.id != interaction.user.id:
                    # Avoid checking the same target multiple times simultaneously
                    if target.id in self.donation_check_locks:
                        self.debug.log(f"Target {target.id} already being checked, skipping")
                        return
                    
                    # Set a lock for this target
                    self.donation_check_locks[target.id] = True
                    
                    try:
                        # Wait longer for the donation to complete and balances to update
                        self.debug.log(f"Waiting for donation to complete...")
                        await asyncio.sleep(3.0)
                        
                        # Check if the target now meets the challenge threshold
                        result = await balance_challenge_manager.trigger_challenge_for_donation_target(
                            self.bot, interaction.guild, target
                        )
                        self.debug.log(f"Challenge trigger result for {target.display_name}: {result}")
                    finally:
                        # Clear the lock regardless of the outcome
                        if target.id in self.donation_check_locks:
                            del self.donation_check_locks[target.id]
                else:
                    self.debug.log(f"Target not found or is self")
            
            # Normal check for the user who initiated the command
            if interaction.command and interaction.command.name in [
                # General commands that earn medals
                "work", "crime", "rob", 
                # Gambling commands
                "roulette", "blackjack", 
                # Banking commands
                "deposit", "withdraw", "donate",
                # Any other commands that might affect balance
                "balance"
            ]:
                await balance_challenge_manager.trigger_balance_challenge(self.bot, interaction)

        except Exception as e:
            self.debug.log(f"Error triggering balance challenge: {e}")