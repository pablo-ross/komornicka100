# Debugging Guide: Fixing the Strava Authentication Freeze

You're experiencing an issue where the app freezes at "Connecting to Strava" after granting Strava access. This guide will help you diagnose and fix the problem using the debugging tools I've provided.

## Step 1: Add the debugging components

1. Add the `DebugPanel` component:
   - Create `frontend/components/DebugPanel.tsx` with the code from the "Debugging Components" artifact.

2. Update the Strava auth page:
   - Replace the content of `frontend/pages/strava-auth/[userId]/[token].tsx` with the code from the "Strava Auth Debug Modification" artifact.

3. Enhance backend logging:
   - Create `backend/app/middleware/debug_middleware.py` with the code from the "Strava API Debug Middleware" artifact.
   - Update `backend/app/services/strava_service.py` with the code from the "Enhanced Strava Service with Debug Logging" artifact.
   - Update `backend/app/routers/strava.py` with the code from the "Enhanced Strava Router with Debug Logging" artifact.

4. Add the debug middleware to your FastAPI application:
   - Open `backend/app/main.py`
   - Add these lines near the top:
     ```python
     from .middleware.debug_middleware import add_debug_middleware
     ```
   - Add this line after creating the FastAPI app (after `app = FastAPI(...)`):
     ```python
     add_debug_middleware(app)
     ```

## Step 2: Test the Strava API directly

1. Create `backend/tests/test_strava_api.py` with the code from the "Strava API Test Script" artifact.

2. Make the script executable:
   ```bash
   chmod +x backend/tests/test_strava_api.py
   ```

3. Get a fresh Strava authorization code by:
   - Going to `https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000/strava-callback&response_type=code&scope=activity:read,profile:read_all`
   - Authorizing the app
   - Copying the `code` parameter from the redirected URL

4. Run the test script:
   ```bash
   cd backend
   python tests/test_strava_api.py YOUR_AUTHORIZATION_CODE
   ```

5. If you want to test with the exact same redirect URI that your app uses:
   ```bash
   python tests/test_strava_api.py YOUR_AUTHORIZATION_CODE "http://localhost:3000/strava-auth/YOUR_USER_ID/YOUR_TOKEN?frontend_redirect=true"
   ```

## Step 3: Check for common issues

Based on the debugging output, look for these common problems:

### 1. Client ID / Client Secret mismatch

Check if your Strava API credentials are correct:
- Verify that `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` in your `.env` file match what's on your Strava API settings page.
- Make sure the client ID used in frontend matches the backend client ID.

### 2. Redirect URI issues

Strava requires the exact same redirect URI used for authorization and token exchange:
- The URI in your `.env` file's `FRONTEND_URL` setting should match what's registered in Strava.
- Check if there are any extra or missing query parameters in the redirect URI.
- Verify that your Strava app's "Authorization Callback Domain" includes your development domain.

### 3. Code exchange timing out

The authorization code might expire if not used quickly:
- Look for timeout errors in the backend logs.
- Check if there are any network connectivity issues between your backend and Strava.

### 4. Database issues

The token might not be getting saved correctly:
- Check for database connection errors in the logs.
- Verify the foreign key references and data types in your database schema.

## Step 4: Common fixes

Based on what you discover, here are the most likely fixes:

### Fix 1: Update Strava API credentials

1. Go to https://www.strava.com/settings/api
2. Copy your Client ID and Client Secret
3. Update in your `.env` file:
   ```
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   ```

### Fix 2: Fix the redirect URI handling

The most common issue is with redirect URI mismatch. Make sure:

1. The `FRONTEND_URL` in your `.env` file is set correctly (e.g., `http://localhost:3000` for local development)
2. The callback domain in your Strava API settings includes your domain (e.g., `localhost` for local development)
3. The frontend is correctly passing the `frontend_redirect=true` parameter

Here's a fix for redirect URI handling in `strava_service.py`:

```python
async def exchange_authorization_code(code: str, redirect_uri: str) -> Dict[str, Any]:
    # Remove any state parameters from redirect_uri
    # Strava can be sensitive to exact redirect URI matching
    if "&state=" in redirect_uri:
        redirect_uri = redirect_uri.split("&state=")[0]
    
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": settings.STRAVA_CLIENT_ID,
        "client_secret": settings.STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    # Rest of the function...
```

### Fix 3: Improve error handling in the frontend

Update the Strava auth page to better handle errors and not freeze:

```jsx
// In frontend/pages/strava-auth/[userId]/[token].tsx

// Add this timeout to prevent infinite loading
useEffect(() => {
  if (isConnecting) {
    // Add a timeout to prevent infinite loading
    const timer = setTimeout(() => {
      setIsConnecting(false);
      setErrorMessage("Connection timed out. Please try again.");
    }, 15000); // 15 seconds timeout
    
    return () => clearTimeout(timer);
  }
}, [isConnecting]);
```

### Fix 4: Database transaction handling

Ensure proper transaction handling in your Strava router:

```python
# In backend/app/routers/strava.py

# Wrap database operations in a try-except-finally block
try:
    # Database operations...
    db.commit()
except Exception as e:
    db.rollback()
    logger.error(f"Database error: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
```

## Testing Your Fix

After implementing the fixes:

1. Restart both frontend and backend services:
   ```bash
   docker compose restart frontend api
   ```

2. Clear your browser's cookies and cache for your development domain

3. Go through the registration and email verification process again

4. Try connecting to Strava and check the debug output in:
   - Browser console
   - API logs
   - Debug panel in the UI

Let me know if you encounter any additional issues during this process!