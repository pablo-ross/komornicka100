#!/usr/bin/env python
# backend/tests/test_strava_api.py
"""
Simple script to test the Strava API connection directly.
This helps diagnose issues with the Strava API without going through the frontend.

Usage:
    python test_strava_api.py <authorization_code>

You can get an authorization code by:
1. Going to https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000/strava-callback&response_type=code&scope=activity:read,profile:read_all
2. Authorizing the app
3. Copying the 'code' parameter from the redirected URL
"""

import sys
import asyncio
import json
import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

async def test_exchange_token(code: str, redirect_uri: str = None):
    """Test exchanging an authorization code for access token"""
    if redirect_uri is None:
        redirect_uri = f"{FRONTEND_URL}/strava-callback"
        
    print(f"\n--- Testing Strava Token Exchange ---")
    print(f"Authorization Code: {code[:10]}...")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Client ID: {STRAVA_CLIENT_ID}")
    
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    print(f"\nSending request to {url}")
    print(f"POST data: {json.dumps({k: v if k != 'client_secret' else '****' for k, v in data.items()}, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data=data)
            print(f"\nResponse status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"\nResponse data: {json.dumps(response_data, indent=2)}")
                
                if "access_token" in response_data:
                    print("\n✅ SUCCESS: Token exchange worked!")
                    
                    # Test getting athlete data with the token
                    await test_get_athlete(response_data["access_token"])
                else:
                    print("\n❌ ERROR: Token exchange failed - no access_token in response")
            except:
                print(f"\nNon-JSON response: {response.text[:500]}")
                print("\n❌ ERROR: Could not parse response as JSON")
    except Exception as e:
        print(f"\n❌ ERROR: Exception occurred: {str(e)}")

async def test_get_athlete(access_token: str):
    """Test getting athlete data with an access token"""
    print(f"\n--- Testing Getting Athlete Data ---")
    print(f"Access Token: {access_token[:10]}...")
    
    url = "https://www.strava.com/api/v3/athlete"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\nSending request to {url}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            print(f"\nResponse status code: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"\nAthlete data: {json.dumps(response_data, indent=2)}")
                print("\n✅ SUCCESS: Successfully retrieved athlete data!")
            except:
                print(f"\nNon-JSON response: {response.text[:500]}")
                print("\n❌ ERROR: Could not parse response as JSON")
    except Exception as e:
        print(f"\n❌ ERROR: Exception occurred: {str(e)}")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_strava_api.py <authorization_code> [redirect_uri]")
        return
    
    code = sys.argv[1]
    redirect_uri = sys.argv[2] if len(sys.argv) > 2 else None
    
    await test_exchange_token(code, redirect_uri)

if __name__ == "__main__":
    asyncio.run(main())