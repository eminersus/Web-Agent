#!/bin/bash

# Test script to verify the Web Agent setup
# This script checks if all components are working correctly

set -e

echo "🧪 Testing Web Agent Setup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Status: $response)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $response)"
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local name=$1
    local url=$2
    
    echo -n "Testing $name... "
    
    response=$(curl -s "$url" 2>&1)
    
    if echo "$response" | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "   Response: $(echo $response | jq -c .)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "   Response: $response"
        return 1
    fi
}

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5
echo ""

# Test Frontend
echo "1️⃣  Testing Frontend (Nginx)"
echo "--------------------------------"
test_endpoint "Frontend Health" "http://localhost:3080/health" "200"
test_endpoint "Frontend Index" "http://localhost:3080/" "200"
echo ""

# Test Backend
echo "2️⃣  Testing Backend"
echo "--------------------------------"
test_json_endpoint "Backend Health" "http://localhost:8000/api/health"
test_json_endpoint "Services Health" "http://localhost:8000/api/services/health"
echo ""

# Test MCP Server
echo "3️⃣  Testing MCP Server"
echo "--------------------------------"
test_json_endpoint "MCP Health" "http://localhost:8001/health"
test_json_endpoint "MCP Tools List" "http://localhost:8001/tools"
echo ""

# Test tool execution
echo "4️⃣  Testing Tool Execution"
echo "--------------------------------"
echo "Testing calculate tool..."
result=$(curl -s -X POST "http://localhost:8001/tools/calculate" \
    -H "Content-Type: application/json" \
    -d '{"expression": "2+2"}' 2>&1)

if echo "$result" | jq -e '.result' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "   Result: $(echo $result | jq -c .)"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "   Response: $result"
fi
echo ""

# Test chat endpoint
echo "5️⃣  Testing Chat Endpoint"
echo "--------------------------------"
echo "Testing chat stream endpoint..."

# Note: This just checks if the endpoint is accessible, not the full streaming
response=$(curl -s -X POST "http://localhost:8000/api/chat/stream" \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "Hello"}], "model": "anthropic/claude-3.5-sonnet"}' \
    --max-time 5 2>&1 | head -n 1)

if [ -n "$response" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "   First chunk received: $response"
else
    echo -e "${YELLOW}⚠ WARN${NC}"
    echo "   No response received (this might be due to API key or rate limiting)"
fi
echo ""

# Summary
echo "================================"
echo "✅ Setup Test Complete!"
echo ""
echo "📝 Next Steps:"
echo "   1. Open http://localhost:3080 in your browser"
echo "   2. Make sure OPENROUTER_API_KEY is set in .env"
echo "   3. Try chatting with the assistant"
echo "   4. Test tool usage by asking to calculate or get time"
echo ""
echo "📚 Documentation:"
echo "   - Frontend Guide: FRONTEND_GUIDE.md"
echo "   - Architecture: ARCHITECTURE.md"
echo ""

