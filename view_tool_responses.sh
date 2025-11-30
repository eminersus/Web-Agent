#!/bin/bash

# Script to view tool call responses from Docker logs
# Usage:
#   ./view_tool_responses.sh                    # View all tool responses
#   ./view_tool_responses.sh get_item_aspects   # View responses for specific tool
#   ./view_tool_responses.sh --follow           # Follow logs in real-time
#   ./view_tool_responses.sh --save             # Save responses to files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
FOLLOW=false
SAVE=false
TOOL_NAME=""
LINES=1000
SERVICE="backend"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --follow|-f)
            FOLLOW=true
            shift
            ;;
        --save|-s)
            SAVE=true
            shift
            ;;
        --lines|-n)
            LINES="$2"
            shift 2
            ;;
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] [TOOL_NAME]"
            echo ""
            echo "View tool call responses from Docker logs"
            echo ""
            echo "Options:"
            echo "  --follow, -f          Follow logs in real-time"
            echo "  --save, -s            Save responses to JSON files"
            echo "  --lines, -n N         Number of log lines to read (default: 1000)"
            echo "  --service SERVICE     Docker service to read logs from (default: backend)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # View all tool responses"
            echo "  $0 get_item_aspects_for_category     # View responses for specific tool"
            echo "  $0 --follow                          # Follow logs in real-time"
            echo "  $0 --save get_item_aspects           # Save responses to files"
            exit 0
            ;;
        *)
            TOOL_NAME="$1"
            shift
            ;;
    esac
done

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo -e "${RED}Error: docker-compose is not installed.${NC}"
    exit 1
fi

# Get the project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}Warning: No services appear to be running. Starting services...${NC}"
    docker-compose up -d > /dev/null 2>&1
    sleep 2
fi

# Create output directory if saving
if [ "$SAVE" = true ]; then
    OUTPUT_DIR="$SCRIPT_DIR/tool_responses"
    mkdir -p "$OUTPUT_DIR"
    echo -e "${GREEN}Responses will be saved to: $OUTPUT_DIR${NC}"
fi

# Function to extract and display tool response
extract_tool_response() {
    local log_line="$1"
    local tool_name=""
    local result_json=""
    
    # Check if this is a tool result log line
    if echo "$log_line" | grep -q "Tool result added"; then
        # Extract tool name and result - handle different log formats
        if echo "$log_line" | grep -q "Tool result added (truncated"; then
            # Pattern: "Tool result added (truncated, X bytes): tool_name - json..."
            tool_name=$(echo "$log_line" | sed -n 's/.*Tool result added (truncated, [0-9]* bytes): \([^ ]*\) - .*/\1/p')
            result_json=$(echo "$log_line" | sed -n 's/.*Tool result added (truncated, [0-9]* bytes): [^ ]* - //p' | sed 's/\.\.\.$//')
        elif echo "$log_line" | grep -q "Tool result added (full"; then
            # Pattern: "Tool result added (full, X bytes): tool_name"
            tool_name=$(echo "$log_line" | sed -n 's/.*Tool result added (full, [0-9]* bytes): \([^ ]*\)/\1/p')
            result_json="[Full response logged at DEBUG level - check logs with LOG_FULL_TOOL_RESPONSES=true]"
        else
            # Pattern: "Tool result added: tool_name - json"
            tool_name=$(echo "$log_line" | sed -n 's/.*Tool result added: \([^ ]*\) - .*/\1/p')
            result_json=$(echo "$log_line" | sed -n 's/.*Tool result added: [^ ]* - //p')
        fi
        
        # If we couldn't extract tool name, set default
        if [ -z "$tool_name" ]; then
            tool_name="unknown"
        fi
        
        # Filter by tool name if specified
        if [ -n "$TOOL_NAME" ] && ! echo "$tool_name" | grep -qi "$TOOL_NAME"; then
            return
        fi
        
        # Display the response
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}Tool: ${tool_name}${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        # Check if result is truncated
        if echo "$log_line" | grep -q "truncated"; then
            # Extract size using sed (works on both GNU and BSD/macOS)
            local size=$(echo "$log_line" | sed -n 's/.*truncated, \([0-9]*\) bytes.*/\1/p')
            if [ -z "$size" ]; then
                size="unknown"
            fi
            echo -e "${YELLOW}Note: Result is truncated (${size} bytes total).${NC}"
            echo -e "${YELLOW}To see full response, set LOG_FULL_TOOL_RESPONSES=true in .env and restart backend.${NC}"
            echo ""
        fi
        
        # If full response is logged, try to extract it from logs
        if [ "$result_json" = "[Full response logged at DEBUG level - check logs with LOG_FULL_TOOL_RESPONSES=true]" ]; then
            echo -e "${YELLOW}Fetching full response from logs...${NC}"
            
            # Extract the formatted response that comes after "Tool result formatted:"
            # The formatted response is logged on the same line and continues on subsequent lines
            # until the next log entry (which starts with container name like "web-agent-backend")
            local full_response=$(docker-compose logs --tail=2000 "$SERVICE" 2>&1 | \
                awk -v tool="$tool_name" '
                /Tool result formatted:/ {
                    # Found the formatted response line
                    # Extract everything after "Tool result formatted:"
                    sub(/.*Tool result formatted:/, "")
                    # Print the rest of this line
                    if (length($0) > 0) print
                    # Continue reading until next log entry
                    while ((getline line) > 0) {
                        # Stop if we hit a new log entry (starts with container name)
                        if (line ~ /^[a-z-]+[ |]/ && line !~ /Tool result/) {
                            break
                        }
                        # Remove log prefix (container name and timestamp)
                        sub(/^[^|]*\| /, "", line)
                        if (length(line) > 0) print line
                    }
                    exit
                }')
            
            # Clean up the response - remove any remaining log prefixes
            full_response=$(echo "$full_response" | sed 's/^[^|]*| //' | sed '/^$/d')
            
            if [ -n "$full_response" ] && [ ${#full_response} -gt 10 ]; then
                echo -e "${GREEN}Full response found:${NC}"
                # Try to pretty-print if it's JSON
                if command -v python3 > /dev/null 2>&1; then
                    echo "$full_response" | python3 -m json.tool 2>/dev/null || echo "$full_response"
                else
                    echo "$full_response"
                fi
            else
                echo -e "${YELLOW}Full response not found in recent logs.${NC}"
                echo -e "${YELLOW}The formatted response should be in the logs. Try:${NC}"
                echo -e "${YELLOW}  docker-compose logs backend | grep -A 100 'Tool result formatted:'${NC}"
                echo -e "${YELLOW}Or view all recent logs:${NC}"
                echo -e "${YELLOW}  docker-compose logs backend --tail=500 | less${NC}"
            fi
        # Try to pretty-print JSON if possible
        elif [ -n "$result_json" ]; then
            if command -v python3 > /dev/null 2>&1; then
                echo "$result_json" | python3 -m json.tool 2>/dev/null || echo "$result_json"
            else
                echo "$result_json"
            fi
        fi
        
        # Save to file if requested
        if [ "$SAVE" = true ] && [ -n "$result_json" ] && [ "$result_json" != "[Full response logged at DEBUG level - check logs with LOG_FULL_TOOL_RESPONSES=true]" ]; then
            local timestamp=$(date +"%Y%m%d_%H%M%S")
            local safe_tool_name=$(echo "$tool_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g')
            local filename="${OUTPUT_DIR}/${safe_tool_name}_${timestamp}.json"
            
            if command -v python3 > /dev/null 2>&1; then
                echo "$result_json" | python3 -m json.tool > "$filename" 2>/dev/null || echo "$result_json" > "$filename"
            else
                echo "$result_json" > "$filename"
            fi
            
            echo -e "${GREEN}Saved to: $filename${NC}"
        fi
    fi
}

# Function to get full tool response from API (if tool is still executing)
get_full_response_from_api() {
    local tool_name="$1"
    local tool_args="$2"
    
    if [ -z "$tool_name" ]; then
        return
    fi
    
    echo -e "${YELLOW}Attempting to get full response from API...${NC}"
    
    # Try to call the tool directly via API
    local response=$(curl -s -X POST "http://localhost:8001/tools/${tool_name}" \
        -H "Content-Type: application/json" \
        -d "$tool_args" 2>/dev/null || echo "")
    
    if [ -n "$response" ]; then
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    fi
}

# Main logic
if [ "$FOLLOW" = true ]; then
    echo -e "${GREEN}Following tool responses in real-time... (Press Ctrl+C to stop)${NC}"
    echo ""
    
    docker-compose logs -f "$SERVICE" 2>&1 | while IFS= read -r line; do
        if echo "$line" | grep -q "Tool result added"; then
            extract_tool_response "$line"
        fi
    done
else
    echo -e "${GREEN}Reading last ${LINES} lines of logs...${NC}"
    echo ""
    
    # Get all logs first (needed for extracting full responses)
    local all_logs=$(docker-compose logs --tail="$LINES" "$SERVICE" 2>&1)
    
    # Process tool result lines
    echo "$all_logs" | grep "Tool result added" | while IFS= read -r line; do
        extract_tool_response "$line"
    done
    
    # Also extract and display full formatted responses if they exist
    if echo "$all_logs" | grep -q "Tool result formatted:"; then
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}Full formatted responses found in logs:${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        # Extract each formatted response using awk
        echo "$all_logs" | awk '
        /Tool result formatted:/ {
            # Extract everything after "Tool result formatted:"
            sub(/.*Tool result formatted:/, "")
            print ""
            # Print the rest of this line (remove log prefix)
            if (length($0) > 0) {
                sub(/^[^|]*\| /, "", $0)
                print $0
            }
            # Continue reading until next log entry
            while ((getline line) > 0) {
                # Stop if we hit a new log entry (starts with container name)
                if (line ~ /^[a-z-]+[ |]/ && line !~ /Tool result/) {
                    break
                }
                # Remove log prefix
                sub(/^[^|]*\| /, "", line)
                if (length(line) > 0) print line
            }
            print ""
        }'
    fi
    
    # Also try to get recent tool calls and their full responses
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Recent tool executions:${NC}"
    docker-compose logs --tail="$LINES" "$SERVICE" 2>&1 | grep "Executing tool:" | tail -10
    
    echo ""
    echo -e "${GREEN}Tip: Use --follow to see responses in real-time${NC}"
    echo -e "${GREEN}Tip: Use --save to save responses to JSON files${NC}"
fi

