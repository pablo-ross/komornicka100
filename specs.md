You are the helpful assistant to create the web app using the incremental approach so I can test each component thoroughly before moving to the next dependency.

# Komornicka 100 System Specification

This is my specification for an app which will help organize a local bike contest where participants has to ride on specific routes (let's call them "source GPXs"). User's bike activites will be pulled from Strava and verified it they match with those stored in the system.

## Facts

- Name: Komornicka 100
- Main URL/domain: https://contest.komornikimtb.pl
- System email: contest@komornikimtb.pl (accessible via SMTP with typical settings like server, port, SSL, username, password)

## System Requirements

### Web App

1) URL: https://contest.komornikimtb.pl/register

Users need to fill a simple online registration form in order to register and provide the following data:
  - First name (string, mandatory)
  - Last name (string, mandatory)
  - Age (integer, mandatory, must be 18 or older)
  - Email address (validation needed, mandatory)
  - Checkbox "I have read the terms and regulations and I agree to follow these regulations" (mandatory)
  - Checkbox "I agree to the processing of my personal data by the contest organizer in order to participate in this contest" (mandatory)
  
2) URL: https://contest.komornikimtb.pl/email-verify/{uuid}/{some_random_token}

After successful validation and form submission, the user must verify their email address by clicking a one-time link in a system message sent to the provided email address.
  
3) URL: https://contest.komornikimtb.pl/strava-auth/{uuid}/{some_random_token}

After positive email validation, the user needs to grant access to their Strava account using the Strava API authentication process. This app needs access only to public bike rides and some basic profile information from Strava.

4) URL: https://contest.komornikimtb.pl/thank-you

After successfully granting Strava access, the user receives a confirmation message on screen plus a confirmation email that they are registered for the contest. The content of this email is not important now and can be adjusted later.

### Background Jobs

1. With all data saved in PostgreSQL, there should be a script that runs automatically via cron every 2 hours from 06:00 to 22:00 (Europe/Warsaw timezone).
2. This script needs to loop through all active users and check whether there are any new bike activities since the last check.
3. If new activities exist, each should be pulled from Strava. Then, verify if the activity stream (GPX) matches or closely resembles those saved as "source GPXs". Consider allowing for some GPS deviation (10-20m) as GPS accuracy varies.
4. Additional check: The length of each activity must be at least 100 kilometers (as the predefined "Source GPX" route is exactly 100 km).
5. If the user's path is approved, it should be stored in PostgreSQL as an activity related to that specific user. The user will also receive an email that their activity (name, date) has been approved by the system.
6. With each script execution, update another table in PostgreSQL storing active users and their number of approved activities so far.

## Additional Information

### General:

a) All data must be stored in a PostgreSQL database.
b) Each action like registration, unregistration, Strava authorization, activity approval, etc. should be logged in a separate table for administration purposes.
c) Each registered user needs a unique identifier (UUID).
d) There should be a link available (https://contest.komornikimtb.pl/unregister) allowing users to unregister and delete all their data. This simple form needs just two fields: email (mandatory) and checkbox (mandatory) "I confirm I want to delete my account". After form submission, the email is checked in the PostgreSQL database to verify if this user exists and is active. If so, an email is sent to verify their decision to sign out and delete data. This email should contain a one-time link (https://contest.komornikimtb.pl/delete/{uuid}/{some_random_token}) which, when clicked, removes all user data and sends a final email confirming removal from the system and welcoming them to join again.
e) The entire solution must be developed as Docker containers with docker-compose.yml files for easier management and potential server migration.
f) Preferred technologies are: Python, Next.js, PostgreSQL. A separate Python API should be implemented for the Next.js web app to call.

### Preferred Database Design:

- users - core user information
- activities - verified rides
- activity_attempts - all activities checked (for analytics)
- audit_log - system events
- tokens - for storing Strava OAuth tokens

### Authentication Management:

- Implement refresh token handling for Strava (tokens expire)
- Add session management for web app users

### Error Handling:

- Add fallback mechanisms if Strava API is unavailable
- Implement retry logic for failed background jobs

### Architecture Recommendations

#### Frontend: Next.js application with:
  - Public pages (registration, verification)
  - Simple public leaderboard with top 20 riders with the highest numbers of approved activities, sorted desc
  - Simple terms & regulations page with some Lorem Ipsum content
  - No authenticated user dashboard is required (for now)
  - No admin section is required (for now)
  - Use .fronted/.env.local file for page titles, urls and so on

#### Backend API: Python FastAPI or Flask service:

  - User management endpoints
  - Strava integration logic
  - Route verification algorithms
  - Use ./.env file to get all needed variables

#### Workers: Separate Python service for background jobs:

  - Activity polling from Strava
  - Route verification processing
  - Use ./.env file to get all needed variables

#### Database: PostgreSQL with proper indexing on frequently queried fields

#### Docker Setup:

  - Separate containers for web, API, workers, database, pgAdmin
  - Nginx as a reverse proxy
  - Use volumes for persistent data

## Project Structure

- `backend/` - FastAPI application for the backend API
- `frontend/` - Next.js application for the frontend
- `worker/` - Python script for background jobs (checking Strava activities)
- `docker-compose.yml` - Docker Compose configuration
- `.env` - Environment variables

