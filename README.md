# Komornicka 100 - Komorniki MTB Team Bike Contest System

This is a web application for the **Komornicka 100** that allows users to register, connect their Strava accounts, and have their bike activities automatically verified against a predefined route.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository
```bash
git clone https://github.com/pablo-ross/k100.git
cd k100
```

2. Create environment variables file
```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

3. Edit the `.env` file with your own settings
```bash
# Use your favorite editor
nano .env
nano frontend/.env.local
```

4. Start the application with Docker Compose
```bash
docker network create -d bridge k100
docker-compose up -d
```

5. The application should now be running at:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - Mailpit: http://localhost:8025
   - PgAdmin: http://localhost:5050

## Project Structure

- `backend/` - FastAPI application for the backend API
- `frontend/` - Next.js application for the frontend
- `worker/` - Python script for background jobs (checking Strava activities)
- `docker-compose.yml` - Docker Compose configuration
- `.env` - Environment variables

## Development

To run the project in development mode:

```bash
docker network create -d bridge k100
docker compose up -d
```

This will start all services and display logs in the console.

## Environment Variables

The following environment variables are used in the project:

- `RESTART` - Docker container restart policy
- `TZ` - Timezone for all services
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_DB` - PostgreSQL database name
- `POSTGRES_PORT` - PostgreSQL port
- `SMTP_SERVER` - SMTP server for sending emails
- `SMTP_PORT` - SMTP port
- `SMTP_USERNAME` - SMTP username
- `SMTP_PASSWORD` - SMTP password
- `SECRET_KEY` - Secret key for JWT token generation
- `STRAVA_CLIENT_ID` - Strava API client ID
- `STRAVA_CLIENT_SECRET` - Strava API client secret
- `PGADMIN_EMAIL` - PgAdmin login
- `PGADMIN_PASSWORD` - PgAdmin password
- `PGADMIN_LISTEN_PORT` - PgAdmin local port

## GPX verification logic

The current verification logic checks how closely a user's activity route matches the original source GPX route by comparing the GPS points. It doesn't specifically require the user to start and finish at the exact same points as the original route.

Here's how the verification works:

1. The system converts both the source GPX and the user's activity into sequences of GPS points
2. It simplifies these routes using the Douglas-Peucker algorithm to improve processing efficiency
3. For each point in the user's activity, it calculates the distance to the closest point on the source GPX route
4. It counts how many of these points are within the maximum deviation threshold (set to 20 meters by default)
5. The similarity score is the percentage of points that are within this threshold

The key parts of this logic are in the `verify_activity_against_source` and `calculate_similarity` functions in the GPX comparison code.

The system does not specifically check if:

- The starting point matches
- The ending point matches
- The direction of travel matches

It only checks overall route similarity based on the percentage of points that are close to the original route.

If you want to enforce starting and ending at specific points, you'd need to add additional checks to the verification logic. This could be done by:

1. Extracting the first and last points from both routes
2. Calculating the distance between the starting points and between the ending points
3. Requiring these distances to be within a certain threshold

## License

[MIT](LICENSE)