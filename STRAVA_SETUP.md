# Setting Up Strava API Integration

This guide explains how to set up the Strava API integration for the Komornicka 100 application.

## Getting Strava API Credentials

### Create a Strava API Application

1. Log in to your Strava account at [strava.com](https://www.strava.com/)

2. Go to the [Strava API settings page](https://www.strava.com/settings/api)

3. Fill in the application details:
   - **Application Name**: Komornicka 100
   - **Category**: Choose "Other"
   - **Website**: Your application's URL (e.g., https://your-domain.com)
   - **Authorization Callback Domain**: Your application's domain (e.g., your-domain.com)
   - **Description**: A brief description of your application

4. Read and agree to the Strava API agreement, then click "Create"

5. After creating the application, you'll see your **Client ID** and **Client Secret**
   - **Client ID**: A number visible on the page
   - **Client Secret**: Click "Show" to view it

6. Save both the Client ID and Client Secret as you'll need them for configuration

### Configure Your Application

1. Update your `.env` file with the Strava API credentials:
   ```
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   ```

2. Update your `frontend/.env.local` file to include the Strava client ID (if needed):
   ```
   NEXT_PUBLIC_STRAVA_CLIENT_ID=your_client_id
   ```

## Applying for Strava API Verification

**Important:** By default, Strava API applications are limited to connecting with only one athlete (the application creator). For a contest application that needs to connect to multiple athletes, you must apply for verification to increase your app's capacity.

### Verification Process

1. Develop your application with basic functionality
2. Test thoroughly with your own Strava account
3. Apply for verification through the [Strava Developer Program](https://developers.strava.com/)
4. In your application, explain:
   - The purpose of your application
   - Expected number of users
   - How you'll use the Strava data
   - Privacy and data protection measures

### Current API Limits After Verification

For this application, Strava has approved the following limits:

- **Overall Rate Limit**: 600 requests every 15 minutes, up to 6,000 requests per day
- **Read Rate Limit**: 300 requests every 15 minutes, up to 3,000 requests per day
- **Athlete Capacity**: 999 athletes can connect to the application

Make sure your application handles these limits appropriately:
- Implement rate limiting in your API calls
- Add retry logic with exponential backoff for failed requests
- Schedule background jobs to distribute API calls evenly

## Setting Up Strava Webhook (Optional)

For real-time activity notifications, you can set up a Strava webhook:

1. Ensure your application is publicly accessible over HTTPS

2. Create a subscription by sending a POST request to Strava:
   ```bash
   curl -X POST https://www.strava.com/api/v3/push_subscriptions \
     -F client_id=YOUR_CLIENT_ID \
     -F client_secret=YOUR_CLIENT_SECRET \
     -F callback_url=https://your-domain.com/api/strava/webhook \
     -F verify_token=VERIFICATION_TOKEN
   ```

3. Implement the webhook verification endpoint in your FastAPI application:
   ```python
   @router.get("/strava/webhook")
   async def strava_webhook_verification(
       request: Request,
       hub_mode: str = Query(None),
       hub_verify_token: str = Query(None),
       hub_challenge: str = Query(None)
   ):
       """Verify Strava webhook subscription"""
       if hub_mode == "subscribe" and hub_verify_token == "VERIFICATION_TOKEN":
           return {"hub.challenge": hub_challenge}
       raise HTTPException(status_code=403)
   ```

4. Implement the webhook event handler for activity updates:
   ```python
   @router.post("/strava/webhook")
   async def strava_webhook(
       request: Request,
       background_tasks: BackgroundTasks
   ):
       """Handle Strava webhook events"""
       data = await request.json()
       if data["object_type"] == "activity" and data["aspect_type"] == "create":
           # Process the new activity
           background_tasks.add_task(
               process_new_activity, data["owner_id"], data["object_id"]
           )
       return {"status": "ok"}
   ```

## Testing the Strava Integration

### Development Testing

1. Start the application in development mode:
   ```bash
   ./run.sh dev
   ```

2. Register a new user through the application

3. Complete the email verification step

4. On the Strava authorization page, you can verify that:
   - You're redirected to Strava's authorization page
   - After authorization, you're redirected back to your application
   - The Strava connection status is displayed correctly

### Simulating Activity Creation

For testing without creating actual Strava activities:

1. Create a test endpoint in your FastAPI application:
   ```python
   @router.get("/strava/test-activity/{user_id}")
   async def test_activity(
       user_id: str,
       db: Session = Depends(get_db)
   ):
       """Test activity verification"""
       # This would normally be called by the background worker
       result = await verify_strava_activity(db, user_id, "test_activity_id")
       return result
   ```

2. Create a sample GPX file and place it in your `gpx/` directory

3. Create a test script to simulate an activity:
   ```python
   import httpx
   import asyncio

   async def main():
       async with httpx.AsyncClient() as client:
           response = await client.get(
               "http://localhost:8000/api/strava/test-activity/your_user_id"
           )
           print(response.json())

   if __name__ == "__main__":
       asyncio.run(main())
   ```

## Troubleshooting

### Common Issues

1. **Authorization Error**:
   - Check that your Client ID and Client Secret are correct
   - Ensure your callback URL is properly configured in the Strava API settings

2. **Token Refresh Failures**:
   - Verify that your refresh token logic is correctly implemented
   - Check the expiration time of the access token

3. **Activity Retrieval Issues**:
   - Ensure the user has granted the correct permissions
   - Check that the activity type is set to "Ride"

### Debugging Strava API Calls

For better debugging:

1. Enable verbose logging in your FastAPI application:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Log all API requests and responses:
   ```python
   async with httpx.AsyncClient() as client:
       response = await client.get(url, headers=headers)
       logging.debug(f"Request URL: {url}")
       logging.debug(f"Request Headers: {headers}")
       logging.debug(f"Response Status: {response.status_code}")
       logging.debug(f"Response Body: {response.text}")
   ```

## Strava API Rate Limits

Be aware of Strava API rate limits (after verification):

- 600 requests per 15 minutes
- 6,000 requests per day
- Read-specific limits: 300 requests per 15 minutes, 3,000 requests per day
- Daily limits reset at midnight UTC

Implement proper rate limiting and caching in your application to avoid hitting these limits.