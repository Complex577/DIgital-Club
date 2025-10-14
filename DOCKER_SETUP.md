# Docker Setup Guide

This guide will help you run the Digital Club application using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed

## Quick Start

### 1. Build and Run the Application

```bash
docker-compose up -d
```

This command will:
- Build the Docker image
- Start the application container
- Run the app on port 5051

### 2. Access the Application

Open your browser and navigate to:
```
http://localhost:5051
```

### 3. Default Admin Credentials

- Email: `admin@digitalclub.kiut.ac.tz`
- Password: `admin123`

**Important:** Change these credentials after first login!

## Docker Commands

### Start the application
```bash
docker-compose up -d
```

### Stop the application
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Stop and remove everything (including volumes)
```bash
docker-compose down -v
```

## Environment Variables (Optional)

For production deployment, create a `.env` file in the project root:

```env
# Flask Configuration
SECRET_KEY=your-very-secure-secret-key

# Database
DATABASE_URL=sqlite:///digital_club_01.db

# Application Port
PORT=5051

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# SMS Configuration (Optional)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890
```

## Data Persistence

The following directories are mounted as volumes to persist data:

- `./instance` - SQLite database files
- `./app/static/uploads` - User uploaded files (profiles, gallery, digital IDs, blogs)

These folders will persist even if you restart or rebuild the container.

## Troubleshooting

### Port already in use
If port 5051 is already in use, you can change it in `docker-compose.yml`:

```yaml
ports:
  - "8080:5051"  # Use port 8080 instead
```

### Permission issues (Linux/Mac)
If you encounter permission issues with mounted volumes:

```bash
sudo chown -R $USER:$USER instance app/static/uploads
```

### View application logs
```bash
docker-compose logs -f web
```

### Enter the container shell
```bash
docker-compose exec web bash
```

### Rebuild without cache
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment

For production:

1. **Change the SECRET_KEY** in your `.env` file
2. **Update admin password** immediately after first login
3. **Configure email/SMS** if needed
4. **Use a reverse proxy** (nginx/Apache) with SSL
5. **Set up regular backups** of the `instance` and `uploads` folders

## Health Check

The application includes a health check that runs every 30 seconds. You can check the container health status:

```bash
docker-compose ps
```

A healthy container will show `healthy` in the status column.

