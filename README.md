# Komornicka 100 - Bike Contest System

A web application for the **Komornicka 100** cycling contest that allows users to register, connect their Strava accounts, and have their cycling activities automatically verified against predefined routes.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/kmtb-contest.git
cd kmtb-contest
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Edit the configuration files:
```bash
nano .env                  # Main environment variables
nano frontend/.env.local   # Frontend-specific variables
```

4. Add your GPX route files to the `gpx/` directory

5. Start the application in development mode:
```bash
./run.sh dev
```

6. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - Mailpit (for email testing): http://localhost:8025
   - PgAdmin: http://localhost:5050

## Key Features

- User registration with email verification
- Strava integration for activity tracking
- Automatic verification of cycling activities against predefined routes
- Leaderboard showing top participants
- Background worker for processing activities
- Email notifications for verified activities

## System Architecture

- **Frontend**: Next.js application
- **Backend API**: FastAPI service
- **Worker**: Python service for background jobs
- **Database**: PostgreSQL for data storage
- **PgAdmin**: Web interface for database management
- **Mailpit**: Development mail server for testing

## Development vs. Production

### Development Mode

Start in development mode for local testing and development:

```bash
./run.sh dev
```

Development mode features:
- Hot reloading for frontend and backend code
- Mailpit for email testing
- Debug logging
- PgAdmin with direct access

### Production Mode

Deploy in production mode for live environments:

```bash
./run.sh prod
```

Production mode options:
- Basic mode: Direct access to services
- NGINX mode: With NGINX as reverse proxy, SSL support, and proper routing

## Documentation

Detailed documentation is available in the following files:

- [DEVELOPER.md](DEVELOPER.md) - Comprehensive guide for developers
- [STRAVA_SETUP.md](STRAVA_SETUP.md) - How to set up the Strava API integration
- [STRAVA_MOBILE.md](STRAVA_MOBILE.md) - Details on the mobile-friendly Strava authentication
- [GPX_VERIFICATION.md](GPX_VERIFICATION.md) - Details on the GPX route verification logic

## GPX Verification Logic

The system verifies cycling activities by:

1. Retrieving GPS data from Strava
2. Comparing it against predefined routes
3. Calculating a similarity score based on how closely the activity matches the route
4. Verifying activities that meet the similarity threshold and minimum distance requirements

Key verification parameters (configurable in `.env`):
- `ROUTE_SIMILARITY_THRESHOLD`: Percentage of points that must match (default: 80%)
- `GPS_MAX_DEVIATION_METERS`: Maximum allowed distance from route (default: 20 meters)
- `MIN_ACTIVITY_DISTANCE_KM`: Minimum activity distance (default: 100 km)

## Project Structure

```
kmtb-contest/
├── backend/             # FastAPI backend application
│   ├── app/             # Application code
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── models.py    # Database models
│   └── Dockerfile       # Docker configuration
├── frontend/            # Next.js frontend application
│   ├── components/      # React components
│   ├── pages/           # Next.js pages
│   ├── styles/          # CSS styles
│   └── hooks/           # React hooks
├── worker/              # Background worker
├── gpx/                 # GPX route files
├── nginx/               # NGINX configuration (for production)
├── docker-compose.yml           # Development Docker Compose
├── docker-compose.prod.yml      # Production Docker Compose
└── run.sh               # Helper script for running the application
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.