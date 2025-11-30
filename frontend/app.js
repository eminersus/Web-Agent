// Configuration
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : `${window.location.protocol}//${window.location.hostname}:8000`;

// State
let conversationHistory = [];
let isProcessing = false;

// DOM Elements
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const clearChatButton = document.getElementById('clear-chat');
const connectionStatus = document.getElementById('connection-status');
const modelSelect = document.getElementById('model-select');
const exportChatButton = document.getElementById('export-chat');
const toggleTimestampsButton = document.getElementById('toggle-timestamps');
const toggleSidebarButton = document.getElementById('toggle-sidebar');
const messageCountElement = document.getElementById('message-count');
const toolCountElement = document.getElementById('tool-count');

// Utility state
let showTimestamps = false;
let messageCount = 0;
let toolCount = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkConnection();
    setupEventListeners();
    autoResizeTextarea();
    loadChatHistory();
});

// Setup event listeners
function setupEventListeners() {
    sendButton.addEventListener('click', sendMessage);

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    messageInput.addEventListener('input', autoResizeTextarea);

    clearChatButton.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear the chat history?')) {
            clearChat();
        }
    });

    exportChatButton.addEventListener('click', exportChat);

    toggleTimestampsButton.addEventListener('click', toggleTimestamps);

    toggleSidebarButton.addEventListener('click', toggleSidebar);

    modelSelect.addEventListener('change', saveChatHistory);

    // Example query buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('example-query')) {
            const query = e.target.textContent.replace(/"/g, '');
            messageInput.value = query;
            messageInput.focus();
        }
    });
}

// Auto resize textarea
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

// Check backend connection
async function checkConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        if (response.ok) {
            updateConnectionStatus('connected', 'Connected');
        } else {
            updateConnectionStatus('disconnected', 'Backend Error');
        }
    } catch (error) {
        updateConnectionStatus('disconnected', 'Disconnected');
        console.error('Connection check failed:', error);
    }
}

// Update connection status
function updateConnectionStatus(status, text) {
    connectionStatus.className = `status-indicator ${status}`;
    connectionStatus.textContent = text;
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message || isProcessing) {
        return;
    }

    // Add user message to UI
    addMessage('user', message);

    // Add to conversation history
    conversationHistory.push({
        role: 'user',
        content: message
    });

    // Clear input
    messageInput.value = '';
    autoResizeTextarea();

    // Disable input during processing
    isProcessing = true;
    updateUIProcessing(true);

    // Show thinking indicator
    const thinkingId = showThinking();

    try {
        // Send to backend and get streaming response
        await streamChatCompletion(conversationHistory, thinkingId);
    } catch (error) {
        console.error('Error sending message:', error);
        removeThinking(thinkingId);
        addMessage('error', `Error: ${error.message}`);
    } finally {
        isProcessing = false;
        updateUIProcessing(false);
        saveChatHistory();
    }
}

// Stream chat completion from backend
async function streamChatCompletion(messages, thinkingId) {
    const model = modelSelect.value;

    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            messages,
            model,
            stream: true
        })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    removeThinking(thinkingId);

    // We'll create the assistant message only when we get actual text
    let messageId = null;
    let fullResponse = '';
    let toolCallsInfo = [];
    let hasToolCalls = false; // Track if we've seen any tool calls
    let textAfterToolCall = false; // Track if we're getting text AFTER tool calls

    // Read the stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = ''; // Buffer for incomplete lines

    try {
        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                break;
            }

            // Decode the chunk and add to buffer
            buffer += decoder.decode(value, { stream: true });

            // Split by newlines, but keep the last incomplete line in buffer
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep the last (potentially incomplete) line

            for (const line of lines) {
                if (!line.trim() || !line.startsWith('data: ')) {
                    continue;
                }

                const data = line.slice(6); // Remove 'data: ' prefix

                if (data === '[DONE]') {
                    continue;
                }

                try {
                    const parsed = JSON.parse(data);

                    // Handle tool calls FIRST
                    if (parsed.type === 'tool_call') {
                        hasToolCalls = true;
                        textAfterToolCall = false; // Reset flag
                        const toolCall = {
                            id: parsed.id,
                            name: parsed.name,
                            arguments: parsed.arguments
                        };
                        toolCallsInfo.push(toolCall);
                        const toolCallId = showToolCall(toolCall);
                        // Store the ID so we can update it later with the result
                        toolCall._messageId = toolCallId;
                    }

                    // Handle text token
                    if (parsed.type === 'token' && parsed.token) {
                        // If we've had tool calls and this is the first text after, create NEW message
                        if (hasToolCalls && !textAfterToolCall) {
                            // This is text AFTER tool calls - create a fresh message
                            messageId = 'msg-after-tool-' + Date.now();
                            const messageElement = createMessageElement('assistant', '', messageId);
                            messagesContainer.appendChild(messageElement);
                            fullResponse = ''; // Reset response
                            textAfterToolCall = true;
                        } else if (!messageId) {
                            // First text ever - create initial message
                            messageId = 'msg-' + Date.now();
                            const messageElement = createMessageElement('assistant', '', messageId);
                            messagesContainer.appendChild(messageElement);
                        }

                        fullResponse += parsed.token;
                        updateMessageContent(messageId, fullResponse);
                        scrollToBottom();
                    }

                    // Handle tool results
                    if (parsed.type === 'tool_result') {
                        const toolResult = {
                            id: parsed.id,
                            name: parsed.name,
                            result: parsed.result
                        };
                        console.log('[Tool Result] Received:', {
                            id: toolResult.id,
                            name: toolResult.name,
                            resultSize: JSON.stringify(toolResult.result).length,
                            availableToolCalls: toolCallsInfo.map(tc => ({ id: tc.id, name: tc.name, hasMessageId: !!tc._messageId }))
                        });

                        // Find the matching tool call by ID
                        let matchingToolCall = toolCallsInfo.find(tc => tc.id === parsed.id);

                        // If not found by ID, try to find by name (most recent one)
                        if (!matchingToolCall) {
                            console.warn('[Tool Result] No match by ID, trying by name:', parsed.name);
                            const byName = toolCallsInfo.filter(tc => tc.name === parsed.name);
                            if (byName.length > 0) {
                                matchingToolCall = byName[byName.length - 1]; // Get most recent
                                console.log('[Tool Result] Found by name:', matchingToolCall.id);
                            }
                        }

                        if (matchingToolCall && matchingToolCall._messageId) {
                            console.log('[Tool Result] Updating tool call:', matchingToolCall._messageId);
                            updateToolCallWithResult(matchingToolCall._messageId, toolResult);
                        } else {
                            console.error('[Tool Result] Cannot update - no matching tool call found', {
                                resultId: parsed.id,
                                resultName: parsed.name,
                                toolCallsInfo: toolCallsInfo
                            });
                        }
                    }

                    // Handle product cards
                    if (parsed.type === 'product_cards') {
                        console.log('Received product_cards event:', parsed);
                        const products = parsed.products || [];
                        console.log('Products array:', products);
                        displayProductCards(products);
                    }

                    // Handle errors
                    if (parsed.type === 'error' && parsed.error) {
                        addMessage('error', `Error: ${parsed.error}`);
                    }

                    // Handle done
                    if (parsed.type === 'done') {
                        // Stream completed
                    }

                } catch (e) {
                    console.error('Error parsing chunk:', e, data);
                }
            }
        }
    } finally {
        reader.releaseLock();
    }

    // Add to conversation history
    if (fullResponse) {
        conversationHistory.push({
            role: 'assistant',
            content: fullResponse
        });
    }

    // If no response was generated, show an error
    if (!fullResponse && toolCallsInfo.length === 0) {
        addMessage('error', 'No response received from the assistant.');
    }
}

// Add message to UI
function addMessage(type, content, messageId = null) {
    // Hide welcome message on first message
    hideWelcomeMessage();

    const id = messageId || 'msg-' + Date.now();
    const messageElement = createMessageElement(type, content, id);
    messagesContainer.appendChild(messageElement);
    scrollToBottom();

    // Update message count for user and assistant messages
    if (type === 'user' || type === 'assistant') {
        updateMessageCount();
    }

    return id;
}

// Create message element
function createMessageElement(type, content, id) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.id = id;

    const labels = {
        user: 'You',
        assistant: 'Assistant',
        system: 'System',
        tool: 'Tool',
        error: 'Error'
    };

    const timestamp = new Date().toLocaleTimeString();

    messageDiv.innerHTML = `
        <div class="message-label">${labels[type] || type}</div>
        <div class="message-content">
            ${formatContent(content)}
        </div>
        <div class="message-timestamp">${timestamp}</div>
    `;

    return messageDiv;
}

// Update message content
function updateMessageContent(messageId, content) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        const contentElement = messageElement.querySelector('.message-content');
        if (contentElement) {
            contentElement.innerHTML = formatContent(content);
        }
    }
}

// Format message content
function formatContent(content) {
    if (!content) {
        return '';
    }

    // Convert markdown-like formatting
    let formatted = content
        .replace(/\n/g, '<br>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>');

    return formatted;
}

// Show thinking indicator
function showThinking() {
    const id = 'thinking-' + Date.now();
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message assistant';
    thinkingDiv.id = id;
    thinkingDiv.innerHTML = `
        <div class="message-label">Assistant</div>
        <div class="thinking-indicator">
            <span>Thinking</span>
            <div class="dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(thinkingDiv);
    scrollToBottom();
    return id;
}

// Remove thinking indicator
function removeThinking(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// Show tool call with collapsible box
function showToolCall(toolCall) {
    // Hide welcome message and update counters
    hideWelcomeMessage();
    updateToolCount();

    const messageId = 'tool-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = messageId;

    // Store tool call data for later
    messageDiv.dataset.toolCall = JSON.stringify(toolCall);
    messageDiv.dataset.toolResult = null;

    const toolCallBox = createToolCallBox(toolCall, null, messageId);

    messageDiv.innerHTML = `<div class="message-label">Tool Execution</div>`;
    messageDiv.appendChild(toolCallBox);

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    return messageId;
}

// Create tool call box (collapsible)
function createToolCallBox(toolCall, toolResult, messageId) {
    const box = document.createElement('div');
    box.className = 'tool-call-box';
    box.id = `tool-box-${messageId}`;

    const hasResult = toolResult !== null;
    const hasError = hasResult && toolResult.result && typeof toolResult.result === 'object' && toolResult.result.error;

    const argsJson = JSON.stringify(toolCall.arguments, null, 2);
    const resultJson = hasResult ? JSON.stringify(toolResult.result, null, 2) : '';

    box.innerHTML = `
        <div class="tool-call-header">
            <span class="tool-call-icon">🔧</span>
            <span class="tool-call-name">${toolCall.name}</span>
            ${hasResult ? `<span class="tool-call-status ${hasError ? 'error' : 'success'}">${hasError ? 'Error' : 'Success'}</span>` : ''}
            <span class="tool-call-toggle">▼ Click to expand</span>
        </div>
        <div class="tool-call-details" id="details-${messageId}">
            <div class="tool-call-section" data-section="args">
                <div class="tool-call-label">
                    <span>📝 Arguments</span>
                    <button class="copy-btn" data-copy-type="args">
                        <span class="copy-icon">📋</span>
                        <span class="copy-text">Copy</span>
                    </button>
                </div>
                <div class="tool-call-content">${argsJson}</div>
            </div>
            ${hasResult ? `
            <div class="tool-call-section" data-section="result">
                <div class="tool-call-label">
                    <span>${hasError ? '❌ Error' : '✅ Response'}</span>
                    <button class="copy-btn" data-copy-type="result">
                        <span class="copy-icon">📋</span>
                        <span class="copy-text">Copy</span>
                    </button>
                </div>
                <div class="tool-call-content tool-result-content">${resultJson}</div>
            </div>
            ` : '<div class="tool-call-section"><div class="tool-call-label">⏳ Executing...</div><div class="tool-call-content"><em>Waiting for tool to complete...</em></div></div>'}
        </div>
    `;

    // Add click handler to toggle details
    const header = box.querySelector('.tool-call-header');
    header.addEventListener('click', () => {
        const details = box.querySelector('.tool-call-details');
        const toggle = box.querySelector('.tool-call-toggle');

        if (details.classList.contains('expanded')) {
            details.classList.remove('expanded');
            toggle.textContent = '▼ Click to expand';
        } else {
            details.classList.add('expanded');
            toggle.textContent = '▲ Click to collapse';
        }
    });

    // Add copy button handlers
    const copyButtons = box.querySelectorAll('.copy-btn');
    copyButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation(); // Prevent toggle

            const copyType = btn.dataset.copyType;
            const section = btn.closest('.tool-call-section');
            const content = section.querySelector('.tool-call-content').textContent;

            try {
                await navigator.clipboard.writeText(content);

                // Visual feedback
                const copyText = btn.querySelector('.copy-text');
                const originalText = copyText.textContent;
                copyText.textContent = 'Copied!';
                btn.classList.add('copied');

                setTimeout(() => {
                    copyText.textContent = originalText;
                    btn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
                const copyText = btn.querySelector('.copy-text');
                copyText.textContent = 'Failed';
                setTimeout(() => {
                    copyText.textContent = 'Copy';
                }, 2000);
            }
        });
    });

    return box;
}

// Update tool call with result
function updateToolCallWithResult(toolCallId, toolResult) {
    console.log('[updateToolCallWithResult] Called:', { toolCallId, toolResultName: toolResult.name });

    const messageElement = document.getElementById(toolCallId);
    if (!messageElement) {
        console.error('[updateToolCallWithResult] Message element not found:', toolCallId);
        return;
    }

    // Get stored tool call data
    let toolCallData;
    try {
        toolCallData = JSON.parse(messageElement.dataset.toolCall);
    } catch (e) {
        console.error('[updateToolCallWithResult] Error parsing tool call data:', e);
        return;
    }

    // Update stored result
    messageElement.dataset.toolResult = JSON.stringify(toolResult);

    // Update the box with result
    const newBox = createToolCallBox(toolCallData, toolResult, toolCallId);
    const oldBox = messageElement.querySelector('.tool-call-box');
    if (oldBox) {
        console.log('[updateToolCallWithResult] Replacing tool call box');
        oldBox.replaceWith(newBox);

        // Auto-expand to show the result
        const details = newBox.querySelector('.tool-call-details');
        if (details) {
            details.classList.add('expanded');
            const toggle = newBox.querySelector('.tool-call-toggle');
            if (toggle) {
                toggle.textContent = '▲ Click to collapse';
            }
        }

        scrollToBottom();
    } else {
        console.error('[updateToolCallWithResult] Tool call box not found in message element');
    }
}

// Show tool result (now just updates the existing box)
function showToolResult(toolResult) {
    // Find the most recent tool call message and update it
    const toolMessages = Array.from(messagesContainer.querySelectorAll('.message.assistant')).filter(
        msg => msg.dataset.toolCall
    );

    if (toolMessages.length > 0) {
        const lastToolMessage = toolMessages[toolMessages.length - 1];
        updateToolCallWithResult(lastToolMessage.id, toolResult);
    }
}

// Update UI during processing
function updateUIProcessing(processing) {
    sendButton.disabled = processing;
    messageInput.disabled = processing;

    if (processing) {
        sendButton.style.opacity = '0.5';
    } else {
        sendButton.style.opacity = '1';
        messageInput.focus();
    }
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Clear chat
function clearChat() {
    // Clear all messages
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🎉</div>
            <h2>Welcome to eBay Web Agent!</h2>
            <p>Your AI-powered shopping assistant for eBay. Ask me to search for products, compare prices, or get detailed information about items.</p>
            <div class="example-queries">
                <span class="example-label">Try asking:</span>
                <button class="example-query">"Find me iPhone 16 Pro under $1000"</button>
                <button class="example-query">"Search for vintage watches"</button>
                <button class="example-query">"Show me gaming laptops with free shipping"</button>
            </div>
        </div>
    `;
    conversationHistory = [];
    messageCount = 0;
    toolCount = 0;
    if (messageCountElement) messageCountElement.textContent = '0';
    if (toolCountElement) toolCountElement.textContent = '0';
    saveChatHistory();
}

// Save chat history to localStorage
function saveChatHistory() {
    try {
        localStorage.setItem('chatHistory', JSON.stringify(conversationHistory));
        localStorage.setItem('selectedModel', modelSelect.value);
    } catch (error) {
        console.error('Error saving chat history:', error);
    }
}

// Load chat history from localStorage
function loadChatHistory() {
    try {
        const saved = localStorage.getItem('chatHistory');
        const savedModel = localStorage.getItem('selectedModel');

        if (savedModel) {
            modelSelect.value = savedModel;
        }

        if (saved) {
            conversationHistory = JSON.parse(saved);

            // Restore messages to UI
            for (const msg of conversationHistory) {
                if (msg.role === 'user' || msg.role === 'assistant') {
                    addMessage(msg.role, msg.content);
                }
            }
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

// Export chat history
function exportChat() {
    try {
        const chatData = {
            model: modelSelect.value,
            timestamp: new Date().toISOString(),
            messages: conversationHistory
        };

        const dataStr = JSON.stringify(chatData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `ebay-agent-chat-${Date.now()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        showNotification('Chat history exported successfully!', 'success');
    } catch (error) {
        console.error('Error exporting chat:', error);
        showNotification('Failed to export chat history', 'error');
    }
}

// Toggle timestamps
function toggleTimestamps() {
    showTimestamps = !showTimestamps;
    messagesContainer.classList.toggle('show-timestamps', showTimestamps);

    const buttonText = toggleTimestampsButton.querySelector('svg').nextSibling;
    if (buttonText) {
        buttonText.textContent = showTimestamps ? ' Hide Timestamps' : ' Toggle Timestamps';
    }
}

// Toggle sidebar
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('hidden');
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? 'var(--accent-success)' : 'var(--accent-error)'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: var(--shadow-lg);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Update message count
function updateMessageCount() {
    messageCount++;
    if (messageCountElement) {
        messageCountElement.textContent = messageCount;
    }
}

// Update tool count
function updateToolCount() {
    toolCount++;
    if (toolCountElement) {
        toolCountElement.textContent = toolCount;
    }
}

// Hide welcome message
function hideWelcomeMessage() {
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
}

// Display product cards
function displayProductCards(products) {
    console.log('displayProductCards called with:', products);
    console.log('Number of products:', products.length);

    hideWelcomeMessage();

    const messageId = 'product-cards-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant product-cards-message';
    messageDiv.id = messageId;

    const header = document.createElement('div');
    header.className = 'message-label';
    header.textContent = 'Product Results';
    messageDiv.appendChild(header);

    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'product-cards-container';

    products.forEach((product, index) => {
        console.log(`Creating card ${index + 1}:`, product);
        try {
            const card = createProductCard(product, index);
            cardsContainer.appendChild(card);
        } catch (error) {
            console.error(`Error creating card ${index + 1}:`, error);
        }
    });

    messageDiv.appendChild(cardsContainer);
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    console.log('Message div appended to DOM:', messageDiv);
    console.log('Cards container children:', cardsContainer.children.length);
    console.log('Message div in DOM?', document.getElementById(messageId) !== null);

    return messageId;
}

// Create a single product card
function createProductCard(product, index) {
    const card = document.createElement('div');
    card.className = 'product-card';

    const shipping = product.shipping || 'See listing for shipping';
    const isFreeShipping = shipping.toLowerCase().includes('free');

    card.innerHTML = `
        <div class="product-card-image">
            <img src="${product.image || ''}" alt="${escapeHtml(product.title || 'Product')}" loading="lazy" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22%3ENo Image%3C/text%3E%3C/svg%3E'" />
            ${product.condition ? `<span class="product-condition">${escapeHtml(product.condition)}</span>` : ''}
        </div>
        <div class="product-card-content">
            <h3 class="product-title">${escapeHtml(product.title || 'No title')}</h3>
            <div class="product-price">${escapeHtml(product.price || 'N/A')}</div>
            ${product.seller ? `<div class="product-seller">Seller: ${escapeHtml(product.seller)}</div>` : ''}
            ${product.location ? `<div class="product-location">📍 ${escapeHtml(product.location)}</div>` : ''}
            <div class="product-shipping ${isFreeShipping ? 'free-shipping' : ''}">
                ${isFreeShipping ? '✅' : '🚚'} ${escapeHtml(shipping)}
            </div>
            <a href="${product.url || '#'}" target="_blank" rel="noopener noreferrer" class="product-link">
                View on eBay →
            </a>
        </div>
    `;

    return card;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Periodic connection check
setInterval(checkConnection, 30000); // Check every 30 seconds

