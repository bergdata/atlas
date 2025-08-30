import requests
import json
import os
import logging
import sys
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config to get environment variables
import config

# Set up logging with console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get bot token and chat ID from config after ensuring .env is loaded
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
STORED_CHAT_ID = config.TELEGRAM_CHAT_ID

# Telegram API base URL
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

class TelegramNotifier:
    """A class to handle Telegram notifications for sending messages to phone."""
    
    def __init__(self, chat_id: Optional[str] = None):
        """
        Initialize the Telegram notifier.
        
        Args:
            chat_id (str, optional): The chat ID to send messages to. 
                                   If None, will attempt to auto-detect.
        """
        # Use provided chat_id, then stored chat_id, then try to get from API
        self.chat_id = chat_id or STORED_CHAT_ID
        if not BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    def get_chat_id(self) -> Optional[str]:
        """Retrieve the chat ID by fetching recent updates and save it to config."""
        try:
            response = requests.get(f"{BASE_URL}/getUpdates")
            response.raise_for_status()
            updates = response.json()
            
            if updates["ok"] and updates["result"]:
                for update in updates["result"]:
                    if "message" in update and "chat" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        chat_type = update["message"]["chat"]["type"]
                        logger.info(f"Found chat ID: {chat_id} (Type: {chat_type})")
                        self.chat_id = str(chat_id)
                        
                        # Save the chat ID to config file for future use
                        self._save_chat_id_to_config(str(chat_id))
                        
                        return self.chat_id
                        
            logger.info("No chat ID found. Send a message to your bot or add it to a group/channel, then try again.")
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching chat ID: {e}")
            return None
    
    def _save_chat_id_to_config(self, chat_id: str):
        """Save the chat ID to the config file for persistent storage."""
        try:
            config_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.py")
            
            # Read the current config file
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Check if TELEGRAM_CHAT_ID already exists
            if 'TELEGRAM_CHAT_ID = os.getenv(\'TELEGRAM_CHAT_ID\')' in config_content:
                # Replace the existing line with the new value
                config_content = config_content.replace(
                    'TELEGRAM_CHAT_ID = os.getenv(\'TELEGRAM_CHAT_ID\')',
                    f'TELEGRAM_CHAT_ID = os.getenv(\'TELEGRAM_CHAT_ID\', \'{chat_id}\')'
                )
            else:
                # Add the line after TELEGRAM_BOT_TOKEN
                config_content = config_content.replace(
                    'TELEGRAM_BOT_TOKEN = os.getenv(\'TELEGRAM_BOT_TOKEN\')',
                    f'TELEGRAM_BOT_TOKEN = os.getenv(\'TELEGRAM_BOT_TOKEN\')\nTELEGRAM_CHAT_ID = os.getenv(\'TELEGRAM_CHAT_ID\', \'{chat_id}\')'
                )
            
            # Write the updated config back
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            logger.info(f"Chat ID {chat_id} saved to config.py for future use")
            
        except Exception as e:
            logger.warning(f"Could not save chat ID to config file: {e}")
            logger.info(f"Please manually add TELEGRAM_CHAT_ID = '{chat_id}' to your .env file")

    def set_chat_id(self, chat_id: str) -> bool:
        """
        Manually set the chat ID and save it to config.
        
        Args:
            chat_id (str): The chat ID to set
            
        Returns:
            bool: True if successfully set and saved, False otherwise
        """
        try:
            # Validate the chat ID by trying to send a test message
            self.chat_id = str(chat_id)
            
            # Try to send a test message to verify the chat ID
            test_message = "Chat ID verification message"
            if self.send_message(test_message):
                logger.info(f"Chat ID {chat_id} verified and working!")
                # Save to config for future use
                self._save_chat_id_to_config(str(chat_id))
                return True
            else:
                logger.error(f"Failed to verify chat ID {chat_id}")
                self.chat_id = None
                return False
                
        except Exception as e:
            logger.error(f"Error setting chat ID: {e}")
            self.chat_id = None
            return False

    def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """
        Send a message to the specified chat ID.
        
        Args:
            text (str): The message text to send
            chat_id (str, optional): Override the default chat ID
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        target_chat_id = chat_id or self.chat_id
        
        if not target_chat_id:
            logger.warning("No chat ID available. Please set one or call get_chat_id() first.")
            return False
            
        try:
            url = f"{BASE_URL}/sendMessage"
            payload = {
                "chat_id": target_chat_id,
                "text": text
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent successfully to chat {target_chat_id}!")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_print_to_phone(self, message: str, chat_id: Optional[str] = None) -> bool:
        """
        Send a print statement to your phone via Telegram.
        
        Args:
            message (str): The message to send (equivalent to a print statement)
            chat_id (str, optional): Override the default chat ID
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        return self.send_message(message, chat_id)

def send_to_phone(message: str, chat_id: Optional[str] = None) -> bool:
    """
    Convenience function to quickly send a message to your phone.
    
    Args:
        message (str): The message to send
        chat_id (str, optional): The chat ID to send to
        
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    # Use provided chat_id or stored chat_id first
    target_chat_id = chat_id or STORED_CHAT_ID
    
    if target_chat_id:
        # If we have a chat ID, use it directly
        notifier = TelegramNotifier(target_chat_id)
        return notifier.send_print_to_phone(message)
    else:
        # Only create instance and get chat ID if we don't have one stored
        notifier = TelegramNotifier()
        if not notifier.chat_id:
            notifier.get_chat_id()
        return notifier.send_print_to_phone(message)

def setup_telegram_notifier(chat_id: Optional[str] = None) -> TelegramNotifier:
    """
    Set up a Telegram notifier instance.
    
    Args:
        chat_id (str, optional): The chat ID to use
        
    Returns:
        TelegramNotifier: Configured notifier instance
    """
    # Use provided chat_id or stored chat_id first
    target_chat_id = chat_id or STORED_CHAT_ID
    
    notifier = TelegramNotifier(target_chat_id)
    if not notifier.chat_id:
        notifier.get_chat_id()
    return notifier

def set_telegram_chat_id(chat_id: str) -> bool:
    """
    Manually set and save the Telegram chat ID.
    
    Args:
        chat_id (str): The chat ID to set
        
    Returns:
        bool: True if successfully set and saved, False otherwise
    """
    try:
        notifier = TelegramNotifier()
        return notifier.set_chat_id(chat_id)
    except Exception as e:
        logger.error(f"Error setting chat ID: {e}")
        return False

def setup_telegram() -> bool:
    """
    Set up Telegram bot chat ID and save it for future use.
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    # Check if bot token is set
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env file!")
        logger.error("Please add your Telegram bot token to the .env file:")
        logger.error("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return False
    
    logger.info("Setting up Telegram bot...")
    logger.info("Please send a message to your bot now...")
    logger.info("(You can send any message like 'Hello' or 'Test')")
    
    # Create notifier and get chat ID
    notifier = TelegramNotifier()
    
    # Try to get chat ID
    chat_id = notifier.get_chat_id()
    
    if chat_id:
        logger.info(f"Successfully retrieved chat ID: {chat_id}")
        
        # Test sending a message
        logger.info("Testing message delivery...")
        test_message = "Telegram bot setup successful! This message confirms everything is working."
        
        if notifier.send_message(test_message):
            logger.info("Test message sent successfully!")
            logger.info("Chat ID has been saved to config.py for future use")
            logger.info("You can now run your main scripts without this setup step")
            return True
        else:
            logger.error("Failed to send test message")
            return False
    else:
        logger.error("Failed to retrieve chat ID")
        logger.error("Please ensure:")
        logger.error("1. Your bot token is correct")
        logger.error("2. You have sent a message to your bot")
        logger.error("3. Your bot is not blocked")
        return False

def debug_telegram() -> bool:
    """
    Debug Telegram bot connection and API calls.
    
    Returns:
        bool: True if debug successful, False otherwise
    """
    logger.info("Telegram Bot Debug Script")
    logger.info("=" * 40)
    
    # Check bot token
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env file!")
        logger.error("Please add your bot token to the .env file")
        return False
    
    logger.info(f"Bot token found: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
    
    # Test bot info
    logger.info("\nTesting bot connection...")
    bot_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(bot_info_url, timeout=10)
        if response.status_code == 200:
            bot_data = response.json()
            if bot_data.get("ok"):
                bot_info = bot_data["result"]
                logger.info("Bot connection successful!")
                logger.info(f"   Bot name: {bot_info.get('first_name', 'Unknown')}")
                logger.info(f"   Username: @{bot_info.get('username', 'Unknown')}")
                logger.info(f"   Bot ID: {bot_info.get('id', 'Unknown')}")
            else:
                logger.error(f"Bot API error: {bot_data.get('description', 'Unknown error')}")
                return False
        else:
            logger.error(f"HTTP error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False
    
    # Test getUpdates
    logger.info("\nTesting getUpdates API...")
    updates_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(updates_url, timeout=10)
        if response.status_code == 200:
            updates_data = response.json()
            if updates_data.get("ok"):
                updates = updates_data.get("result", [])
                logger.info("getUpdates successful!")
                logger.info(f"   Number of updates: {len(updates)}")
                
                if updates:
                    logger.info("\nRecent updates:")
                    for i, update in enumerate(updates[-3:], 1):  # Show last 3 updates
                        if "message" in update:
                            message = update["message"]
                            chat = message.get("chat", {})
                            logger.info(f"   {i}. Chat ID: {chat.get('id')} | Type: {chat.get('type')} | From: {message.get('from', {}).get('first_name', 'Unknown')}")
                        elif "edited_message" in update:
                            logger.info(f"   {i}. Edited message")
                        else:
                            logger.info(f"   {i}. Other update type: {list(update.keys())}")
                else:
                    logger.info("   No recent updates found")
                    logger.info("\nTo get a chat ID:")
                    logger.info("   1. Open Telegram")
                    logger.info("   2. Search for your bot: @{bot_info.get('username', 'Unknown')}")
                    logger.info("   3. Send any message (like 'Hello' or 'Test')")
                    logger.info("   4. Run this debug script again")
            else:
                logger.error(f"getUpdates API error: {updates_data.get('description', 'Unknown error')}")
                return False
        else:
            logger.error(f"HTTP error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"getUpdates error: {e}")
        return False
    
    # Test webhook info
    logger.info("\nChecking webhook status...")
    webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(webhook_url, timeout=10)
        if response.status_code == 200:
            webhook_data = response.json()
            if webhook_data.get("ok"):
                webhook_info = webhook_data["result"]
                if webhook_info.get("url"):
                    logger.warning(f"Webhook is set to: {webhook_info['url']}")
                    logger.info("   This might interfere with getUpdates. Consider removing webhook:")
                    logger.info(f"   https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
                else:
                    logger.info("No webhook set (good for getUpdates)")
            else:
                logger.error(f"Webhook API error: {webhook_data.get('description', 'Unknown error')}")
        else:
            logger.error(f"Webhook HTTP error: {response.status_code}")
    except Exception as e:
        logger.error(f"Webhook check error: {e}")
    
    logger.info("\n" + "=" * 40)
    logger.info("Debug complete!")
    
    return True

def quick_set_chat_id(chat_id: str) -> bool:
    """
    Quick function to set chat ID from command line.
    
    Args:
        chat_id (str): The chat ID to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Setting Telegram chat ID to: {chat_id}")
    logger.info("Sending verification message...")
    
    try:
        success = set_telegram_chat_id(chat_id)
        
        if success:
            logger.info("Chat ID set successfully!")
            logger.info("It has been saved to config.py for future use")
            logger.info("You can now run your main scripts without setup")
        else:
            logger.error("Failed to set chat ID")
            logger.error("Please check:")
            logger.error("   - The chat ID is correct")
            logger.error("   - Your bot token is valid")
            logger.error("   - You have permission to send messages")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Check command line arguments for different modes
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            # Setup mode
            logger.info("Starting Telegram bot setup...")
            try:
                success = setup_telegram()
                if success:
                    logger.info("Setup completed successfully!")
                    logger.info("You can now run your main scripts and they will use the saved chat ID")
                else:
                    logger.error("Setup failed. Please check the errors above and try again.")
                    sys.exit(1)
            except KeyboardInterrupt:
                logger.info("\nSetup cancelled by user")
                sys.exit(0)
            except Exception as e:
                logger.error(f"Unexpected error during setup: {e}")
                sys.exit(1)
                
        elif command == "debug":
            # Debug mode
            try:
                success = debug_telegram()
                if not success:
                    sys.exit(1)
            except KeyboardInterrupt:
                logger.info("\nDebug cancelled by user")
                sys.exit(0)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                sys.exit(1)
                
        elif command == "set":
            # Set chat ID mode
            if len(sys.argv) != 3:
                logger.error("Usage: python telegram_notifier.py set <chat_id>")
                logger.error("Example: python telegram_notifier.py set 123456789")
                sys.exit(1)
            
            chat_id = sys.argv[2]
            success = quick_set_chat_id(chat_id)
            if not success:
                sys.exit(1)
                
        else:
            logger.error("Usage:")
            logger.error("  python telegram_notifier.py setup    - Set up Telegram bot")
            logger.error("  python telegram_notifier.py debug    - Debug Telegram connection")
            logger.error("  python telegram_notifier.py set <id> - Set chat ID manually")
            logger.error("  python telegram_notifier.py          - Run example usage")
            sys.exit(1)
    else:
        # Example usage (default mode)
        try:
            # Create notifier instance
            notifier = setup_telegram_notifier()
            
            if notifier.chat_id:
                # Send a test message
                notifier.send_print_to_phone("Test message from Atlas EC2! to retrieve the chat ID")
            else:
                logger.error("Failed to retrieve a valid CHAT_ID. Please ensure:")
                logger.error("1. TELEGRAM_BOT_TOKEN environment variable is set")
                logger.error("2. A message has been sent to the bot")
                logger.error("3. The bot token is correct")
                logger.info("\nTry running: python telegram_notifier.py setup")
                
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
