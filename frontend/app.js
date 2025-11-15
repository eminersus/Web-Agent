// Dynamically determine API base URL based on current host
// This allows the app to work from any machine on the network
const API_BASE = (() => {
  // Check if there's a meta tag with API URL (for production override)
  const metaApiUrl = document.querySelector('meta[name="api-url"]');
  if (metaApiUrl) {
    return metaApiUrl.getAttribute('content');
  }
  
  // Use current hostname with backend port
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
})();

// DOM elements
let messagesArea;
let chatInput;
let sendBtn;

// Active connections tracking
const activeConnections = new Map();

// Track streaming messages
const streamingMessages = new Map();

document.addEventListener("DOMContentLoaded", () => {
  console.log("eBay Web Agent frontend ready");

  // Get DOM elements
  messagesArea = document.getElementById("messages");
  chatInput = document.getElementById("chatInput");
  sendBtn = document.getElementById("sendBtn");

  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Health check to backend (logs only)
  fetch(`${API_BASE}/api/health`)
    .then((r) => r.json())
    .then((d) => console.log("Backend health:", d))
    .catch((err) => console.warn("Health check failed:", err));

  // Event listeners
  sendBtn.addEventListener("click", handleSend);
  chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });
});

/**
 * Handle send button click
 */
async function handleSend() {
  const text = chatInput.value.trim();
  if (!text) return;

  // Disable input while processing
  setInputEnabled(false);

  // Add user message to UI
  addMessage("user", text);

  // Clear input
  chatInput.value = "";

  try {
    // Step 1: POST message to backend
    console.log("[Chat] Sending message:", text);
    const response = await fetch(`${API_BASE}/api/chat/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const messageId = data.message_id;
    console.log("[Chat] Message created:", messageId);

    // Step 2: Connect to SSE stream or fallback to polling
    connectToStream(messageId);
  } catch (error) {
    console.error("[Chat] Error sending message:", error);
    addMessage("assistant", "❌ Error sending message. Please try again.");
    setInputEnabled(true);
  }
}

/**
 * Connect to SSE stream for real-time updates
 */
function connectToStream(messageId) {
  console.log(`[SSE] Connecting for message: ${messageId}`);

  try {
    const eventSource = new EventSource(
      `${API_BASE}/api/chat/messages/${messageId}/events`
    );

    // Track this connection
    activeConnections.set(messageId, {
      type: "sse",
      source: eventSource,
    });

    // Handle status events
    eventSource.addEventListener("status", (event) => {
      const data = JSON.parse(event.data);
      console.log(`[SSE] Status event:`, data);
      const message = data.message || formatStatus(data.stage);
      addStatusMessage(message);
    });

    // Handle token events (streaming LLM response)
    eventSource.addEventListener("token", (event) => {
      const data = JSON.parse(event.data);
      const token = data.token;
      
      // Get or create streaming message element
      let streamingMsg = streamingMessages.get(messageId);
      if (!streamingMsg) {
        streamingMsg = createStreamingMessage();
        streamingMessages.set(messageId, streamingMsg);
      }
      
      // Append token to streaming message
      appendTokenToMessage(streamingMsg, token);
    });

    // Handle response complete event
    eventSource.addEventListener("response_complete", (event) => {
      const data = JSON.parse(event.data);
      console.log(`[SSE] Response complete:`, data);
      
      // Finalize streaming message
      const streamingMsg = streamingMessages.get(messageId);
      if (streamingMsg) {
        finalizeStreamingMessage(streamingMsg);
        streamingMessages.delete(messageId);
      }
    });

    // Handle error events
    eventSource.addEventListener("error", (event) => {
      const data = JSON.parse(event.data);
      console.error(`[SSE] Error event:`, data);
      addMessage("assistant", `❌ ${data.message}`);
      
      // Clean up streaming message if exists
      const streamingMsg = streamingMessages.get(messageId);
      if (streamingMsg) {
        streamingMsg.element.remove();
        streamingMessages.delete(messageId);
      }
    });

    // Handle result events (for backward compatibility)
    eventSource.addEventListener("result", (event) => {
      const data = JSON.parse(event.data);
      console.log(`[SSE] Result event:`, data);
      addResultMessage(data);
    });

    // Handle done event
    eventSource.addEventListener("done", (event) => {
      console.log(`[SSE] Done event received`);
      eventSource.close();
      activeConnections.delete(messageId);
      streamingMessages.delete(messageId);
      setInputEnabled(true);
    });

    // Handle errors
    eventSource.onerror = (error) => {
      console.error(`[SSE] Connection error:`, error);
      eventSource.close();
      activeConnections.delete(messageId);

      // Fallback to polling
      console.log(`[SSE] Falling back to polling for message: ${messageId}`);
      startPolling(messageId);
    };
  } catch (error) {
    console.error(`[SSE] Failed to create EventSource:`, error);
    // Fallback to polling immediately
    console.log(`[SSE] Falling back to polling for message: ${messageId}`);
    startPolling(messageId);
  }
}

/**
 * Fallback polling mechanism
 */
function startPolling(messageId) {
  console.log(`[Polling] Starting for message: ${messageId}`);

  let lastEventCount = 0;
  let pollCount = 0;
  const maxPolls = 60; // Max 60 polls (30 seconds with 500ms interval)

  const pollInterval = setInterval(async () => {
    pollCount++;

    if (pollCount > maxPolls) {
      console.warn(`[Polling] Timeout for message: ${messageId}`);
      clearInterval(pollInterval);
      activeConnections.delete(messageId);
      addMessage("assistant", "⏱️ Request timed out. Please try again.");
      setInputEnabled(true);
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/chat/messages/${messageId}/status`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log(`[Polling] Status response:`, data);

      // Process new events
      const events = data.events || [];
      if (events.length > lastEventCount) {
        for (let i = lastEventCount; i < events.length; i++) {
          const event = events[i];
          
          if (event.type === "status") {
            const message = event.data.message || formatStatus(event.data.stage);
            addStatusMessage(message);
          } else if (event.type === "token") {
            // Handle streaming tokens in polling mode
            let streamingMsg = streamingMessages.get(messageId);
            if (!streamingMsg) {
              streamingMsg = createStreamingMessage();
              streamingMessages.set(messageId, streamingMsg);
            }
            appendTokenToMessage(streamingMsg, event.data.token);
          } else if (event.type === "response_complete") {
            const streamingMsg = streamingMessages.get(messageId);
            if (streamingMsg) {
              finalizeStreamingMessage(streamingMsg);
              streamingMessages.delete(messageId);
            }
          } else if (event.type === "error") {
            addMessage("assistant", `❌ ${event.data.message}`);
            const streamingMsg = streamingMessages.get(messageId);
            if (streamingMsg) {
              streamingMsg.element.remove();
              streamingMessages.delete(messageId);
            }
          } else if (event.type === "result") {
            addResultMessage(event.data);
          }
        }
        lastEventCount = events.length;
      }

      // Check if done
      if (data.done) {
        console.log(`[Polling] Message complete: ${messageId}`);
        clearInterval(pollInterval);
        activeConnections.delete(messageId);
        setInputEnabled(true);
      }
    } catch (error) {
      console.error(`[Polling] Error:`, error);
      clearInterval(pollInterval);
      activeConnections.delete(messageId);
      addMessage("assistant", "❌ Error fetching status. Please try again.");
      setInputEnabled(true);
    }
  }, 500); // Poll every 500ms

  // Track this connection
  activeConnections.set(messageId, {
    type: "polling",
    interval: pollInterval,
  });
}

/**
 * Add a message to the chat UI
 */
function addMessage(type, text) {
  // Remove welcome message if it exists
  const welcomeMsg = messagesArea.querySelector(".welcome-message");
  if (welcomeMsg) {
    welcomeMsg.remove();
  }

  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}`;
  messageDiv.textContent = text;
  messagesArea.appendChild(messageDiv);
  scrollToBottom();
}

/**
 * Add a status message to the chat UI
 */
function addStatusMessage(stage) {
  const statusText = formatStatus(stage);
  const messageDiv = document.createElement("div");
  messageDiv.className = "message status";
  messageDiv.textContent = `⏳ ${statusText}`;
  messagesArea.appendChild(messageDiv);
  scrollToBottom();
}

/**
 * Add a result message to the chat UI
 */
function addResultMessage(result) {
  const messageDiv = document.createElement("div");
  messageDiv.className = "message result";

  const title = document.createElement("div");
  title.className = "result-title";
  title.textContent = result.title || "Product";

  const price = document.createElement("div");
  price.className = "result-price";
  price.textContent = `$${result.price?.toFixed(2) || "0.00"}`;

  messageDiv.appendChild(title);
  messageDiv.appendChild(price);

  if (result.condition) {
    const condition = document.createElement("div");
    condition.className = "result-detail";
    condition.textContent = `Condition: ${result.condition}`;
    messageDiv.appendChild(condition);
  }

  if (result.url) {
    const link = document.createElement("a");
    link.className = "result-link";
    link.href = result.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "View on eBay →";
    messageDiv.appendChild(link);
  }

  messagesArea.appendChild(messageDiv);
  scrollToBottom();
}

/**
 * Create a new streaming message element
 */
function createStreamingMessage() {
  // Remove welcome message if it exists
  const welcomeMsg = messagesArea.querySelector(".welcome-message");
  if (welcomeMsg) {
    welcomeMsg.remove();
  }

  const messageDiv = document.createElement("div");
  messageDiv.className = "message assistant streaming";
  
  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";
  messageDiv.appendChild(contentDiv);
  
  // Add typing indicator
  const indicator = document.createElement("span");
  indicator.className = "typing-indicator";
  indicator.textContent = "▊";
  contentDiv.appendChild(indicator);
  
  messagesArea.appendChild(messageDiv);
  scrollToBottom();
  
  return {
    element: messageDiv,
    content: contentDiv,
    indicator: indicator,
    text: ""
  };
}

/**
 * Append a token to a streaming message
 */
function appendTokenToMessage(streamingMsg, token) {
  streamingMsg.text += token;
  
  // Update content (keep indicator at end)
  streamingMsg.content.textContent = streamingMsg.text;
  streamingMsg.content.appendChild(streamingMsg.indicator);
  
  scrollToBottom();
}

/**
 * Finalize a streaming message (remove indicator)
 */
function finalizeStreamingMessage(streamingMsg) {
  streamingMsg.element.classList.remove("streaming");
  streamingMsg.indicator.remove();
  streamingMsg.content.textContent = streamingMsg.text;
  scrollToBottom();
}

/**
 * Format status stage into human-readable text
 */
function formatStatus(stage) {
  const statusMap = {
    preparing: "Preparing your request...",
    querying_llm: "Thinking...",
    parsing: "Parsing your request...",
    searching_ebay: "Searching eBay...",
    completed: "Complete!",
  };
  return statusMap[stage] || stage;
}

/**
 * Enable or disable input controls
 */
function setInputEnabled(enabled) {
  chatInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
  if (enabled) {
    chatInput.focus();
  }
}

/**
 * Scroll messages area to bottom
 */
function scrollToBottom() {
  messagesArea.scrollTop = messagesArea.scrollHeight;
}

/**
 * Cleanup on page unload
 */
window.addEventListener("beforeunload", () => {
  activeConnections.forEach((connection, messageId) => {
    if (connection.type === "sse" && connection.source) {
      connection.source.close();
    } else if (connection.type === "polling" && connection.interval) {
      clearInterval(connection.interval);
    }
  });
  activeConnections.clear();
});
