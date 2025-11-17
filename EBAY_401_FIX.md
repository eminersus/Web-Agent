# eBay 401 Error - Quick Fix Guide

## The Problem
You're getting a 401 "Invalid access token" error because OAuth tokens from eBay expire after ~2 hours.

## The Solution (2 Minutes)

### Step 1: Get eBay Credentials
Visit: https://developer.ebay.com/my/keys

Copy:
- **App ID (Client ID)** 
- **Cert ID (Client Secret)**

### Step 2: Update Your .env File
```bash
# Replace the eBay section with:
EBAY_CLIENT_ID=Your-AppID-Here
EBAY_CLIENT_SECRET=Your-CertID-Here
EBAY_USE_SANDBOX=false
```

**Important:** Remove or clear the old `EBAY_APP_ID` line.

### Step 3: Restart
```bash
docker-compose restart mcp-server
```

**Done!** The system now automatically refreshes tokens. ✨

---

## Alternative: Generate Token Manually
```bash
cd mcp-server/api/ebay
python get_ebay_token.py
```

**Note:** Manual tokens expire in ~2 hours. Use automatic refresh for production.

---

## Verify It Works
```bash
# Check logs
docker-compose logs -f mcp-server

# Look for:
# "Token refreshed successfully. Expires in 7200 seconds"
```

---

## Full Documentation
- **Troubleshooting:** `mcp-server/api/ebay/TROUBLESHOOTING.md`
- **API Docs:** `mcp-server/api/ebay/README.md`
- **Quick Reference:** `mcp-server/api/ebay/QUICK_REFERENCE.md`

---

## What Was Fixed?
✅ Automatic OAuth token generation and refresh
✅ Auto-retry on 401 errors
✅ Token expiration handling
✅ Better error messages with solutions
✅ Interactive token generator tool

No more manual token management needed! 🎉

