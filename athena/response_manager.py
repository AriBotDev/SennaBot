"""
Response management system for SennaBot.
Handles themed responses for various commands and events.
"""
import os
import json
import random
from .debug_tools import DebugTools
from .data_service import DataService

# Setup debugger
debug = DebugTools.get_debugger("response_manager")

class ResponseManager:
    """
    Manages themed responses for bot interactions.
    Handles loading, selecting, and formatting response messages.
    """
    
    # Constants
    RESPONSES_DIR = os.path.join("data", "responses")
    
    # Response categories
    CATEGORIES = ["work", "crime", "death", "injury", "prison", "rob"]
    
    # Default responses for when category files don't exist yet
    DEFAULT_RESPONSES = {
        "work": {
            "work": ["You worked hard and earned **{amount}** Medals."],
            "work_rare_success": ["You hit the jackpot and earned **{amount}** Medals instead of your usual **{original}** Medals!"]
        },
        "crime": {
            "crime_success": ["Your crime was successful! You stole **{amount}** Medals."],
            "crime_rare_success": ["A perfect heist! You earned **{amount}** Medals instead of the expected **{original}** Medals!"]
        },
        "death": {
            "death": ["You died and lost **{amount}** Medals."]
        },
        "injury": {
            "injury": ["You were injured and lost **{amount}** Medals for medical treatment."]
        },
        "prison": {
            "prison": ["You were caught and sent to prison!"],
            "escape_success": ["You successfully escaped from prison."],
            "escape_failure": ["Your escape attempt failed."]
        },
        "rob": {
            "rob_success": ["You successfully robbed {target} and got **{amount}** Medals."],
            "rob_injury": ["You failed to rob {target} and were injured, losing **{amount}** Medals."],
            "rob_death": ["You died trying to rob {target} and lost **{amount}** Medals."]
        }
    }
    
    # Cache
    _responses_cache = {}
    
    @classmethod
    def initialize(cls):
        """Initialize the response system."""
        debug.log("Initializing ResponseManager")
        
        # Ensure responses directory exists
        os.makedirs(cls.RESPONSES_DIR, exist_ok=True)
        
        # Create default response files if they don't exist
        for category, responses in cls.DEFAULT_RESPONSES.items():
            file_path = os.path.join(cls.RESPONSES_DIR, f"{category}_responses.json")
            if not os.path.exists(file_path):
                debug.log(f"Creating default {category} responses file")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(responses, f, indent=4)
        
        debug.log("ResponseManager initialization complete")
    
    @classmethod
    def get_response(cls, key, **kwargs):
        """
        Get a formatted response for a specific key.
        Randomly selects from available responses and formats with kwargs.
        """
        debug.log(f"Getting response for key: {key}")
        
        # Determine the category from the key
        category = cls._get_category_from_key(key)
        if not category:
            debug.log(f"No category found for key: {key}")
            return f"No response found for key: {key}"
        
        # Load responses for this category
        responses = cls._load_category(category)
        
        # Get response list for this key
        response_list = responses.get(key)
        if not response_list:
            debug.log(f"No responses found for key: {key}")
            return f"No responses configured for: {key}"
        
        # Select a random response
        response = random.choice(response_list)
        
        # Format response with kwargs
        try:
            formatted = response.format(**kwargs)
            return formatted
        except KeyError as e:
            debug.log(f"Missing format key in response: {e}")
            return response
        except Exception as e:
            debug.log(f"Error formatting response: {e}")
            return response
    
    @classmethod
    def _get_category_from_key(cls, key):
        """Determine which category a response key belongs to."""
        # First try direct match with category
        if key in cls.CATEGORIES:
            return key
            
        # Then try prefix matching
        for category in cls.CATEGORIES:
            if key.startswith(f"{category}_"):
                return category
                
        # Then try to load all categories and check each
        for category in cls.CATEGORIES:
            responses = cls._load_category(category)
            if key in responses:
                return category
                
        return None
    
    @classmethod
    def _load_category(cls, category):
        """Load responses for a specific category with caching."""
        # Return cached responses if available
        if category in cls._responses_cache:
            return cls._responses_cache[category]
            
        # Load from file
        file_path = os.path.join(cls.RESPONSES_DIR, f"{category}_responses.json")
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    responses = json.load(f)
                    cls._responses_cache[category] = responses
                    return responses
        except Exception as e:
            debug.log(f"Error loading responses from {file_path}: {e}")
            
        # Return defaults if file doesn't exist or has an error
        defaults = cls.DEFAULT_RESPONSES.get(category, {})
        cls._responses_cache[category] = defaults
        return defaults
    
    @classmethod
    def add_response(cls, key, response):
        """Add a new response for a specific key."""
        # Determine the category from the key
        category = cls._get_category_from_key(key)
        if not category:
            # Try to guess category from key
            for cat in cls.CATEGORIES:
                if cat in key:
                    category = cat
                    break
                    
            # If still no category, use the first part of the key
            if not category and "_" in key:
                category = key.split("_")[0]
                
            # If still no category, use "custom"
            if not category:
                category = "custom"
        
        # Load current responses
        responses = cls._load_category(category)
        
        # Add the new response
        if key not in responses:
            responses[key] = []
        responses[key].append(response)
        
        # Save back to file
        file_path = os.path.join(cls.RESPONSES_DIR, f"{category}_responses.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(responses, f, indent=4)
                
            # Update cache
            cls._responses_cache[category] = responses
            debug.log(f"Added new response for key: {key}")
            return True
        except Exception as e:
            debug.log(f"Error saving response: {e}")
            return False