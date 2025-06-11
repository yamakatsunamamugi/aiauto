"""
ChatGPT handler for AI automation operations.

This module provides the handler for automating ChatGPT interactions,
including login, message sending, and response retrieval.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_handler import BaseAIHandler


class ChatGPTHandler(BaseAIHandler):
    """
    Handler for ChatGPT AI platform automation.
    
    This class implements ChatGPT-specific automation including
    login, model selection, settings configuration, and message processing.
    """
    
    def _get_platform_name(self) -> str:
        """Get the platform name."""
        return "ChatGPT"
    
    def _get_base_url(self) -> str:
        """Get the base URL."""
        return "https://chat.openai.com"
    
    def login(self) -> bool:
        """
        Perform login to ChatGPT.
        
        This method assumes the user is already logged in via Chrome browser.
        It will check if login is required and handle it if necessary.
        
        Returns:
            bool: True if login successful or already logged in, False otherwise
        """
        try:
            self.logger.info("Checking ChatGPT login status...")
            
            # Navigate to ChatGPT
            if not self.navigate_to_platform():
                return False
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we're already logged in by looking for chat interface
            try:
                wait = WebDriverWait(self.driver, 10)
                # Look for the main chat container or new chat button
                wait.until(EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='send-button']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='Message']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".text-token-text-primary")),
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'New chat')]"))
                ))
                
                self.logger.info("ChatGPT login successful - already logged in")
                self.is_logged_in = True
                return True
                
            except TimeoutException:
                # Check if we're on login page
                try:
                    login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
                    self.logger.warning("ChatGPT requires login - please log in manually")
                    self.logger.info("Please log in to ChatGPT manually and then retry the automation")
                    return False
                except NoSuchElementException:
                    # Maybe we're on a different page, try to find other indicators
                    self.logger.warning("ChatGPT page loaded but login status unclear")
                    return False
                    
        except Exception as e:
            self.logger.error(f"ChatGPT login failed: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for ChatGPT.
        
        Returns:
            List[str]: List of available model names
        """
        try:
            self.logger.info("Getting available ChatGPT models...")
            
            models = []
            
            # Look for model selector button (usually shows current model)
            try:
                # Try different selectors for model dropdown
                model_selectors = [
                    "button[data-testid='model-switcher']",
                    "button[class*='model']",
                    ".model-selector",
                    "button:has(span:contains('GPT'))",
                    "[role='button']:has-text('GPT')"
                ]
                
                model_button = None
                for selector in model_selectors:
                    try:
                        model_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                if model_button:
                    # Click to open dropdown
                    self.driver.execute_script("arguments[0].click();", model_button)
                    time.sleep(1)
                    
                    # Look for model options
                    model_options = self.driver.find_elements(By.CSS_SELECTOR, 
                                                            "[role='option'], .model-option, li:contains('GPT')")
                    
                    for option in model_options:
                        text = option.text.strip()
                        if text and 'GPT' in text:
                            models.append(text)
                    
                    # Close dropdown by clicking elsewhere
                    self.driver.execute_script("arguments[0].click();", model_button)
                
            except Exception as e:
                self.logger.warning(f"Could not detect model selector: {str(e)}")
            
            # If no models found, provide default ones
            if not models:
                models = ["GPT-4", "GPT-4 Turbo", "GPT-3.5"]
                self.logger.info("Using default model list")
            
            self.available_models = models
            self.logger.info(f"Available models: {models}")
            return models
            
        except Exception as e:
            self.logger.error(f"Failed to get ChatGPT models: {str(e)}")
            return ["GPT-4", "GPT-3.5"]  # Fallback
    
    def select_model(self, model_name: str) -> bool:
        """
        Select a specific model to use.
        
        Args:
            model_name: Name of the model to select
            
        Returns:
            bool: True if model selection successful, False otherwise
        """
        try:
            self.logger.info(f"Selecting ChatGPT model: {model_name}")
            
            # Look for model selector button
            model_selectors = [
                "button[data-testid='model-switcher']",
                "button[class*='model']",
                ".model-selector"
            ]
            
            model_button = None
            for selector in model_selectors:
                try:
                    model_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not model_button:
                self.logger.warning("Model selector not found, using current model")
                self.current_model = model_name  # Assume it's set
                return True
            
            # Click to open dropdown
            self.driver.execute_script("arguments[0].click();", model_button)
            time.sleep(1)
            
            # Look for the specific model option
            try:
                model_option = self.driver.find_element(
                    By.XPATH, f"//div[@role='option' and contains(text(), '{model_name}')]"
                )
                self.driver.execute_script("arguments[0].click();", model_option)
                time.sleep(1)
                
                self.current_model = model_name
                self.logger.info(f"Successfully selected model: {model_name}")
                return True
                
            except NoSuchElementException:
                self.logger.warning(f"Model '{model_name}' not found in dropdown")
                # Close dropdown
                self.driver.execute_script("arguments[0].click();", model_button)
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to select ChatGPT model: {str(e)}")
            return False
    
    def get_available_settings(self) -> Dict[str, Any]:
        """
        Get available settings for ChatGPT.
        
        Returns:
            Dict[str, Any]: Dictionary of available settings and their options
        """
        settings = {
            "model": {
                "type": "select",
                "options": self.get_available_models(),
                "default": "GPT-4"
            },
            "temperature": {
                "type": "slider",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
                "description": "Controls randomness in responses"
            },
            "conversation_mode": {
                "type": "select",
                "options": ["New conversation", "Continue conversation"],
                "default": "New conversation"
            }
        }
        
        return settings
    
    def configure_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Configure ChatGPT settings.
        
        Args:
            settings: Dictionary of settings to configure
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        try:
            self.logger.info(f"Configuring ChatGPT settings: {settings}")
            
            success = True
            
            # Handle model selection
            if "model" in settings:
                if not self.select_model(settings["model"]):
                    success = False
            
            # Handle new conversation
            if settings.get("conversation_mode") == "New conversation":
                if not self.start_new_conversation():
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to configure ChatGPT settings: {str(e)}")
            return False
    
    def send_message(self, message: str) -> bool:
        """
        Send a message to ChatGPT.
        
        Args:
            message: Text message to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            self.logger.info(f"Sending message to ChatGPT: {message[:100]}...")
            
            # Look for the input textarea
            input_selectors = [
                "textarea[placeholder*='Message']",
                "textarea[data-testid='prompt-textarea']",
                "textarea#prompt-textarea",
                ".ProseMirror",
                "[contenteditable='true']"
            ]
            
            textarea = None
            for selector in input_selectors:
                try:
                    wait = WebDriverWait(self.driver, 5)
                    textarea = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not textarea:
                self.logger.error("Could not find ChatGPT input textarea")
                return False
            
            # Clear existing text and enter new message
            textarea.clear()
            textarea.send_keys(message)
            time.sleep(0.5)
            
            # Look for send button
            send_selectors = [
                "[data-testid='send-button']",
                "button[aria-label*='Send']",
                "button:has(svg)",
                ".send-button"
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if send_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if send_button and send_button.is_enabled():
                # Click send button
                self.driver.execute_script("arguments[0].click();", send_button)
                self.logger.info("Message sent successfully")
                return True
            else:
                # Try Enter key as fallback
                textarea.send_keys(Keys.RETURN)
                self.logger.info("Message sent using Enter key")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to send message to ChatGPT: {str(e)}")
            return False
    
    def wait_for_response(self, timeout: int = 60) -> bool:
        """
        Wait for ChatGPT response to be generated.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if response received, False if timeout
        """
        try:
            self.logger.info(f"Waiting for ChatGPT response (timeout: {timeout}s)...")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Check if ChatGPT is still generating (look for stop button or loading indicators)
                    stop_indicators = [
                        "[data-testid='stop-button']",
                        "button:contains('Stop generating')",
                        ".result-streaming",
                        "[aria-label*='Stop']"
                    ]
                    
                    is_generating = False
                    for selector in stop_indicators:
                        try:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if element.is_displayed():
                                is_generating = True
                                break
                        except NoSuchElementException:
                            continue
                    
                    if not is_generating:
                        # Check if we have a complete response
                        response_text = self.get_response()
                        if response_text and len(response_text.strip()) > 0:
                            self.logger.info("ChatGPT response received")
                            return True
                    
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.warning(f"Error while waiting for response: {str(e)}")
                    time.sleep(2)
            
            self.logger.warning("Timeout waiting for ChatGPT response")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to wait for ChatGPT response: {str(e)}")
            return False
    
    def get_response(self) -> Optional[str]:
        """
        Get the ChatGPT response text.
        
        Returns:
            Optional[str]: Response text or None if no response
        """
        try:
            # Look for the latest response from ChatGPT
            response_selectors = [
                "[data-message-author-role='assistant'] .markdown",
                "[data-message-author-role='assistant']",
                ".message.assistant",
                ".group\\/conversation-turn:last-child [data-message-author-role='assistant']",
                ".prose"
            ]
            
            for selector in response_selectors:
                try:
                    response_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if response_elements:
                        # Get the last response (most recent)
                        response_element = response_elements[-1]
                        response_text = response_element.text.strip()
                        
                        if response_text:
                            self.logger.info(f"Retrieved ChatGPT response: {response_text[:100]}...")
                            return response_text
                            
                except Exception as e:
                    self.logger.debug(f"Selector '{selector}' failed: {str(e)}")
                    continue
            
            self.logger.warning("Could not retrieve ChatGPT response")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get ChatGPT response: {str(e)}")
            return None
    
    def start_new_conversation(self) -> bool:
        """
        Start a new conversation/chat session.
        
        Returns:
            bool: True if new conversation started successfully, False otherwise
        """
        try:
            self.logger.info("Starting new ChatGPT conversation...")
            
            # Look for new chat button
            new_chat_selectors = [
                "button:contains('New chat')",
                "[data-testid='new-chat-button']",
                "a[href='/']",
                ".new-chat-button"
            ]
            
            for selector in new_chat_selectors:
                try:
                    new_chat_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if new_chat_button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", new_chat_button)
                        time.sleep(2)
                        self.logger.info("New conversation started")
                        return True
                except NoSuchElementException:
                    continue
            
            # Fallback: navigate to base URL
            self.logger.info("New chat button not found, navigating to base URL")
            return self.navigate_to_platform()
            
        except Exception as e:
            self.logger.error(f"Failed to start new ChatGPT conversation: {str(e)}")
            return False