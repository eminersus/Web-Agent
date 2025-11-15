# Network Access Guide

## Accessing the Application from Other Computers on Your Home Network

This guide explains how to access your Web Agent application from any device on your local network (phones, tablets, other computers).

---

## Quick Start

### 1. Find Your Host Machine's IP Address

**On macOS:**
```bash
# Option 1: Simple
ipconfig getifaddr en0    # WiFi
ipconfig getifaddr en1    # Ethernet

# Option 2: Detailed
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**On Linux:**
```bash
hostname -I
# or
ip addr show | grep "inet " | grep -v 127.0.0.1
```

**On Windows:**
```cmd
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

Example output: `192.168.1.100`

### 2. Update Your .env File

Create or update `.env` file in the project root:

```bash
# If .env doesn't exist, create it from template
cp env.template .env

# Edit the file
nano .env  # or use your preferred editor
```

Set CORS to allow all origins:
```bash
CORS_ALLOW_ORIGINS=*
```

**Note:** For production, specify exact IPs instead of `*`:
```bash
CORS_ALLOW_ORIGINS=http://192.168.1.100:8080,http://192.168.1.101:8080
```

### 3. Restart Your Services

```bash
./dev.sh restart

# or
docker-compose restart
```

### 4. Access from Other Devices

On any device connected to the same WiFi/network:

**Frontend:**
```
http://192.168.1.100:8080
```
(Replace `192.168.1.100` with your host machine's IP)

**Backend API:**
```
http://192.168.1.100:8000
```

---

## How It Works

### Changes Made

#### 1. **Frontend - Dynamic API URL** (`frontend/app.js`)

Before:
```javascript
const API_BASE = "http://localhost:8000";  // ❌ Only works locally
```

After:
```javascript
const API_BASE = (() => {
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
})();
// ✅ Works from any machine
```

**What this does:**
- When you access `http://localhost:8080` → API is `http://localhost:8000`
- When you access `http://192.168.1.100:8080` → API is `http://192.168.1.100:8000`
- Frontend automatically uses the correct backend URL!

#### 2. **Backend - CORS Settings** (`.env`)

```bash
CORS_ALLOW_ORIGINS=*
```

This allows the backend to accept requests from any origin on your network.

#### 3. **Docker - Already Configured!**

The services are already binding to all network interfaces:
- Frontend: `0.0.0.0:8080` → Port 8080 on all IPs
- Backend: `0.0.0.0:8000` → Port 8000 on all IPs
- Ollama: `0.0.0.0:11434` → Port 11434 on all IPs

---

## Testing Network Access

### From Host Machine

Test that services are accessible:
```bash
# Get your IP
export HOST_IP=$(ipconfig getifaddr en0)

# Test frontend
curl -I http://$HOST_IP:8080

# Test backend
curl http://$HOST_IP:8000/api/health

# Test LLM
curl http://$HOST_IP:11434/api/version
```

### From Another Device

1. **Connect to the same WiFi network**
2. **Open browser and navigate to:** `http://192.168.1.100:8080` (use your host IP)
3. **You should see the chat interface**
4. **Try sending a message** - it should work!

### Troubleshooting

#### Can't Access from Other Devices?

**1. Check Firewall (macOS)**
```bash
# Temporarily disable firewall to test
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off

# Re-enable after testing
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
```

Or allow Docker in System Preferences → Security & Privacy → Firewall → Firewall Options → Allow Docker.

**2. Check Firewall (Linux)**
```bash
# Allow ports 8000 and 8080
sudo ufw allow 8000
sudo ufw allow 8080
sudo ufw reload
```

**3. Check Firewall (Windows)**
```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "Web Agent Frontend" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Web Agent Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**4. Verify Docker is Listening**
```bash
# Should show 0.0.0.0:8080 and 0.0.0.0:8000
netstat -an | grep LISTEN | grep -E '8080|8000'

# or
lsof -i :8080
lsof -i :8000
```

**5. Check Same Network**
```bash
# On both devices, run:
# macOS/Linux:
ifconfig | grep "inet "

# Windows:
ipconfig

# Ensure both devices have IPs in the same subnet (e.g., 192.168.1.x)
```

---

## Mobile Access

### On Your Phone/Tablet

1. **Connect to your home WiFi**
2. **Open browser (Safari, Chrome, etc.)**
3. **Navigate to:** `http://192.168.1.100:8080`
4. **Chat works perfectly on mobile!** 📱

### For Better Mobile Experience

Add to `frontend/index.html` (already has viewport meta):
```html
<meta name="viewport" content="width=device-width, initial-scale=1" />
```

This ensures the UI scales properly on mobile devices.

---

## Production Considerations

### For Home Network

Current setup is perfect for home use:
- ✅ Dynamic URL detection
- ✅ CORS allowing local network
- ✅ Easy access from any device

### For Public Access (Advanced)

If you want to access from outside your home network:

1. **Use Dynamic DNS** (e.g., DuckDNS, No-IP)
2. **Port Forwarding** on your router:
   - Forward port 8080 → your machine's 8080 (frontend)
   - Forward port 8000 → your machine's 8000 (backend)
3. **Security:** Add authentication, use HTTPS, restrict CORS
4. **Alternative:** Use Tailscale, ZeroTier, or Cloudflare Tunnel

---

## Advanced: Custom API URL

If you want to use a custom backend URL (different port, different machine):

### Option 1: Meta Tag Override

In `frontend/index.html`, uncomment and set:
```html
<meta name="api-url" content="http://192.168.1.200:8000" />
```

### Option 2: Environment Variable (Build Time)

For production builds, you could use a build-time environment variable, but since this is a static frontend, the meta tag approach is simpler.

---

## Network Diagram

```
┌─────────────────────────────────────────────────┐
│            Home WiFi Network (192.168.1.x)      │
│                                                 │
│  ┌──────────────────────────────┐              │
│  │  Host Machine (192.168.1.100)│              │
│  │  - Docker Containers         │              │
│  │    • Frontend :8080          │              │
│  │    • Backend  :8000          │              │
│  │    • Ollama   :11434         │              │
│  └────────────┬─────────────────┘              │
│               │                                 │
│               │ All accessible via host IP     │
│               │                                 │
│  ┌────────────┴────────────┐                   │
│  │                          │                   │
│  ┌──────────────┐  ┌───────────────┐           │
│  │ Laptop       │  │ Phone         │           │
│  │ 192.168.1.10 │  │ 192.168.1.15  │           │
│  │              │  │               │           │
│  │ Access:      │  │ Access:       │           │
│  │ http://192.  │  │ http://192.   │           │
│  │ 168.1.100:   │  │ 168.1.100:    │           │
│  │ 8080         │  │ 8080          │           │
│  └──────────────┘  └───────────────┘           │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Summary

✅ **What's Already Done:**
- Frontend dynamically detects hostname
- Backend accepts CORS from all origins
- Docker binds to 0.0.0.0 (all interfaces)

✅ **What You Need to Do:**
1. Find your host machine's IP address
2. Update `.env` with `CORS_ALLOW_ORIGINS=*`
3. Restart services: `./dev.sh restart`
4. Access from other devices: `http://YOUR_IP:8080`

✅ **Works On:**
- Other computers on your network
- Phones and tablets
- Any device with a browser on the same WiFi

---

**Enjoy chatting from anywhere in your home! 🏠📱💻**

