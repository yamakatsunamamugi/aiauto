# AI Service DOM Selector Guide for Automation

This guide provides common CSS selector patterns and strategies for automating interactions with popular AI services. Since these services frequently update their interfaces, this guide focuses on general patterns and backup strategies.

## Overview

### Key Challenges
- **Dynamic Interfaces**: AI services frequently update their UI, breaking static selectors
- **Anti-Bot Protection**: Many services implement measures to detect and block automation
- **Authentication Requirements**: Most services require user login before access
- **Shadow DOM**: Some services use shadow DOM, making traditional selectors ineffective

### Recommended Approach
1. **Multiple Selector Strategy**: Use arrays of potential selectors with fallbacks
2. **Content-Based Selection**: Combine CSS selectors with text matching
3. **Wait Strategies**: Implement proper waiting for dynamic content
4. **Error Handling**: Graceful fallback when elements are not found

## Common Selector Patterns by Service

### 1. Claude.ai (https://claude.ai)

#### Login State Detection
```javascript
// Logged out indicators
const loginIndicators = [
  'button:has-text("Sign in")',
  'a:has-text("Login")',
  '[data-testid*="login"]',
  '.login-button',
  '[href*="login"]'
];

// Logged in indicators  
const loggedInIndicators = [
  '[data-testid*="user"]',
  '[data-testid*="avatar"]',
  '.user-menu',
  '[aria-label*="user menu"]',
  '.profile-button'
];
```

#### Text Input Area
```javascript
const textInputSelectors = [
  'textarea[placeholder*="message"]',
  'textarea[placeholder*="Message Claude"]',
  'textarea[data-testid*="chat-input"]',
  'textarea[aria-label*="message"]',
  '[contenteditable="true"][data-testid*="input"]',
  '.ProseMirror', // Rich text editor
  '[role="textbox"]'
];
```

#### Submit Button
```javascript
const submitSelectors = [
  'button[data-testid*="send"]',
  'button[aria-label*="Send message"]',
  'button:has(svg[data-icon*="send"])',
  'button:has(svg[data-icon*="arrow-up"])',
  '.send-button',
  '[data-testid*="submit"]'
];
```

#### Response Area
```javascript
const responseSelectors = [
  '[data-testid*="message"]',
  '[data-testid*="conversation"]',
  '.message-content',
  '[role="log"]',
  '.chat-messages',
  '[data-message-author-role*="assistant"]'
];
```

#### Model Selection
```javascript
const modelSelectors = [
  'button[data-testid*="model"]',
  '[aria-label*="model"]',
  '.model-selector',
  '[data-testid*="dropdown"]',
  'select[name*="model"]'
];
```

### 2. ChatGPT (https://chat.openai.com)

#### Login State Detection
```javascript
const loginIndicators = [
  'button:has-text("Log in")',
  'a[href*="auth/login"]',
  '.login-button'
];

const loggedInIndicators = [
  '[data-testid*="user-menu"]',
  '.user-avatar',
  '[aria-label*="user menu"]'
];
```

#### Text Input Area
```javascript
const textInputSelectors = [
  'textarea[placeholder*="Message ChatGPT"]',
  'textarea[data-testid*="prompt-textarea"]',
  '#prompt-textarea',
  'textarea[rows]',
  '[contenteditable="true"]',
  'div[role="textbox"]'
];
```

#### Submit Button
```javascript
const submitSelectors = [
  'button[data-testid*="send-button"]',
  'button[aria-label*="Send message"]',
  'button:has(svg[data-testid*="send-icon"])',
  '[data-testid*="fruitjuice-send-button"]' // Historical selector
];
```

#### Response Area
```javascript
const responseSelectors = [
  '[data-message-author-role="assistant"]',
  '.markdown',
  '[data-testid*="conversation-turn"]',
  '.message-content'
];
```

### 3. Google Gemini (https://gemini.google.com)

#### Text Input Area
```javascript
const textInputSelectors = [
  'textarea[aria-label*="Enter a prompt"]',
  'textarea[data-testid*="input"]',
  '.ql-editor', // Quill editor
  '[contenteditable="true"]',
  'rich-textarea textarea'
];
```

#### Submit Button
```javascript
const submitSelectors = [
  'button[aria-label*="Submit"]',
  'button[data-testid*="send"]',
  'button:has(svg[aria-label*="Send"])',
  '.send-button'
];
```

### 4. Google AI Studio (https://aistudio.google.com)

#### Text Input Area
```javascript
const textInputSelectors = [
  'textarea[placeholder*="Enter prompt"]',
  '.cm-editor textarea', // CodeMirror editor
  '[data-testid*="prompt-input"]',
  'textarea[aria-label*="prompt"]'
];
```

### 5. Genspark (https://www.genspark.ai)

#### Text Input Area
```javascript
const textInputSelectors = [
  'textarea[placeholder*="Ask me anything"]',
  'input[type="text"][placeholder*="search"]',
  '[data-testid*="search-input"]',
  'textarea[name*="query"]'
];
```

## General Automation Strategies

### 1. Multi-Selector Approach
```javascript
async function findElement(page, selectors) {
  for (const selector of selectors) {
    try {
      const element = await page.waitForSelector(selector, { timeout: 2000 });
      if (element) return element;
    } catch (error) {
      continue;
    }
  }
  throw new Error('No element found with any of the provided selectors');
}
```

### 2. Text-Based Fallback
```javascript
async function findByText(page, text, tagName = '*') {
  return await page.locator(`${tagName}:has-text("${text}")`).first();
}

// Usage examples
const loginButton = await findByText(page, 'Sign in', 'button');
const sendButton = await findByText(page, 'Send', 'button');
```

### 3. Waiting Strategies
```javascript
// Wait for response to complete (streaming)
async function waitForResponseComplete(page, responseSelector) {
  // Look for indicators that streaming is complete
  const completionIndicators = [
    '.cursor-blink', // Blinking cursor indicating completion
    '[data-streaming="false"]',
    '.message-complete',
    ':not([aria-busy="true"])'
  ];
  
  await page.waitForFunction(() => {
    // Check if there are any streaming indicators
    const streamingElements = document.querySelectorAll('[aria-busy="true"], .streaming');
    return streamingElements.length === 0;
  });
}
```

### 4. Model Selection Helper
```javascript
async function selectModel(page, modelName) {
  const modelButtonSelectors = [
    'button[data-testid*="model"]',
    '[aria-label*="model"]',
    '.model-selector'
  ];
  
  const modelButton = await findElement(page, modelButtonSelectors);
  await modelButton.click();
  
  // Wait for dropdown and select model
  await page.waitForSelector('[role="listbox"], [role="menu"]');
  await page.click(`text="${modelName}"`);
}
```

## Error Handling Best Practices

### 1. Graceful Fallbacks
```javascript
async function sendMessage(page, message) {
  try {
    // Try primary method
    await sendMessagePrimary(page, message);
  } catch (error) {
    console.log('Primary method failed, trying fallback');
    await sendMessageFallback(page, message);
  }
}
```

### 2. Element State Validation
```javascript
async function validateElementState(page, selector) {
  const element = await page.locator(selector);
  
  // Check if element is visible and enabled
  const isVisible = await element.isVisible();
  const isEnabled = await element.isEnabled();
  
  if (!isVisible || !isEnabled) {
    throw new Error(`Element ${selector} is not ready for interaction`);
  }
  
  return element;
}
```

## Testing and Maintenance

### 1. Selector Health Check
```javascript
async function checkSelectorHealth(page, service) {
  const results = {};
  const selectors = SERVICE_SELECTORS[service];
  
  for (const [type, selectorList] of Object.entries(selectors)) {
    results[type] = {
      working: [],
      broken: []
    };
    
    for (const selector of selectorList) {
      try {
        const element = await page.waitForSelector(selector, { timeout: 1000 });
        if (element) {
          results[type].working.push(selector);
        }
      } catch (error) {
        results[type].broken.push(selector);
      }
    }
  }
  
  return results;
}
```

### 2. Regular Updates
- **Monthly Selector Audits**: Test all selectors against live services
- **Fallback Strategy Updates**: Add new patterns as services evolve
- **Community Contributions**: Maintain shared selector database

## Notes and Warnings

1. **Rate Limiting**: All AI services implement rate limiting. Implement appropriate delays.

2. **Terms of Service**: Ensure automation complies with each service's terms of service.

3. **Authentication**: Most services require active login sessions. Consider using authenticated browser contexts.

4. **Dynamic Content**: AI responses are streamed. Always wait for completion before proceeding.

5. **Browser Detection**: Services may detect automated browsers. Use stealth techniques if necessary.

6. **Selector Volatility**: UI elements change frequently. Always implement fallback strategies.

---

**Last Updated**: 2025-06-11  
**Recommended Review Frequency**: Monthly

For the most current selectors, inspect the live applications using browser developer tools and update this guide accordingly.