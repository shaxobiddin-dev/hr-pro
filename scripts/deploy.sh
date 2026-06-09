#!/bin/bash
# HR-Pro Deployment Script
# Usage: ./scripts/deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

echo "========================================"
echo "HR-Pro Deployment - $ENVIRONMENT"
echo "========================================"

# Check if .env.prod exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found!"
    echo "Please copy .env.prod.example to .env.prod and configure it."
    exit 1
fi

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo "Pulling latest code..."
    git pull origin main
fi

# Build new images
echo "Building Docker images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down

# Start new containers
echo "Starting new containers..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for database to be ready
echo "Waiting for database..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose -f $COMPOSE_FILE exec -T web python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker-compose -f $COMPOSE_FILE exec -T web python manage.py collectstatic --noinput

# Initialize data (if first deployment)
echo "Initializing default data..."
docker-compose -f $COMPOSE_FILE exec -T web python manage.py init_hr_data || true
docker-compose -f $COMPOSE_FILE exec -T web python manage.py init_payroll_data || true

# Health check
echo "Performing health check..."
sleep 5
curl -f http://localhost/health/ || echo "Warning: Health check failed"

echo "========================================"
echo "Deployment completed!"
echo "========================================"
docker-compose -f $COMPOSE_FILE ps
