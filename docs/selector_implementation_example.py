#!/usr/bin/env python3
"""
AI Service Selector Implementation Example

This file demonstrates how to implement the selector patterns from the guide
in a practical automation handler using Playwright.
"""

import asyncio
from typing import List, Dict, Optional, Any
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError


class AIServiceSelectors:
    """AI service selector definitions"""
    
    CLAUDE_AI = {
        "login_indicators": [
            'button:has-text("Sign in")',
            'a:has-text("Login")',
            '[data-testid*="login"]',
            '.login-button',
            '[href*="login"]'
        ],
        "logged_in_indicators": [
            '[data-testid*="user"]',
            '[data-testid*="avatar"]',
            '.user-menu',
            '[aria-label*="user menu"]',
            '.profile-button'
        ],
        "text_input": [
            'textarea[placeholder*="message"]',
            'textarea[placeholder*="Message Claude"]',
            'textarea[data-testid*="chat-input"]',
            'textarea[aria-label*="message"]',
            '[contenteditable="true"][data-testid*="input"]',
            '.ProseMirror',
            '[role="textbox"]'
        ],
        "submit_button": [
            'button[data-testid*="send"]',
            'button[aria-label*="Send message"]',
            'button:has(svg[data-icon*="send"])',
            'button:has(svg[data-icon*="arrow-up"])',
            '.send-button',
            '[data-testid*="submit"]'
        ],
        "response_area": [
            '[data-testid*="message"]',
            '[data-testid*="conversation"]',
            '.message-content',
            '[role="log"]',
            '.chat-messages',
            '[data-message-author-role*="assistant"]'
        ],
        "model_selector": [
            'button[data-testid*="model"]',
            '[aria-label*="model"]',
            '.model-selector',
            '[data-testid*="dropdown"]',
            'select[name*="model"]'
        ]
    }
    
    CHATGPT = {
        "login_indicators": [
            'button:has-text("Log in")',
            'a[href*="auth/login"]',
            '.login-button'
        ],
        "logged_in_indicators": [
            '[data-testid*="user-menu"]',
            '.user-avatar',
            '[aria-label*="user menu"]'
        ],
        "text_input": [
            'textarea[placeholder*="Message ChatGPT"]',
            'textarea[data-testid*="prompt-textarea"]',
            '#prompt-textarea',
            'textarea[rows]',
            '[contenteditable="true"]',
            'div[role="textbox"]'
        ],
        "submit_button": [
            'button[data-testid*="send-button"]',
            'button[aria-label*="Send message"]',
            'button:has(svg[data-testid*="send-icon"])',
            '[data-testid*="fruitjuice-send-button"]'
        ],
        "response_area": [
            '[data-message-author-role="assistant"]',
            '.markdown',
            '[data-testid*="conversation-turn"]',
            '.message-content'
        ]
    }
    
    GEMINI = {
        "text_input": [
            'textarea[aria-label*="Enter a prompt"]',
            'textarea[data-testid*="input"]',
            '.ql-editor',
            '[contenteditable="true"]',
            'rich-textarea textarea'
        ],
        "submit_button": [
            'button[aria-label*="Submit"]',
            'button[data-testid*="send"]',
            'button:has(svg[aria-label*="Send"])',
            '.send-button'
        ],
        "response_area": [
            '[data-testid*="response"]',
            '.response-content',
            '[role="main"] .message'
        ]
    }


class SelectorHelper:
    """Helper class for working with selectors"""
    
    def __init__(self, page: Page):
        self.page = page
        
    async def find_element(self, selectors: List[str], timeout: int = 5000) -> Optional[Locator]:
        """
        Try multiple selectors until one is found
        
        Args:
            selectors: List of CSS selectors to try
            timeout: Timeout per selector in milliseconds
            
        Returns:
            Locator if found, None otherwise
        """
        for selector in selectors:
            try:
                element = self.page.locator(selector)
                await element.wait_for(timeout=timeout)
                if await element.is_visible():
                    return element
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                print(f"Error with selector '{selector}': {e}")
                continue
        
        return None
    
    async def find_by_text(self, text: str, tag: str = "*", exact: bool = False) -> Optional[Locator]:
        """
        Find element by text content
        
        Args:
            text: Text to search for
            tag: HTML tag to search within (default: any tag)
            exact: Whether to match text exactly
            
        Returns:
            Locator if found, None otherwise
        """
        try:
            if exact:
                selector = f'{tag}:has-text("{text}")'
            else:
                selector = f'{tag}:text-matches("{text}", "i")'
            
            element = self.page.locator(selector).first()
            await element.wait_for(timeout=3000)
            return element if await element.is_visible() else None
            
        except PlaywrightTimeoutError:
            return None
    
    async def wait_for_response_complete(self, response_selectors: List[str], timeout: int = 30000) -> bool:
        """
        Wait for AI response to complete (streaming finished)
        
        Args:
            response_selectors: Selectors for response area
            timeout: Maximum wait time in milliseconds
            
        Returns:
            True if response completed, False if timeout
        """
        # First, find the response area
        response_area = await self.find_element(response_selectors)
        if not response_area:
            return False
        
        # Wait for streaming to complete - look for various completion indicators
        try:
            # Method 1: Wait for cursor to stop blinking (common pattern)
            await self.page.wait_for_function("""
                () => {
                    // Check for streaming indicators
                    const streamingElements = document.querySelectorAll(
                        '[aria-busy="true"], .streaming, .typing-indicator, .cursor-blink'
                    );
                    return streamingElements.length === 0;
                }
            """, timeout=timeout)
            
            return True
            
        except PlaywrightTimeoutError:
            return False
    
    async def get_response_text(self, response_selectors: List[str]) -> Optional[str]:
        """
        Get the latest response text
        
        Args:
            response_selectors: Selectors for response area
            
        Returns:
            Response text if found, None otherwise
        """
        response_area = await self.find_element(response_selectors)
        if not response_area:
            return None
        
        try:
            # Get all message elements and return the last one
            messages = response_area.locator('[data-message-author-role="assistant"]').last()
            if await messages.count() > 0:
                return await messages.text_content()
            
            # Fallback: get all text content
            return await response_area.text_content()
            
        except Exception as e:
            print(f"Error getting response text: {e}")
            return None


class AIServiceAutomator:
    """Example automation handler using the selector patterns"""
    
    def __init__(self, page: Page, service_name: str):
        self.page = page
        self.service_name = service_name.upper()
        self.helper = SelectorHelper(page)
        self.selectors = getattr(AIServiceSelectors, self.service_name, {})
        
    async def check_login_status(self) -> bool:
        """
        Check if user is logged in
        
        Returns:
            True if logged in, False otherwise
        """
        # Check for logged-in indicators first
        logged_in_selectors = self.selectors.get("logged_in_indicators", [])
        if logged_in_selectors:
            logged_in_element = await self.helper.find_element(logged_in_selectors, timeout=2000)
            if logged_in_element:
                return True
        
        # Check for login required indicators
        login_selectors = self.selectors.get("login_indicators", [])
        if login_selectors:
            login_element = await self.helper.find_element(login_selectors, timeout=2000)
            if login_element:
                return False
        
        # If neither found, assume logged in
        return True
    
    async def send_message(self, message: str) -> bool:
        """
        Send a message to the AI service
        
        Args:
            message: Message to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            # Find text input area
            text_input_selectors = self.selectors.get("text_input", [])
            if not text_input_selectors:
                raise ValueError(f"No text input selectors defined for {self.service_name}")
            
            text_input = await self.helper.find_element(text_input_selectors)
            if not text_input:
                print("Could not find text input area")
                return False
            
            # Clear and enter message
            await text_input.clear()
            await text_input.fill(message)
            
            # Find and click submit button
            submit_selectors = self.selectors.get("submit_button", [])
            if not submit_selectors:
                # Fallback: try Enter key
                await text_input.press("Enter")
                return True
            
            submit_button = await self.helper.find_element(submit_selectors)
            if submit_button:
                await submit_button.click()
                return True
            else:
                # Fallback: try Enter key
                await text_input.press("Enter")
                return True
                
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    async def wait_for_response(self, timeout: int = 30000) -> Optional[str]:
        """
        Wait for and retrieve the AI response
        
        Args:
            timeout: Maximum wait time in milliseconds
            
        Returns:
            Response text if successful, None otherwise
        """
        response_selectors = self.selectors.get("response_area", [])
        if not response_selectors:
            print(f"No response selectors defined for {self.service_name}")
            return None
        
        # Wait for response to complete
        completed = await self.helper.wait_for_response_complete(response_selectors, timeout)
        if not completed:
            print("Response did not complete within timeout")
            return None
        
        # Get response text
        response_text = await self.helper.get_response_text(response_selectors)
        return response_text
    
    async def select_model(self, model_name: str) -> bool:
        """
        Select a specific model if available
        
        Args:
            model_name: Name of the model to select
            
        Returns:
            True if model selected successfully, False otherwise
        """
        model_selectors = self.selectors.get("model_selector", [])
        if not model_selectors:
            print(f"No model selectors defined for {self.service_name}")
            return False
        
        try:
            # Find model selector button
            model_button = await self.helper.find_element(model_selectors)
            if not model_button:
                print("Could not find model selector")
                return False
            
            await model_button.click()
            
            # Wait for dropdown/menu to appear
            await self.page.wait_for_selector('[role="listbox"], [role="menu"], [role="combobox"]', timeout=5000)
            
            # Look for the specific model
            model_option = await self.helper.find_by_text(model_name, "button")
            if not model_option:
                model_option = await self.helper.find_by_text(model_name, "*")
            
            if model_option:
                await model_option.click()
                return True
            else:
                print(f"Could not find model option: {model_name}")
                return False
                
        except Exception as e:
            print(f"Error selecting model: {e}")
            return False


# Example usage
async def example_usage():
    """Example of how to use the automation classes"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Example with Claude.ai
        await page.goto("https://claude.ai")
        
        automator = AIServiceAutomator(page, "CLAUDE_AI")
        
        # Check login status
        is_logged_in = await automator.check_login_status()
        print(f"Logged in: {is_logged_in}")
        
        if is_logged_in:
            # Send a message
            success = await automator.send_message("Hello, how are you?")
            if success:
                print("Message sent successfully")
                
                # Wait for response
                response = await automator.wait_for_response()
                if response:
                    print(f"Response: {response}")
                else:
                    print("No response received")
            else:
                print("Failed to send message")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(example_usage())