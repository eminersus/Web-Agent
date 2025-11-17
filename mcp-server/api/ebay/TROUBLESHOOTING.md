# eBay Browse API - Troubleshooting 401 Error

## Problem: Invalid Access Token (401 Error)

You're getting this error because OAuth tokens from eBay **expire after approximately 2 hours**. Your token has expired and needs to be refreshed.

```json
{
  "error": "eBay API returned status 401",
  "status_code": 401,
  "details": {
    "errors": [{
      "errorId": 1001,
      "domain": "OAuth",
      "message": "Invalid access token"
    }]
  }
}
```

## Solution: Choose One of These Options

### Option 1: Use Automatic Token Refresh (RECOMMENDED) ⭐

This option automatically generates and refreshes tokens without manual intervention.

**Step 1: Get Your Credentials**
1. Go to: https://developer.ebay.com/my/keys
2. Sign in to your eBay Developer account
3. Find or create an application
4. Copy your **App ID (Client ID)** and **Cert ID (Client Secret)**

**Step 2: Update Your .env File**

Remove or comment out the old `EBAY_APP_ID` and add:

```bash
# eBay API Configuration - Option 2 (Automatic Refresh)
EBAY_CLIENT_ID=YourAppID_Here
EBAY_CLIENT_SECRET=YourCertID_Here
EBAY_USE_SANDBOX=false
```

**Step 3: Restart the MCP Server**

```bash
docker-compose restart mcp-server
```

That's it! The server will now automatically:
- Generate fresh OAuth tokens
- Refresh tokens before they expire
- Retry failed requests with new tokens

---

### Option 2: Manual Token Generation

If you prefer to manually manage tokens (not recommended for production):

**Step 1: Run the Token Generator**

```bash
cd mcp-server/api/ebay
python get_ebay_token.py
```

**Step 2: Follow the Prompts**

The script will ask for:
- Your **App ID (Client ID)**
- Your **Cert ID (Client Secret)**  
- Environment (Production or Sandbox)

**Step 3: Copy the Generated Token**

The script will output a fresh OAuth token that looks like:

```
v^1.1#i^1#r^0#p^3#I^3#t^H4sIAAAAAAAA...
```

**Step 4: Update Your .env File**

```bash
EBAY_APP_ID=v^1.1#i^1#r^0#p^3#I^3#t^H4sIAAAAAAAA...
EBAY_USE_SANDBOX=false
```

**Step 5: Restart the MCP Server**

```bash
docker-compose restart mcp-server
```

**⚠️ Important:** You'll need to repeat this process every ~2 hours when the token expires.

---

## How to Get eBay Credentials

###1. Visit eBay Developers
Go to: https://developer.ebay.com/

### 2. Sign In or Create Account
- Use your eBay account
- Accept the developer agreement

### 3. Create an Application
- Go to "My Account" → "Application Keys"
- Click "Create an Application Key Set"
- Fill in application details

### 4. Get Your Keys
You'll receive:
- **App ID (Client ID)**: Used for automatic token refresh
- **Cert ID (Client Secret)**: Used for automatic token refresh
- **OAuth tokens**: Can be manually generated

### 5. Production vs. Sandbox
- **Sandbox**: For testing (use sandbox credentials and set `EBAY_USE_SANDBOX=true`)
- **Production**: For real data (use production credentials and set `EBAY_USE_SANDBOX=false`)

---

## Complete .env Configuration Examples

### Example 1: Automatic Refresh (Recommended)

```bash
# eBay API Configuration
EBAY_CLIENT_ID=MyAppNam-WebAgent-PRD-1234567890-abcdefgh
EBAY_CLIENT_SECRET=PRD-1234567890abcd-ef123456
EBAY_USE_SANDBOX=false

# Optional: Leave blank or remove
# EBAY_APP_ID=
```

### Example 2: Manual Token

```bash
# eBay API Configuration
EBAY_APP_ID=v^1.1#i^1#r^0#p^3#I^3#t^H4sIAAAAAAAA/+1Za2wUVRS...
EBAY_USE_SANDBOX=false

# Optional: Leave blank or remove
# EBAY_CLIENT_ID=
# EBAY_CLIENT_SECRET=
```

### Example 3: Sandbox Testing

```bash
# eBay API Configuration (Sandbox)
EBAY_CLIENT_ID=MyAppNam-WebAgent-SBX-1234567890-abcdefgh
EBAY_CLIENT_SECRET=SBX-1234567890abcd-ef123456
EBAY_USE_SANDBOX=true
```

---

## Testing Your Configuration

After updating your configuration:

### 1. Restart the Server

```bash
docker-compose restart mcp-server
```

### 2. Check the Logs

```bash
docker-compose logs -f mcp-server
```

Look for:
```
INFO - eBay Browse API initialized
INFO - Refreshing eBay OAuth token...
INFO - Token refreshed successfully. Expires in 7200 seconds
```

### 3. Test a Search

Try searching for items:

```json
{
  "tool": "search_items",
  "params": {
    "q": "iPhone",
    "limit": 5
  }
}
```

If successful, you'll see:
```json
{
  "total": 12345,
  "itemSummaries": [...]
}
```

---

## Common Issues

### Issue: "Cannot refresh token: EBAY_CLIENT_ID or EBAY_CLIENT_SECRET not set"

**Solution**: You haven't set the credentials for automatic refresh. Either:
- Add `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` to your .env file, OR
- Use `EBAY_APP_ID` with a manually generated token

### Issue: "Failed to obtain eBay access token using client credentials"

**Possible causes:**
1. **Wrong credentials**: Double-check your App ID and Cert ID
2. **Wrong environment**: Verify production vs. sandbox credentials match `EBAY_USE_SANDBOX` setting
3. **Invalid application**: Ensure your eBay application is active and properly configured

**Solution**: 
- Verify credentials at https://developer.ebay.com/my/keys
- Ensure you're using the correct environment (production/sandbox)
- Check that your application has OAuth enabled

### Issue: Still getting 401 after updating credentials

**Solution:**
1. Completely remove the old `EBAY_APP_ID` line from .env
2. Restart the entire Docker stack:
   ```bash
   docker-compose down
   docker-compose up -d
   ```
3. Check logs: `docker-compose logs mcp-server`

### Issue: "Token expires after ~2 hours"

**Solution:** Use **Option 1** (Automatic Token Refresh) instead of manual tokens. This handles token expiration automatically.

---

## Security Best Practices

1. **Never commit credentials to Git**
   - Your `.env` file should be in `.gitignore`
   - Never share your tokens or credentials publicly

2. **Use environment variables**
   - Keep credentials in `.env` file
   - Don't hardcode credentials in source code

3. **Rotate credentials regularly**
   - Change credentials if compromised
   - Use different credentials for different environments

4. **Use sandbox for testing**
   - Test with `EBAY_USE_SANDBOX=true` first
   - Switch to production only when ready

---

## Getting Help

### eBay Developer Support
- Documentation: https://developer.ebay.com/api-docs/buy/browse/overview.html
- Forums: https://developer.ebay.com/support/forums
- Contact: https://developer.ebay.com/support/contact

### Token Generation Script
```bash
cd mcp-server/api/ebay
python get_ebay_token.py --help
```

### Check Server Logs
```bash
# All logs
docker-compose logs mcp-server

# Follow logs in real-time
docker-compose logs -f mcp-server

# Last 100 lines
docker-compose logs --tail=100 mcp-server
```

---

## Quick Checklist

- [ ] I have eBay Developer credentials
- [ ] I've added `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` to .env
- [ ] I've set `EBAY_USE_SANDBOX` to the correct environment
- [ ] I've restarted the MCP server
- [ ] I've checked the logs for token refresh success
- [ ] I've tested a simple search
- [ ] The 401 error is resolved!

---

## Summary

**Best Practice:**
Use automatic token refresh (Option 1) with `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`. This eliminates the need to manually refresh tokens every 2 hours.

**Your .env should look like:**
```bash
EBAY_CLIENT_ID=your_app_id_here
EBAY_CLIENT_SECRET=your_cert_id_here
EBAY_USE_SANDBOX=false
```

**Then restart:**
```bash
docker-compose restart mcp-server
```

That's it! The system will handle token management automatically. 🎉

