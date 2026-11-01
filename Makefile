.PHONY: build push up down logs health restart clean help

# Docker image names
DOCKER_REGISTRY ?= docker.io
DOCKER_USERNAME ?= your_username
BACKEND_IMAGE := $(DOCKER_REGISTRY)/$(DOCKER_USERNAME)/hirepilot-backend
FRONTEND_IMAGE := $(DOCKER_REGISTRY)/$(DOCKER_USERNAME)/hirepilot-frontend
IMAGE_TAG ?= latest

help:
	@echo "HirePilot Docker Commands"
	@echo "========================="
	@echo "make build      - Build both backend and frontend Docker images locally"
	@echo "make push       - Tag and push images to Docker registry (requires DOCKER_USERNAME)"
	@echo "make up         - Start all services with docker compose"
	@echo "make down       - Stop all running services"
	@echo "make logs       - View logs from all services (follow mode)"
	@echo "make health     - Check health of backend service"
	@echo "make restart    - Restart all services"
	@echo "make clean      - Remove containers, images, and volumes"
	@echo ""
	@echo "Configuration:"
	@echo "  DOCKER_USERNAME - Docker Hub username (default: your_username)"
	@echo "  IMAGE_TAG       - Docker image tag (default: latest)"
	@echo ""
	@echo "Example:"
	@echo "  make build"
	@echo "  make up"
	@echo "  make health"

build:
	@echo "Building HirePilot Docker images..."
	docker compose build --no-cache
	@echo "✓ Docker images built successfully"

push:
	@if [ "$(DOCKER_USERNAME)" = "your_username" ]; then \
		echo "ERROR: DOCKER_USERNAME not set. Use: make push DOCKER_USERNAME=your_username"; \
		exit 1; \
	fi
	@echo "Tagging images for Docker registry..."
	docker tag hirepilot-ai-backend:latest $(BACKEND_IMAGE):$(IMAGE_TAG)
	docker tag hirepilot-ai-frontend:latest $(FRONTEND_IMAGE):$(IMAGE_TAG)
	@echo "Pushing images to $(DOCKER_REGISTRY)..."
	docker push $(BACKEND_IMAGE):$(IMAGE_TAG)
	docker push $(FRONTEND_IMAGE):$(IMAGE_TAG)
	@echo "✓ Images pushed successfully to $(DOCKER_REGISTRY)"

up:
	@echo "Starting HirePilot services..."
	docker compose up -d --build
	@echo "✓ Services started"
	@echo ""
	@echo "Frontend available at: http://localhost:3000"
	@echo "Backend API at: http://localhost:4000"
	@echo "API docs at: http://localhost:4000/docs"
	@sleep 3
	@make health

down:
	@echo "Stopping HirePilot services..."
	docker compose down
	@echo "✓ Services stopped"

logs:
	@echo "Showing service logs (Ctrl+C to exit)..."
	docker compose logs -f

health:
	@echo "Checking backend health..."
	@if curl -s -f http://localhost:4000/api/v1/health > /dev/null; then \
		echo "✓ Backend is healthy"; \
		curl -s http://localhost:4000/api/v1/health | jq . || echo "Response: $$(curl -s http://localhost:4000/api/v1/health)"; \
	else \
		echo "✗ Backend is not responding"; \
		exit 1; \
	fi

restart:
	@echo "Restarting HirePilot services..."
	docker compose restart
	@echo "✓ Services restarted"
	@sleep 2
	@make health

clean:
	@echo "Cleaning up Docker resources..."
	docker compose down -v
	docker rmi hirepilot-ai-backend hirepilot-ai-frontend 2>/dev/null || true
	@echo "✓ Cleanup completed"

.DEFAULT_GOAL := help
