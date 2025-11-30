# Tool Response Logging Guide

This guide explains how to view tool call responses in logs.

## Quick Start

### View Recent Tool Responses
```bash
./view_tool_responses.sh
```

### Follow Tool Responses in Real-Time
```bash
./view_tool_responses.sh --follow
```

### View Responses for Specific Tool
```bash
./view_tool_responses.sh get_item_aspects_for_category
```

### Save Responses to Files
```bash
./view_tool_responses.sh --save
```

## Configuration Options

### Enable Full Response Logging

By default, tool responses are truncated to 200 characters in logs. To see full responses:

1. Edit `.env` file:
```bash
LOG_FULL_TOOL_RESPONSES=true
TOOL_RESPONSE_LOG_LIMIT=200  # Only used when LOG_FULL_TOOL_RESPONSES=false
```

2. Restart the backend service:
```bash
docker-compose restart backend
```

3. View full responses:
```bash
# View full responses from logs
./view_tool_responses.sh

# Or follow in real-time
./view_tool_responses.sh --follow
```

## Script Usage

### Basic Usage
```bash
# View all tool responses from last 1000 log lines
./view_tool_responses.sh

# View responses for specific tool
./view_tool_responses.sh get_item_aspects_for_category

# Follow logs in real-time
./view_tool_responses.sh --follow

# Save responses to JSON files
./view_tool_responses.sh --save
```

### Advanced Options
```bash
# View last 5000 lines
./view_tool_responses.sh --lines 5000

# View from MCP server logs
./view_tool_responses.sh --service mcp-server

# Combine options
./view_tool_responses.sh --follow --save get_item_aspects
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--follow`, `-f` | Follow logs in real-time |
| `--save`, `-s` | Save responses to JSON files in `tool_responses/` directory |
| `--lines`, `-n N` | Number of log lines to read (default: 1000) |
| `--service SERVICE` | Docker service to read logs from (default: backend) |
| `--help`, `-h` | Show help message |

## Examples

### Example 1: View Recent Tool Responses
```bash
$ ./view_tool_responses.sh

Reading last 1000 lines of logs...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tool: get_item_aspects_for_category
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Note: Result is truncated (8255 bytes total).
To see full response, set LOG_FULL_TOOL_RESPONSES=true in .env and restart backend.

{
  "aspects": [
    {
      "localizedAspectName": "Brand",
      ...
    }
  ]
}
```

### Example 2: Follow Tool Responses in Real-Time
```bash
$ ./view_tool_responses.sh --follow

Following tool responses in real-time... (Press Ctrl+C to stop)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tool: search_items
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "itemSummaries": [
    {
      "itemId": "123456789",
      "title": "iPhone 15 Pro",
      ...
    }
  ]
}
```

### Example 3: Save Responses to Files
```bash
$ ./view_tool_responses.sh --save get_item_aspects

Responses will be saved to: /path/to/Web-Agent/tool_responses

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tool: get_item_aspects_for_category
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
Saved to: tool_responses/get_item_aspects_for_category_20251130_084530.json
```

## Viewing Full Responses

### Method 1: Enable Full Logging (Recommended)

1. Set `LOG_FULL_TOOL_RESPONSES=true` in `.env`
2. Restart backend: `docker-compose restart backend`
3. Run the script: `./view_tool_responses.sh`

Full responses will be logged at DEBUG level and can be viewed with:
```bash
docker-compose logs backend | grep -A 100 "Tool result formatted:"
```

### Method 2: Direct API Call

If you know the tool name and arguments, you can call it directly:

```bash
curl -X POST http://localhost:8001/tools/get_item_aspects_for_category \
  -H "Content-Type: application/json" \
  -d '{"category_id": "9355"}' \
  | python3 -m json.tool > response.json

cat response.json
```

### Method 3: Save from Script

Use the `--save` option to save truncated responses to files:
```bash
./view_tool_responses.sh --save
```

## Troubleshooting

### No Tool Responses Found

1. Check if services are running:
```bash
docker-compose ps
```

2. Check if tools are being called:
```bash
docker-compose logs backend | grep "Executing tool:"
```

3. Increase log lines:
```bash
./view_tool_responses.sh --lines 5000
```

### Responses Are Truncated

1. Enable full logging in `.env`:
```bash
LOG_FULL_TOOL_RESPONSES=true
```

2. Restart backend:
```bash
docker-compose restart backend
```

3. View full responses:
```bash
docker-compose logs backend | grep -A 1000 "Tool result formatted:"
```

### Script Not Executable

Make the script executable:
```bash
chmod +x view_tool_responses.sh
```

## Output Directory

When using `--save`, responses are saved to:
```
tool_responses/
├── get_item_aspects_for_category_20251130_084530.json
├── search_items_20251130_084545.json
└── get_category_suggestions_20251130_084600.json
```

## Integration with Development Workflow

### During Development
```bash
# Terminal 1: Follow tool responses
./view_tool_responses.sh --follow

# Terminal 2: Run your tests or use the UI
# Tool responses will appear in Terminal 1
```

### Debugging Specific Tool
```bash
# Filter for specific tool and save responses
./view_tool_responses.sh --save --follow get_item_aspects
```

## Environment Variables

| Variable | Default | Description |
|-----------|---------|-------------|
| `LOG_FULL_TOOL_RESPONSES` | `false` | Enable full tool response logging |
| `TOOL_RESPONSE_LOG_LIMIT` | `200` | Character limit when full logging is disabled |

## Notes

- Full response logging can be very verbose and may impact performance
- Use `--save` to archive important tool responses for later analysis
- The script automatically pretty-prints JSON when possible
- Tool responses are saved with timestamps for easy tracking

