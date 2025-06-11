"""
Base handler class for AI automation operations.

This module provides the abstract base class for all AI platform handlers,
defining the common interface and shared functionality for AI operations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from selenium.webdriver.remote.webdriver import WebDriver


class BaseAIHandler(ABC):
    """
    Abstract base class for AI platform handlers.
    
    This class defines the interface that all AI handlers must implement
    and provides common functionality for AI operations.
    """
    
    def __init__(self, driver: WebDriver, logger: logging.Logger):
        """
        Initialize the base AI handler.
        
        Args:
            driver: Selenium WebDriver instance
            logger: Logger instance for logging operations
        """
        self.driver = driver
        self.logger = logger
        self.platform_name = self._get_platform_name()
        self.base_url = self._get_base_url()
        self.is_logged_in = False
        self.current_model = None
        self.available_models = []
        
    @abstractmethod
    def _get_platform_name(self) -> str:
        """
        Get the name of the AI platform.
        
        Returns:
            str: Platform name (e.g., 'ChatGPT', 'Claude', etc.)
        """
        pass
    
    @abstractmethod
    def _get_base_url(self) -> str:
        """
        Get the base URL of the AI platform.
        
        Returns:
            str: Base URL of the platform
        """
        pass
    
    @abstractmethod
    def login(self) -> bool:
        """
        Perform login to the AI platform.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for the AI platform.
        
        Returns:
            List[str]: List of available model names
        """
        pass
    
    @abstractmethod
    def select_model(self, model_name: str) -> bool:
        """
        Select a specific model to use.
        
        Args:
            model_name: Name of the model to select
            
        Returns:
            bool: True if model selection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_settings(self) -> Dict[str, Any]:
        """
        Get available settings for the AI platform.
        
        Returns:
            Dict[str, Any]: Dictionary of available settings and their options
        """
        pass
    
    @abstractmethod
    def configure_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Configure AI platform settings.
        
        Args:
            settings: Dictionary of settings to configure
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        pass
    
    @abstractmethod
    def send_message(self, message: str) -> bool:
        """
        Send a message to the AI platform.
        
        Args:
            message: Text message to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def wait_for_response(self, timeout: int = 60) -> bool:
        """
        Wait for AI response to be generated.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if response received, False if timeout
        """
        pass
    
    @abstractmethod
    def get_response(self) -> Optional[str]:
        """
        Get the AI response text.
        
        Returns:
            Optional[str]: Response text or None if no response
        """
        pass
    
    @abstractmethod
    def start_new_conversation(self) -> bool:
        """
        Start a new conversation/chat session.
        
        Returns:
            bool: True if new conversation started successfully, False otherwise
        """
        pass
    
    def process_text(self, text: str, timeout: int = 60) -> Optional[str]:
        """
        Process text through the AI platform (complete workflow).
        
        Args:
            text: Text to process
            timeout: Maximum time to wait for response
            
        Returns:
            Optional[str]: AI response or None if failed
        """
        try:
            self.logger.info(f"Processing text on {self.platform_name}: {text[:100]}...")
            
            # Send message
            if not self.send_message(text):
                self.logger.error(f"Failed to send message to {self.platform_name}")
                return None
            
            # Wait for response
            if not self.wait_for_response(timeout):
                self.logger.error(f"Timeout waiting for response from {self.platform_name}")
                return None
            
            # Get response
            response = self.get_response()
            if response:
                self.logger.info(f"Successfully received response from {self.platform_name}")
                return response
            else:
                self.logger.error(f"Failed to get response from {self.platform_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing text on {self.platform_name}: {str(e)}")
            return None
    
    def navigate_to_platform(self) -> bool:
        """
        Navigate to the AI platform's main page.
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            self.logger.info(f"Navigating to {self.platform_name} at {self.base_url}")
            self.driver.get(self.base_url)
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to {self.platform_name}: {str(e)}")
            return False
    
    def is_page_loaded(self, timeout: int = 10) -> bool:
        """
        Check if the platform page is loaded.
        
        Args:
            timeout: Maximum time to wait for page load
            
        Returns:
            bool: True if page is loaded, False otherwise
        """
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return True
        except Exception as e:
            self.logger.error(f"Page load check failed for {self.platform_name}: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the AI handler.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            "platform": self.platform_name,
            "base_url": self.base_url,
            "is_logged_in": self.is_logged_in,
            "current_model": self.current_model,
            "available_models": self.available_models
        }