# Blockchain Heatmap App - Docker Commands

.PHONY: help up down build rebuild logs restart frontend-logs backend-logs clean

# Default target
help:
	@echo "Available commands:"
	@echo "  up          - Start all services"
	@echo "  down        - Stop all services"
	@echo "  build       - Build all services"
	@echo "  rebuild     - Rebuild and restart all services"
	@echo "  logs        - Show logs from all services"
	@echo "  frontend-logs - Show frontend logs"
	@echo "  backend-logs  - Show backend logs"
	@echo "  restart     - Restart all services"
	@echo "  clean       - Stop services and remove containers/images"

# Start all services
up:
	docker-compose up -d
	@echo "Services started! Frontend: http://localhost:3000, Backend: http://localhost:8000"

# Stop all services
down:
	docker-compose down
	@echo "Services stopped."

# Build all services
build:
	docker-compose build

# Rebuild and restart all services
rebuild: down build up

# Show logs from all services
logs:
	docker-compose logs -f

# Show frontend logs only
frontend-logs:
	docker-compose logs -f frontend

# Show backend logs only
backend-logs:
	docker-compose logs -f backend

# Restart all services
restart:
	docker-compose restart

# Clean up - stop services and remove containers/images
clean:
	docker-compose down --rmi all --volumes --remove-orphans
	@echo "Cleaned up containers, images, and volumes."