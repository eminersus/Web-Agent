#!/usr/bin/env python3
"""
Script to get eBay OAuth Application Access Token

This script helps you generate a valid OAuth token for the eBay Browse API.
Application tokens are suitable for general search operations.

Usage:
    python get_ebay_token.py

Requirements:
    - eBay App ID (Client ID)
    - eBay Cert ID (Client Secret)
    - requests library
"""

import requests
import base64
import sys
import os
from datetime import datetime, timedelta


def get_application_token(client_id, client_secret, environment='production'):
    """
    Get an OAuth 2.0 Application Access Token from eBay.
    
    Args:
        client_id: Your eBay App ID (Client ID)
        client_secret: Your eBay Cert ID (Client Secret)
        environment: 'production' or 'sandbox'
    
    Returns:
        dict with 'access_token' and 'expires_in' or None on error
    """
    # Determine the OAuth endpoint
    if environment == 'sandbox':
        token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    else:
        token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    
    # Encode credentials
    credentials = f"{client_id}:{client_secret}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Prepare headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_credentials}"
    }
    
    # Prepare data
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }
    
    print(f"\n🔄 Requesting token from eBay ({environment})...")
    print(f"   Endpoint: {token_url}")
    
    try:
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            expires_in = token_data.get('expires_in', 7200)
            expiry_time = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"\n✅ Success! Token obtained.")
            print(f"   Expires in: {expires_in} seconds ({expires_in/3600:.2f} hours)")
            print(f"   Expiry time: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return token_data
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return None
    
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        return None


def main():
    """Main function to get eBay token"""
    
    print("=" * 80)
    print("eBay OAuth Token Generator")
    print("=" * 80)
    
    # Check for environment variables first
    client_id = os.getenv('EBAY_CLIENT_ID')
    client_secret = os.getenv('EBAY_CLIENT_SECRET')
    environment = os.getenv('EBAY_ENV', 'production')
    
    # If not in environment, prompt user
    if not client_id:
        print("\n📝 Enter your eBay credentials:")
        print("   (Get these from: https://developer.ebay.com/my/keys)")
        print()
        client_id = input("   App ID (Client ID): ").strip()
    
    if not client_secret:
        client_secret = input("   Cert ID (Client Secret): ").strip()
    
    if not client_id or not client_secret:
        print("\n❌ Error: Both Client ID and Client Secret are required!")
        sys.exit(1)
    
    # Ask for environment
    print("\n🌍 Environment:")
    print("   1. Production (default)")
    print("   2. Sandbox")
    env_choice = input("   Choose (1 or 2): ").strip() or "1"
    environment = 'sandbox' if env_choice == '2' else 'production'
    
    # Get the token
    token_data = get_application_token(client_id, client_secret, environment)
    
    if token_data:
        access_token = token_data.get('access_token')
        
        print("\n" + "=" * 80)
        print("✨ Your OAuth Access Token:")
        print("=" * 80)
        print(f"\n{access_token}\n")
        print("=" * 80)
        
        print("\n📋 Add this to your .env file:")
        print("=" * 80)
        print(f"\nEBAY_APP_ID={access_token}")
        print(f"EBAY_USE_SANDBOX={'true' if environment == 'sandbox' else 'false'}\n")
        print("=" * 80)
        
        print("\n⚠️  Important Notes:")
        print("   • This token expires in ~2 hours")
        print("   • You'll need to regenerate it when it expires")
        print("   • For production use, implement automatic token refresh")
        print("   • Keep your Client ID and Secret secure!")
        
        print("\n💡 For automatic token refresh, consider:")
        print("   • Storing Client ID and Secret (not the token)")
        print("   • Implementing a token refresh mechanism")
        print("   • Using eBay's Python SDK for token management")
        
        # Option to save credentials
        print("\n💾 Save credentials for easy token refresh?")
        save = input("   Save Client ID and Secret to .env? (y/N): ").strip().lower()
        
        if save == 'y':
            env_file = '../../../.env'
            if os.path.exists(env_file):
                with open(env_file, 'a') as f:
                    f.write(f"\n# eBay OAuth Credentials (for token refresh)\n")
                    f.write(f"EBAY_CLIENT_ID={client_id}\n")
                    f.write(f"EBAY_CLIENT_SECRET={client_secret}\n")
                print(f"   ✅ Credentials saved to {env_file}")
            else:
                print(f"   ⚠️  .env file not found at {env_file}")
        
        return 0
    else:
        print("\n❌ Failed to obtain token. Please check your credentials and try again.")
        print("\n💡 Troubleshooting:")
        print("   • Verify your App ID and Cert ID at: https://developer.ebay.com/my/keys")
        print("   • Ensure you're using the correct environment (production vs sandbox)")
        print("   • Check that your application is set up for OAuth")
        return 1


if __name__ == "__main__":
    sys.exit(main())

