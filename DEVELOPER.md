# Komornicka 100 - Developer Guide

This guide provides detailed information for developers working on the Komornicka 100 application.

## Architecture Overview

The application consists of several components:

1. **Frontend**: Next.js application handling user interface and interactions
2. **Backend API**: FastAPI service providing API endpoints for the frontend
3. **Worker**: Background service for checking and validating Strava activities
4. **Database**: PostgreSQL database storing all application data
5. **PgAdmin**: Web interface for database management
6. **Mailpit**: Development mail server for testing emails

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Git
- Basic knowledge of React/Next.js, Python, and PostgreSQL

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/pablo-ross/komornicka100.git
   cd komornicka100
   ```

2. Run the setup script to prepare the environment:
   ```bash
   ./setup.sh
   ```

3. Edit the environment files with your settings:
   - `.env` - Main environment variables
   - `frontend/.env.local` - Frontend-specific variables

4. Add your GPX route files to the `gpx/` directory

5. Start the development environment:
   ```bash
   ./run.sh dev
   ```

### Development Workflow

#### Frontend Development (Next.js)

The frontend code is located in the `frontend/` directory:

- `pages/` - Next.js pages (routes)
- `components/` - Reusable React components
- `hooks/` - Custom React hooks
- `styles/` - CSS and styling files

To work on the frontend:

1. Make changes to the frontend code
2. The development server will automatically reload with your changes
3. Access the frontend at http://localhost:3000

#### Backend Development (FastAPI)

The backend code is located in the `backend/` directory:

- `app/main.py` - Application entry point
- `app/routers/` - API route definitions
- `app/services/` - Business logic and service functions
- `app/models.py` - Database models

To work on the backend:

1. Make changes to the backend code
2. The development server will automatically reload with your changes
3. Access the API at http://localhost:8000
4. API documentation is available at http://localhost:8000/docs

#### Worker Development

The worker code is located in the `worker/` directory:

- `worker.py` - Main worker script
- `verification.py` - Activity verification logic
- `services.py` - Service functions
- `models.py` - Database models

To test the worker:

1. Make changes to the worker code
2. Restart the worker container:
   ```bash
   docker compose restart worker
   ```
3. Check the logs for debugging:
   ```bash
   docker compose logs -f worker
   ```

#### Database Management

Database tables are created automatically on startup. To manage the database:

1. Access PgAdmin at http://localhost:5050
2. Login with credentials from your `.env` file
3. Connect to the database server

### Testing and Debugging

#### Email Testing

All emails sent by the application in development mode are captured by Mailpit:

1. Access the Mailpit interface at http://localhost:8025
2. View all sent emails, including HTML content and attachments

#### API Testing

You can test the API endpoints using the Swagger UI:

1. Access the Swagger UI at http://localhost:8000/docs
2. Try out API endpoints directly from the UI

#### Logs

View container logs for debugging:

```bash
# View logs for all containers
docker compose logs

# View logs for a specific container
docker compose logs -f frontend
docker compose logs -f api
docker compose logs -f worker
```

## Production Deployment

### Using Run Script

To deploy in production mode:

```bash
./run.sh prod
```

The script will prompt you for additional options, such as whether to include NGINX as a reverse proxy.

### Manual Production Deployment

Alternatively, you can manually deploy using Docker Compose:

   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

To force building images from scratch:

   ```bash
   docker compose -f docker-compose.prod.yml build --no-cache
   ```

### Production Considerations

1. **SSL Certificates**: For NGINX setup, place your SSL certificates in `nginx/ssl/`:
   - `cert.pem` - Certificate file
   - `key.pem` - Private key file

2. **Environment Variables**: Update production-specific variables in `.env`:
   - Set `ENVIRONMENT=production`
   - Configure real SMTP server settings
   - Set real Strava API credentials

3. **Database Backups**: Set up regular database backups:
   ```bash
   docker exec k100-db pg_dump -U <username> <dbname> > backup_$(date +%Y%m%d).sql
   ```

## Extending the Application

### Adding New API Endpoints

1. Create a new router file in `backend/app/routers/`
2. Define your endpoints using FastAPI decorators
3. Add the router to `backend/app/main.py`

### Adding New Frontend Pages

1. Create a new page file in `frontend/pages/`
2. Add the necessary components and logic
3. Update navigation if needed

### Modifying the Database Schema

1. Update the models in `backend/app/models.py`
2. The changes will be applied on the next application start

## Troubleshooting

### Common Issues

1. **Database connection issues**:
   - Check database credentials in `.env`
   - Ensure the database container is running

2. **Strava API issues**:
   - Verify your Strava API credentials
   - Check if the access token is refreshing properly

3. **Email sending failures**:
   - Check SMTP settings in `.env`
   - Use Mailpit for testing in development

### Getting Help

If you encounter issues not covered here, please:

1. Check the container logs for error messages
2. Review the documentation for the specific component
3. Consult with the project maintainers