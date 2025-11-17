# Testing Guide

This guide helps you test the Web Agent implementation to ensure everything works correctly.

## Pre-Test Checklist

- [ ] Docker and Docker Compose installed
- [ ] OpenRouter API key configured in `.env`
- [ ] All services built and running

## Quick Test Suite

### 1. Service Health Tests

Run these commands to verify all services are healthy:

```bash
# Check Docker containers
docker-compose -f dev.yaml ps

# Expected: All services show "Up (healthy)"
```

```bash
# Test backend health
curl http://localhost:8000/api/health

# Expected: {"status":"healthy",...}
```

```bash
# Test all services health
curl http://localhost:8000/api/services/health

# Expected: All services show "healthy"
```

```bash
# Test MCP server health
curl http://localhost:8001/health

# Expected: {"status":"healthy",...}
```

### 2. LibreChat UI Tests

**Test 2.1: Access Frontend**
1. Open browser: http://localhost:3080
2. ✅ Page loads without errors
3. ✅ Registration/login form visible

**Test 2.2: Create Account**
1. Click "Sign Up"
2. Enter email: `test@example.com`
3. Enter password: `Test123!`
4. Click "Sign Up"
5. ✅ Account created successfully

**Test 2.3: Login**
1. Enter credentials
2. Click "Sign In"
3. ✅ Chat interface loads

**Test 2.4: Select Model**
1. Open model dropdown
2. Select "OpenRouter"
3. Choose "Claude 3.5 Sonnet"
4. ✅ Model selected

### 3. MCP Tool Tests

**Test 3.1: Get Current Time**
```
User: What time is it?
Expected: LLM responds with current date and time
Tool called: get_current_time()
```
✅ Pass / ❌ Fail

**Test 3.2: Calculator**
```
User: Calculate 25 * 17
Expected: LLM responds with 425
Tool called: calculate("25 * 17")
```
✅ Pass / ❌ Fail

**Test 3.3: Complex Calculation**
```
User: What is (100 + 50) / 3?
Expected: LLM responds with 50.0
Tool called: calculate("(100 + 50) / 3")
```
✅ Pass / ❌ Fail

**Test 3.4: Create Task**
```
User: Create a high-priority task to review documentation
Expected: LLM creates task and confirms with task ID
Tool called: create_task(title="review documentation", priority="high")
```
✅ Pass / ❌ Fail

**Test 3.5: List Tasks**
```
User: Show me all my tasks
Expected: LLM lists all tasks including the one just created
Tool called: list_tasks()
```
✅ Pass / ❌ Fail

**Test 3.6: Update Task**
```
User: Mark the documentation review task as completed
Expected: LLM updates task status
Tool called: update_task(task_id="...", status="completed")
```
✅ Pass / ❌ Fail

**Test 3.7: Delete Task**
```
User: Delete the completed task
Expected: LLM deletes task and confirms
Tool called: delete_task(task_id="...")
```
✅ Pass / ❌ Fail

**Test 3.8: Text Analysis**
```
User: Analyze the sentiment of this text: "I love this product! It's amazing!"
Expected: LLM returns positive sentiment
Tool called: analyze_text(text="...", analysis_type="sentiment")
```
✅ Pass / ❌ Fail

**Test 3.9: Keywords Extraction**
```
User: Extract keywords from: "Machine learning and artificial intelligence"
Expected: LLM returns keywords
Tool called: analyze_text(text="...", analysis_type="keywords")
```
✅ Pass / ❌ Fail

**Test 3.10: Text Summary**
```
User: Summarize this: [long text]
Expected: LLM returns summary
Tool called: analyze_text(text="...", analysis_type="summary")
```
✅ Pass / ❌ Fail

### 4. Placeholder Tool Tests

These tools return placeholder data (integrate real APIs to make functional):

**Test 4.1: Weather**
```
User: What's the weather in San Francisco?
Expected: LLM returns placeholder weather data with note about integration needed
Tool called: get_weather(location="San Francisco")
```
✅ Pass / ❌ Fail

**Test 4.2: Web Search**
```
User: Search the web for Python tutorials
Expected: LLM returns placeholder search results with note about integration needed
Tool called: search_web(query="Python tutorials")
```
✅ Pass / ❌ Fail

### 5. Backend API Tests

**Test 5.1: Root Endpoint**
```bash
curl http://localhost:8000/

# Expected: API info with architecture details
```
✅ Pass / ❌ Fail

**Test 5.2: MCP Info**
```bash
curl http://localhost:8000/api/mcp/info

# Expected: MCP server information
```
✅ Pass / ❌ Fail

**Test 5.3: OpenRouter Models**
```bash
curl http://localhost:8000/api/openrouter/models

# Expected: List of available models
```
✅ Pass / ❌ Fail

**Test 5.4: Flow Control (Placeholder)**
```bash
curl -X POST http://localhost:8000/api/flow/interrupt \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"test123","reason":"testing"}'

# Expected: Placeholder response
```
✅ Pass / ❌ Fail

### 6. Performance Tests

**Test 6.1: Response Time**
1. Send message: "What time is it?"
2. Measure time from send to response
3. ✅ Response < 3 seconds

**Test 6.2: Concurrent Requests**
1. Open 3 browser tabs
2. Send tool requests simultaneously
3. ✅ All execute without errors

**Test 6.3: Streaming**
1. Ask for a long response
2. ✅ Text streams in real-time

### 7. Error Handling Tests

**Test 7.1: Invalid Calculation**
```
User: Calculate abc + 123
Expected: LLM reports error message from calculator
```
✅ Pass / ❌ Fail

**Test 7.2: Division by Zero**
```
User: What is 10 / 0?
Expected: LLM reports error from calculator
```
✅ Pass / ❌ Fail

**Test 7.3: Invalid Task ID**
```
User: Delete task with ID "invalid123"
Expected: LLM reports task not found
```
✅ Pass / ❌ Fail

### 8. Integration Tests

**Test 8.1: Multi-Tool Conversation**
```
User: What time is it?
User: Calculate how many hours until 5pm
User: Create a task to finish work by 5pm
User: Show me my tasks
```
✅ All tools work in sequence

**Test 8.2: Context Retention**
```
User: Create a task called "Project A"
User: Update that task to high priority
User: Show me the task
```
✅ LLM maintains context across messages

### 9. Architecture Validation Tests

**Test 9.1: Direct SSE Connection**
```bash
# Watch MCP logs for SSE connections
docker-compose -f dev.yaml logs -f mcp-server | grep -i sse

# Expected: See SSE connection logs
```
✅ Pass / ❌ Fail

**Test 9.2: Backend Not Proxying**
```bash
# Watch backend logs
docker-compose -f dev.yaml logs -f backend

# During tool execution, backend should NOT show tool call logs
# Only LibreChat → MCP direct
```
✅ Pass / ❌ Fail

**Test 9.3: FastMCP Initialization**
```bash
docker-compose -f dev.yaml logs mcp-server | grep -i "fastmcp"

# Expected: See FastMCP initialization logs
```
✅ Pass / ❌ Fail

### 10. Stress Tests (Optional)

**Test 10.1: Rapid Fire**
Send 10 messages quickly:
```
What time is it?
Calculate 1+1
Calculate 2+2
Calculate 3+3
...
```
✅ All responses correct

**Test 10.2: Long Session**
Keep conversation active for 30+ minutes
✅ No disconnections or errors

**Test 10.3: Large Inputs**
Send very long text for analysis
✅ Handles gracefully

## Test Results Template

```
Test Date: _______________
Tester: _______________

Service Health: ✅ / ❌
UI Access: ✅ / ❌
Account Creation: ✅ / ❌
Model Selection: ✅ / ❌

Tools:
- get_current_time: ✅ / ❌
- calculate: ✅ / ❌
- create_task: ✅ / ❌
- list_tasks: ✅ / ❌
- update_task: ✅ / ❌
- delete_task: ✅ / ❌
- analyze_text: ✅ / ❌
- get_weather: ✅ / ❌
- search_web: ✅ / ❌

Backend API: ✅ / ❌
Performance: ✅ / ❌
Error Handling: ✅ / ❌
Architecture: ✅ / ❌

Overall: ✅ PASS / ❌ FAIL

Notes:
_____________________
_____________________
```

## Troubleshooting Failed Tests

### Tool Not Working
1. Check MCP server logs: `docker-compose -f dev.yaml logs mcp-server`
2. Verify tool is registered in `server.py`
3. Restart MCP: `docker-compose -f dev.yaml restart mcp-server`

### No Response from LLM
1. Check OpenRouter API key in `.env`
2. Verify credits at openrouter.ai
3. Check backend logs: `docker-compose -f dev.yaml logs backend`

### SSE Connection Issues
1. Verify `librechat.yaml` has `type: sse`
2. Check MCP server is accessible: `curl http://localhost:8001/health`
3. Restart LibreChat: `docker-compose -f dev.yaml restart librechat`

### Service Won't Start
1. Check logs: `docker-compose -f dev.yaml logs [service-name]`
2. Verify ports not in use: `lsof -i :3080` etc.
3. Rebuild: `docker-compose -f dev.yaml up --build -d`

## Automated Test Script

Save as `test.sh`:

```bash
#!/bin/bash

echo "🧪 Web Agent Test Suite"
echo "======================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    echo -n "Testing $name... "
    
    if curl -s -f "$url" > /dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Run tests
test_endpoint "Backend Health" "http://localhost:8000/api/health"
test_endpoint "Services Health" "http://localhost:8000/api/services/health"
test_endpoint "MCP Health" "http://localhost:8001/health"
test_endpoint "LibreChat" "http://localhost:3080"

echo ""
echo "✅ Automated tests complete!"
echo "🔍 Run manual UI tests for full validation"
```

Run with:
```bash
chmod +x test.sh
./test.sh
```

## Continuous Testing

For ongoing development:

```bash
# Watch for changes and test
watch -n 30 './test.sh'

# Or use docker-compose logs
docker-compose -f dev.yaml logs -f
```

## Success Criteria

All tests should pass for a successful implementation:
- ✅ All services healthy
- ✅ LibreChat accessible
- ✅ All tools functional
- ✅ Direct SSE connection verified
- ✅ Backend monitoring works
- ✅ Error handling proper
- ✅ Performance acceptable

---

**Happy Testing! 🧪**

