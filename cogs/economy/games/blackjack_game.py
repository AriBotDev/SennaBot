"""
Blackjack game implementation.
Provides the blackjack command for gambling.
"""
import discord
import random
import asyncio
import time  # Add this import
from discord import app_commands, ui
from discord.ext import commands
from athena.cmd_registry import CommandRegistry
from athena.data_service import DataService
from athena.debug_tools import DebugTools
from ..economy_base import EconomyCog

# Card suits and values
SUITS = ['♠️', '♥️', '♦️', '♣️']
CARD_VALUES = {
    'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10
}
CARD_FACES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Track active games
ACTIVE_GAMES = {}  # (player_id, guild_id) -> game instance

# Setup debugger
debug = DebugTools.get_debugger("blackjack_game")

class BlackjackGame:
    """Manages a blackjack game between two players."""
    
    def __init__(self, initiator, opponent, bet):
        """Initialize a blackjack game."""
        self.initiator = initiator
        self.opponent = opponent
        self.bet = bet
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        
        # Deal initial cards
        self.initiator_hand = [self.draw_card(), self.draw_card()]
        self.opponent_hand = [self.draw_card(), self.draw_card()]
        
        # Game state
        self.current_turn = initiator
        self.initiator_stood = False
        self.opponent_stood = False
        self.game_over = False
        self.winner = None
        self.blackjack_bonus = False
        
        # Pot tracking
        self.pot = bet * 2  # Both players contribute the bet amount
    
    def create_deck(self):
        """Create a standard 52-card deck."""
        deck = []
        for suit in SUITS:
            for face in CARD_FACES:
                deck.append((face, suit))
        return deck
    
    def draw_card(self):
        """Draw a card from the deck."""
        if not self.deck:
            # Create and shuffle a new deck if we run out
            self.deck = self.create_deck()
            random.shuffle(self.deck)
        return self.deck.pop()
    
    def calculate_hand_value(self, hand):
        """Calculate the value of a blackjack hand."""
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
    
    def hit(self, player):
        """Player draws a card."""
        if player.id == self.initiator.id:
            self.initiator_hand.append(self.draw_card())
            if self.calculate_hand_value(self.initiator_hand) > 21:
                self.initiator_stood = True
                self.check_game_over()
        else:
            self.opponent_hand.append(self.draw_card())
            if self.calculate_hand_value(self.opponent_hand) > 21:
                self.opponent_stood = True
                self.check_game_over()
    
    def stand(self, player):
        """Player stands (stops drawing cards)."""
        if player.id == self.initiator.id:
            self.initiator_stood = True
        else:
            self.opponent_stood = True
        
        self.check_game_over()
    
    def check_game_over(self):
        """Check if the game is over."""
        if self.initiator_stood and self.opponent_stood:
            self.game_over = True
            self.determine_winner()
            return True
        
        if self.initiator_stood:
            self.current_turn = self.opponent
        elif self.opponent_stood:
            self.current_turn = self.initiator
            
        return False
    
    def determine_winner(self):
        """Determine the winner of the game."""
        initiator_value = self.calculate_hand_value(self.initiator_hand)
        opponent_value = self.calculate_hand_value(self.opponent_hand)
        
        initiator_blackjack = len(self.initiator_hand) == 2 and initiator_value == 21
        opponent_blackjack = len(self.opponent_hand) == 2 and opponent_value == 21
        
        # Check for blackjack
        if initiator_blackjack and not opponent_blackjack:
            self.winner = self.initiator
            self.blackjack_bonus = True
            return
        
        if opponent_blackjack and not initiator_blackjack:
            self.winner = self.opponent
            self.blackjack_bonus = True
            return
        
        # Check for busts
        if initiator_value > 21:
            if opponent_value > 21:
                self.winner = None  # Both bust, it's a tie
            else:
                self.winner = self.opponent
            return
        
        if opponent_value > 21:
            self.winner = self.initiator
            return
        
        # Compare values
        if initiator_value > opponent_value:
            self.winner = self.initiator
        elif opponent_value > initiator_value:
            self.winner = self.opponent
        else:
            self.winner = None  # Tie
    
    def get_embed_for_player(self, player, game_over=False):
        """Generate an embed display for a player."""
        is_initiator = player.id == self.initiator.id
        
        if is_initiator:
            own_hand = self.initiator_hand
            opponent_hand = self.opponent_hand
            own_name = self.initiator.display_name
            opponent_name = self.opponent.display_name
        else:
            own_hand = self.opponent_hand
            opponent_hand = self.initiator_hand
            own_name = self.opponent.display_name
            opponent_name = self.initiator.display_name
        
        own_value = self.calculate_hand_value(own_hand)
        
        # Create the embed
        embed = discord.Embed(
            title="Blackjack",
            description=f"Bet: **{self.bet}** Medals each\nTotal Pot: **{self.pot}** Medals",
            color=discord.Color.gold()
        )
        
        # Show both hands based on game state
        if game_over:
            # Show all cards
            initiator_cards = " ".join([f"{face}{suit}" for face, suit in self.initiator_hand])
            opponent_cards = " ".join([f"{face}{suit}" for face, suit in self.opponent_hand])
            
            initiator_value = self.calculate_hand_value(self.initiator_hand)
            opponent_value = self.calculate_hand_value(self.opponent_hand)
            
            embed.add_field(
                name=f"{self.initiator.display_name}'s Hand ({initiator_value})",
                value=initiator_cards or "No cards",
                inline=False
            )
            
            embed.add_field(
                name=f"{self.opponent.display_name}'s Hand ({opponent_value})",
                value=opponent_cards or "No cards",
                inline=False
            )
            
            # Show result
            if self.winner:
                embed.add_field(
                    name="Result",
                    value=f"**{self.winner.display_name}** wins! :D" + (" (Blackjack!)" if self.blackjack_bonus else ""),
                    inline=False
                )
            else:
                embed.add_field(name="Result", value="It's a tie. :/", inline=False)
                
        else:
            # During game: show your cards and only first card of opponent
            own_cards = " ".join([f"{face}{suit}" for face, suit in own_hand])
            
            # For opponent, show first card and hide the rest
            opponent_visible = [opponent_hand[0]]
            opponent_hidden = opponent_hand[1:]
            opponent_visible_cards = " ".join([f"{face}{suit}" for face, suit in opponent_visible])
            opponent_hidden_cards = " 🂠" * len(opponent_hidden)  # Card back symbol
            
            # Calculate the visible value safely
            opponent_visible_value = self.calculate_hand_value(opponent_visible)
            
            embed.add_field(
                name=f"Your Hand ({own_value})",
                value=own_cards or "No cards",
                inline=False
            )
            
            embed.add_field(
                name=f"{opponent_name}'s Hand (Showing {opponent_visible_value})",
                value=f"{opponent_visible_cards}{opponent_hidden_cards}",
                inline=False
            )
            
            # Show whose turn it is
            if not self.game_over:
                turn_name = self.current_turn.display_name
                turn_status = ""
                if self.initiator_stood:
                    turn_status = f"\n{self.initiator.display_name} has stood."
                if self.opponent_stood:
                    turn_status = f"\n{self.opponent.display_name} has stood."
                
                embed.add_field(
                    name="Current Turn",
                    value=f"It's **{turn_name}**'s turn.{turn_status}",
                    inline=False
                )
        
        return embed

class BlackjackInviteView(ui.View):
    """Invitation view for a blackjack game."""
    
    def __init__(self, cog, initiator, opponent, bet):
        super().__init__(timeout=30)
        self.cog = cog
        self.initiator = initiator
        self.opponent = opponent
        self.bet = bet
        self.response = None
        self.message = None
    
    @ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept_button(self, interaction: discord.Interaction, button: ui.Button):
        """Handle acceptance of the blackjack invitation."""
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("WHO ARE YOU?", ephemeral=True)
            return
        
        # Check if opponent has enough funds
        opponent_pockets = self.cog.get_pockets(interaction.guild.id, self.opponent)
        if opponent_pockets < self.bet:
            await interaction.response.send_message(
                f"You don't have enough Medals to accept this bet....", 
                ephemeral=True
            )
            self.response = "insufficient_funds"
            self.stop()
            return
        
        self.response = "accepted"
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Blackjack Accepted!",
                description=f"{self.opponent.mention} has accepted {self.initiator.mention}'s blackjack game for **{self.bet}** Medals each. Good luck :>",
                color=discord.Color.green()
            ),
            view=None
        )
        self.stop()
    
    @ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline_button(self, interaction: discord.Interaction, button: ui.Button):
        """Handle rejection of the blackjack invitation."""
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("WHO ARE YOU?", ephemeral=True)
            return
        
        self.response = "declined"
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Blackjack Declined",
                description=f"{self.opponent.mention} has declined {self.initiator.mention}'s blackjack game :<",
                color=discord.Color.red()
            ),
            view=None
        )
        self.stop()
    
    async def on_timeout(self):
        """Handle timeout of the invitation."""
        self.response = "timeout"
        try:
            if self.message:
                await self.message.edit(
                    embed=discord.Embed(
                        title="Blackjack Expired",
                        description=f"{self.opponent.mention} did not respond to {self.initiator.mention}'s blackjack challenge in time >:c)",
                        color=discord.Color.red()
                    ),
                    view=None
                )
        except Exception as e:
            debug.log(f"Error in BlackjackInviteView on_timeout: {e}")

class PlayerGameControlView(ui.View):
    """Game control view for a player in blackjack."""
    
    def __init__(self, main_game_view, player):
        super().__init__(timeout=180)
        self.main_game_view = main_game_view
        self.player = player
        self.game = main_game_view.game
        self.action_taken = False
    
    @ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: ui.Button):
        """Handle the hit action."""
        # Check if it's the user's turn
        if interaction.user.id != self.game.current_turn.id:
            await interaction.response.send_message("It's not your turn >:c", ephemeral=True)
            return
        
        # Execute the hit
        self.game.hit(interaction.user)
        self.action_taken = True
        
        # Update the game display
        await self.main_game_view.update_public_display()
        
        # Check if player busted or if game is over
        player_hand = self.game.initiator_hand if interaction.user.id == self.game.initiator.id else self.game.opponent_hand
        player_value = self.game.calculate_hand_value(player_hand)
        
        if self.game.game_over:
            # Game ended due to this action
            await interaction.response.send_message(
                content=f"You hit and got a total of {player_value}. Game over!",
                ephemeral=True
            )
            await self.main_game_view.handle_game_over(interaction)
            self.stop()
        elif player_value > 21:
            # Player busted
            await interaction.response.send_message(
                content=f"You hit and busted with {player_value}! Waiting for opponent to play.",
                ephemeral=True
            )
            # Continue to opponent's turn
            await self.main_game_view.next_player_turn()
            self.stop()
        else:
            # Show updated hand
            updated_embed = self.game.get_embed_for_player(interaction.user)
            await interaction.response.send_message(
                content=f"You hit! Your new total is {player_value}.",
                embed=updated_embed,
                view=self,  # Keep the same view for continuous play
                ephemeral=True
            )
    
    @ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand_button(self, interaction: discord.Interaction, button: ui.Button):
        """Handle the stand action."""
        # Check if it's the user's turn
        if interaction.user.id != self.game.current_turn.id:
            await interaction.response.send_message("It's not your turn >:c", ephemeral=True)
            return
        
        # Execute the stand
        self.game.stand(interaction.user)
        self.action_taken = True
        
        # Update the game display
        await self.main_game_view.update_public_display()
        
        # Check if game is over
        if self.game.game_over:
            await interaction.response.send_message(
                content="You stood. Game over!",
                ephemeral=True
            )
            await self.main_game_view.handle_game_over(interaction)
        else:
            # Move to next player
            await interaction.response.send_message(
                content="You stood. Waiting for opponent to play.",
                ephemeral=True
            )
            await self.main_game_view.next_player_turn()
        
        self.stop()
    
    async def on_timeout(self):
        """Handle timeout of the game control."""
        if not self.action_taken:
            # Player didn't take action within time limit
            self.game.stand(self.player)  # Auto-stand for inactive player
            await self.main_game_view.update_public_display()
            
            if self.game.game_over:
                await self.main_game_view.handle_timeout()
            else:
                await self.main_game_view.next_player_turn()

class TurnNotificationView(ui.View):
    """Notification view for a player's turn."""
    
    def __init__(self, game_view, player):
        super().__init__(timeout=180)
        self.game_view = game_view
        self.player = player
        self.responded = False  # Track if the player has responded
    
    @ui.button(label="Show Cards & Play", style=discord.ButtonStyle.primary)
    async def show_cards_button(self, interaction: discord.Interaction, button: ui.Button):
        """Show cards and play button."""
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("This isn't your game.", ephemeral=True)
            return
        
        game = self.game_view.game
        if interaction.user.id != game.current_turn.id:
            await interaction.response.send_message("It's not your turn.", ephemeral=True)
            return
        
        # Mark this notification as responded to
        self.responded = True
        
        # Create a special game control view just for this player
        player_view = PlayerGameControlView(self.game_view, interaction.user)
        
        player_embed = game.get_embed_for_player(interaction.user)
        await interaction.response.send_message(
            content="Your turn in blackjack:",
            embed=player_embed,
            view=player_view,
            ephemeral=True
        )
        
        # Wait for the player to make their move
        await player_view.wait()
        
        # This view is done
        self.stop()

class BlackjackGameView(ui.View):
    """Main game view for blackjack."""
    
    def __init__(self, game, cog, channel):
        super().__init__(timeout=180)  # 3 minute timeout
        self.game = game
        self.cog = cog
        self.channel = channel
        self.game_message = None  # Public game status message
        self.turn_messages = []   # Keep track of turn notification messages for cleanup
        self.turn_notifications = {}  # Track active turn notifications by player ID
        self.finished = False  # Flag to track if the game was properly finished
        self.last_activity = time.time()  # Track last activity time
    
    def register_game(self):
        """Register this game in active games tracking."""
        player_key = f"{self.game.initiator.id}-{self.channel.guild.id}"
        opponent_key = f"{self.game.opponent.id}-{self.channel.guild.id}"
        ACTIVE_GAMES[player_key] = self.game
        ACTIVE_GAMES[opponent_key] = self.game
        debug.log(f"Registered game for {player_key} and {opponent_key}")

    def unregister_game(self):
        """Remove this game from active games tracking."""
        try:
            player_key = f"{self.game.initiator.id}-{self.channel.guild.id}"
            opponent_key = f"{self.game.opponent.id}-{self.channel.guild.id}"
            if player_key in ACTIVE_GAMES:
                del ACTIVE_GAMES[player_key]
            if opponent_key in ACTIVE_GAMES:
                del ACTIVE_GAMES[opponent_key]
            debug.log(f"Unregistered game for {player_key} and {opponent_key}")
        except Exception as e:
            debug.log(f"Error unregistering game: {e}")
    
    async def update_public_display(self):
        """Update the public game message in the channel."""
        if not self.game_message:
            return
        
        # Update last activity time
        self.last_activity = time.time()
            
        # Create public embed that shows game state without revealing hidden cards
        public_embed = discord.Embed(
            title="Blackjack Game",
            description=f"Bet: **{self.game.bet}** Medals each\nTotal Pot: **{self.game.pot}** Medals",
            color=discord.Color.gold()
        )
        
        # Show whose turn it is
        turn_name = self.game.current_turn.display_name
        public_embed.add_field(
            name="Current Turn",
            value=f"It's **{turn_name}**'s turn.",
            inline=False
        )
        
        # Show partial hands in public view (only first card visible)
        initiator_visible = [self.game.initiator_hand[0]]
        initiator_hidden = self.game.initiator_hand[1:]
        initiator_visible_cards = " ".join([f"{face}{suit}" for face, suit in initiator_visible])
        initiator_hidden_cards = " 🂠" * len(initiator_hidden)
        
        opponent_visible = [self.game.opponent_hand[0]]
        opponent_hidden = self.game.opponent_hand[1:]
        opponent_visible_cards = " ".join([f"{face}{suit}" for face, suit in opponent_visible])
        opponent_hidden_cards = " 🂠" * len(opponent_hidden)
        
        public_embed.add_field(
            name=f"{self.game.initiator.display_name}'s Hand (Showing {self.game.calculate_hand_value(initiator_visible)})",
            value=f"{initiator_visible_cards}{initiator_hidden_cards}",
            inline=False
        )
        
        public_embed.add_field(
            name=f"{self.game.opponent.display_name}'s Hand (Showing {self.game.calculate_hand_value(opponent_visible)})",
            value=f"{opponent_visible_cards}{opponent_hidden_cards}",
            inline=False
        )
        
        # Add status info
        status = ""
        if self.game.initiator_stood:
            status += f"{self.game.initiator.display_name} has stood.\n"
        if self.game.opponent_stood:
            status += f"{self.game.opponent.display_name} has stood.\n"
        
        if status:
            public_embed.add_field(name="Status", value=status, inline=False)
        
        # Update the public message
        try:
            await self.game_message.edit(embed=public_embed)
        except Exception as e:
            debug.log(f"Error updating public game display: {e}")
    
    async def next_player_turn(self):
        """Initiates the next player's turn."""
        # Send turn notification to the current player
        current_player = self.game.current_turn
        await self.notify_player_turn(current_player)
    
    async def notify_player_turn(self, player):
        """Send a notification to the player that it's their turn."""
        # Create a view for the player to see their cards
        turn_view = TurnNotificationView(self, player)
        
        # Send a notification in the channel with a button for the player
        try:
            turn_message = await self.channel.send(
                content=f"{player.mention}, it's your turn in blackjack!",
                view=turn_view
            )
            # Add to list of messages to clean up later
            self.turn_messages.append(turn_message)
            
            # Store the notification view
            self.turn_notifications[player.id] = turn_view
            
            # Wait for the player to respond
            await turn_view.wait()
            
            # If player didn't respond, handle it as a timeout
            if not turn_view.responded and not self.game.game_over:
                # Auto-stand for this player
                self.game.stand(player)
                await self.update_public_display()
                
                # Check if game is over, otherwise continue to next player
                if self.game.game_over:
                    await self.handle_timeout()
                else:
                    # Continue to next player's turn
                    await self.next_player_turn()
        except Exception as e:
            debug.log(f"Error sending turn notification: {e}")

    async def cleanup_messages(self):
        """Clean up all turn notification messages."""
        for message in self.turn_messages:
            try:
                await message.delete()
            except Exception as e:
                debug.log(f"Error deleting message: {e}")
        
        # Clear the list after deletion attempts
        self.turn_messages = []
    
    async def cleanup_game(self, message=None):
        """Clean up all resources for this game."""
        try:
            # Unregister from active games
            self.unregister_game()
            
            # Clean up turn messages
            await self.cleanup_messages()
            
            # Clean up game message if not already handled
            if self.game_message and not message:
                try:
                    await self.game_message.delete()
                except Exception as e:
                    debug.log(f"Error deleting game message: {e}")
                    # Don't throw, continue cleanup
            
            # Clear any stored references
            for player_id in self.turn_notifications:
                try:
                    # Stop all pending notifications
                    notification = self.turn_notifications[player_id]
                    notification.stop()
                except Exception as e:
                    debug.log(f"Error stopping notification: {e}")
        except Exception as e:
            debug.log(f"Error in game cleanup: {e}")
    
    async def handle_game_over(self, interaction):
        """Handle the end of the game."""
        try:
            guild_id = interaction.guild.id
            initiator = self.game.initiator
            opponent = self.game.opponent
            bet = self.game.bet
            pot = self.game.pot
            
            # Mark the game as finished properly
            self.finished = True
            
            # Determine payouts
            if self.game.winner is None:
                # It's a tie, return the bet to both players
                message = f"The game ended in a tie. Both players get their **{bet}** Medals back."
                self.cog.update_pockets(guild_id, initiator, bet)
                self.cog.update_pockets(guild_id, opponent, bet)
            else:
                # Winner takes all
                if self.game.blackjack_bonus:
                    bonus = int(bet * 0.5)  # 50% bonus for blackjack
                    total_winnings = pot + bonus
                    message = f"**{self.game.winner.display_name}** wins with a Blackjack! They take the entire pot of **{pot}** Medals plus a bonus of **{bonus}** Medals for a total of **{total_winnings}** Medals c:<"
                    self.cog.update_pockets(guild_id, self.game.winner, total_winnings)
                else:
                    message = f"**{self.game.winner.display_name}** wins and takes the entire pot of **{pot}** Medals! c:<"
                    self.cog.update_pockets(guild_id, self.game.winner, pot)
            
            # Create the final result embed
            result_embed = discord.Embed(
                title="Blackjack Game Over",
                description=message,
                color=discord.Color.gold()
            )
            
            # Show final hands
            initiator_cards = " ".join([f"{face}{suit}" for face, suit in self.game.initiator_hand])
            opponent_cards = " ".join([f"{face}{suit}" for face, suit in self.game.opponent_hand])
            
            initiator_value = self.game.calculate_hand_value(self.game.initiator_hand)
            opponent_value = self.game.calculate_hand_value(self.game.opponent_hand)
            
            result_embed.add_field(
                name=f"{initiator.display_name}'s Hand ({initiator_value})",
                value=initiator_cards,
                inline=False
            )
            
            result_embed.add_field(
                name=f"{opponent.display_name}'s Hand ({opponent_value})",
                value=opponent_cards,
                inline=False
            )

            # Clean up all resources
            await self.cleanup_game(interaction.message)
            
            # Send a fresh result message
            try:
                await self.channel.send(
                    content=f"🂠 **BLACKJACK GAME RESULTS** 🂠\n{initiator.mention} vs {opponent.mention}",
                    embed=result_embed
                )
            except Exception as e:
                debug.log(f"Error sending final result message: {e}")
                # Use centralized error handler for this error
                from athena.error_handler import ErrorHandler
                ErrorHandler.handle_event_error("blackjack_game_results", e, 
                                            {"game_id": f"{initiator.id}-{opponent.id}"})
            
            self.stop()
        except Exception as e:
            # Use centralized error handler for any error in this method
            from athena.error_handler import ErrorHandler
            debug.log(f"Error in handle_game_over: {e}")
            ErrorHandler.handle_event_error("blackjack_game_over", e, 
                                        {"game_id": f"{self.game.initiator.id}-{self.game.opponent.id}"})
    
    async def handle_timeout(self):
        """Handle case where one player times out during active turn."""
        # The player whose turn it was forfeits
        if self.game.current_turn.id == self.game.initiator.id:
            self.game.winner = self.game.opponent
        else:
            self.game.winner = self.game.initiator
            
        # Mark the game as finished properly
        self.finished = True
            
        # Give the pot to the winner
        guild_id = self.channel.guild.id
        self.cog.update_pockets(guild_id, self.game.winner, self.game.pot)
        
        # Create timeout embed
        timeout_embed = discord.Embed(
            title="Blackjack Game Timed Out",
            description=f"The game has ended due to inactivity...(lame)\n\n**{self.game.winner.display_name}** wins by default!",
            color=discord.Color.red()
        )
        
        # Clean up all resources
        await self.cleanup_game()
        
        # Send fresh timeout message
        try:
            await self.channel.send(
                content=f"⏰ **BLACKJACK GAME TIMED OUT** ⏰\n{self.game.initiator.mention} vs {self.game.opponent.mention}",
                embed=timeout_embed
            )
        except Exception as e:
            debug.log(f"Error sending timeout message: {e}")
        
        self.stop()
    
    async def cancel_game(self):
        """Cancel the game and return bets to players."""
        # Mark the game as finished properly
        self.finished = True
        
        # Return bets to players
        guild_id = self.channel.guild.id
        self.cog.update_pockets(guild_id, self.game.initiator, self.game.bet)
        self.cog.update_pockets(guild_id, self.game.opponent, self.game.bet)
        
        # Clean up all resources
        await self.cleanup_game()
        
        # Send cancellation message
        try:
            await self.channel.send(
                content=f"❌ **BLACKJACK GAME CANCELLED** ❌\n{self.game.initiator.mention} vs {self.game.opponent.mention}",
                embed=discord.Embed(
                    title="Blackjack Game Cancelled",
                    description=f"The game has been cancelled due to inactivity. Bets have been returned to the players.",
                    color=discord.Color.red()
                )
            )
        except Exception as e:
            debug.log(f"Error sending cancellation message: {e}")
    
    async def on_timeout(self):
        """Handle timeout of the game view."""
        try:
            # Check if the game was already completed
            if self.finished:
                # Game already finished, just clean up any remaining messages
                await self.cleanup_messages()
                return
                
            # If a game is still in progress when the view times out, cancel it
            await self.cancel_game()
        except Exception as e:
            debug.log(f"Error in timeout handler: {e}")

@CommandRegistry.register_cog("economy")
class BlackjackCog(EconomyCog):
    """Provides the blackjack command for gambling with other players."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.debug.log("Initializing BlackjackCog")
    
    def get_app_commands(self):
        """Get all app commands from this cog."""
        return [self.blackjack]
    
    @app_commands.command(name="blackjack", description="Challenge another player to a game of blackjack for Medals.")
    @app_commands.describe(opponent="The player you want to challenge", bet="How many Medals to bet")
    async def blackjack(self, interaction: discord.Interaction, opponent: discord.Member, bet: int):
        """Challenge another player to blackjack."""
        # Check prison status
        if not await self.check_prison_status(interaction):
            return
            
        # Check balance challenge status
        if not await self.check_balance_challenge(interaction):
            return
        
        # Check if opponent is in prison
        opponent_data = DataService.get_user_data(
            interaction.guild.id, 
            opponent.id, 
            opponent.display_name
        )
        opponent_prison = opponent_data.get("prison")
        if opponent_prison:
            return await self.send_embed(
                interaction, 
                "Prison Restriction",
                f"{opponent.mention} is currently in prison with the **{opponent_prison['tier']}** and cannot play blackjack. (asshole)",
                discord.Color.red(), 
                ephemeral=True
            )

        # Check if opponent is valid
        if opponent.id == interaction.user.id:
            return await self.send_embed(
                interaction, 
                "Error",
                "You can't challenge yourself to blackjack...",
                discord.Color.red(), 
                ephemeral=True
            )
        
        if opponent.bot:
            return await self.send_embed(
                interaction, 
                "Error",
                "I'd wipe the floor against you",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Check if the bet is valid
        if bet <= 0:
            return await self.send_embed(
                interaction, 
                "Error",
                "The bet must be greater than 0 Medals.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Check if initiator has enough funds
        initiator_pockets = self.get_pockets(interaction.guild.id, interaction.user)
        if initiator_pockets < bet:
            return await self.send_embed(
                interaction, 
                "Error",
                f"You don't have enough Medals for this bet. You need {bet} but only have {initiator_pockets}.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Check if opponent has enough funds
        opponent_pockets = self.get_pockets(interaction.guild.id, opponent)
        if opponent_pockets < bet:
            return await self.send_embed(
                interaction, 
                "Error",
                f"{opponent.display_name} doesn't have enough Medals for this bet. They need {bet} but only have {opponent_pockets}.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Check if the users are already in a game
        player_key = f"{interaction.user.id}-{interaction.guild.id}"
        opponent_key = f"{opponent.id}-{interaction.guild.id}"
        
        if player_key in ACTIVE_GAMES or opponent_key in ACTIVE_GAMES:
            return await self.send_embed(
                interaction, 
                "Error",
                "You or your opponent is already in a blackjack game.",
                discord.Color.red(), 
                ephemeral=True
            )
        
        # Create the invitation view
        invite_view = BlackjackInviteView(self, interaction.user, opponent, bet)
        
        # Send the invitation
        invite_embed = discord.Embed(
            title="Blackjack Challenge!",
            description=f"{interaction.user.mention} has challenged {opponent.mention} to a game of blackjack with a bet of **{bet}** Medals each.",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=invite_embed, view=invite_view)
        
        # Store the message for the view
        invite_view.message = await interaction.original_response()
        
        # Wait for a response
        await invite_view.wait()
        
        # Handle all possible responses properly
        if invite_view.response == "accepted":
            try:
                # Deduct the bet amount from both players immediately
                self.update_pockets(interaction.guild.id, interaction.user, -bet)
                self.update_pockets(interaction.guild.id, opponent, -bet)
                
                # Start the game
                game = BlackjackGame(interaction.user, opponent, bet)
                game_view = BlackjackGameView(game, self, interaction.channel)
                
                # Register the active game
                game_view.register_game()
                
                # Send the public game interface to the channel
                game_embed = discord.Embed(
                    title="Blackjack Game",
                    description=f"Bet: **{bet}** Medals each\nTotal Pot: **{game.pot}** Medals\n\nGame is starting...",
                    color=discord.Color.gold()
                )
                game_message = await interaction.followup.send(
                    content=f"🂠 Blackjack game between {interaction.user.mention} and {opponent.mention} has started!",
                    embed=game_embed
                )
                game_view.game_message = game_message
                
                # Update the public display
                await game_view.update_public_display()
                
                # Start the game with the first player's turn
                await game_view.notify_player_turn(game.initiator)
                
                # Wait for the game to complete
                await game_view.wait()
                
                # Game is now complete (cleanup handled in respective methods)
            except Exception as e:
                debug.log(f"Error in blackjack game: {e}")
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Blackjack Error",
                        description=f"An error occurred while running the game: {e}",
                        color=discord.Color.red()
                    )
                )
                
                # Clean up active games entries if they exist
                if player_key in ACTIVE_GAMES:
                    del ACTIVE_GAMES[player_key]
                if opponent_key in ACTIVE_GAMES:
                    del ACTIVE_GAMES[opponent_key]
                
        elif invite_view.response == "insufficient_funds":
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Blackjack Failed",
                    description=f"{opponent.mention} doesn't have enough Medals to accept the bet....(jerk)",
                    color=discord.Color.red()
                )
            )
            
        elif invite_view.response == "declined":
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Blackjack Declined",
                    description=f"{opponent.mention} has declined {interaction.user.mention}'s blackjack game :<",
                    color=discord.Color.red()
                )
            )
            
        elif invite_view.response == "timeout" or invite_view.response is None:
            try:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Blackjack Request Timed Out",
                        description=f"{opponent.mention} did not respond to the blackjack challenge in time.",
                        color=discord.Color.red()
                    )
                )
            except Exception as e:
                debug.log(f"Error sending timeout followup: {e}")