#!/bin/bash

# Deep Research Comparator - Docker Startup Script

set -e

echo "🚀 Deep Research Comparator - Docker Setup"
echo "==========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Error: docker-compose is not installed."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your API keys before running the application."
    echo "   Required keys: GEMINI_API_KEY, OPENAI_API_KEY, SERPER_API_KEY, PERPLEXITY_API_KEY"
    echo ""
    echo "After updating .env, run this script again."
    exit 1
fi

# Validate required environment variables
echo "🔍 Validating environment variables..."
source .env

missing_keys=()
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    missing_keys+=("GEMINI_API_KEY")
fi
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    missing_keys+=("OPENAI_API_KEY")
fi
if [ -z "$SERPER_API_KEY" ] || [ "$SERPER_API_KEY" = "your_serper_api_key_here" ]; then
    missing_keys+=("SERPER_API_KEY")
fi
if [ -z "$PERPLEXITY_API_KEY" ] || [ "$PERPLEXITY_API_KEY" = "your_perplexity_api_key_here" ]; then
    missing_keys+=("PERPLEXITY_API_KEY")
fi

if [ ${#missing_keys[@]} -ne 0 ]; then
    echo "❌ Missing or invalid API keys in .env file:"
    for key in "${missing_keys[@]}"; do
        echo "   - $key"
    done
    echo ""
    echo "Please update your .env file with valid API keys."
    exit 1
fi

echo "✅ Environment variables validated"

# Build and start services
echo "🏗️  Building and starting services..."
echo "This may take a few minutes on first run..."

docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."

# Wait for database to be ready
echo "   Waiting for PostgreSQL..."
timeout=30
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose exec -T postgres pg_isready -U deepresearch_user -d deepresearch_db > /dev/null 2>&1; then
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ PostgreSQL failed to start within $timeout seconds"
    docker-compose logs postgres
    exit 1
fi

echo "✅ PostgreSQL is ready"

# Wait for backend to be ready
echo "   Waiting for backend API..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        break
    fi
    sleep 3
    counter=$((counter + 3))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Backend API failed to start within $timeout seconds"
    docker-compose logs backend_app
    exit 1
fi

echo "✅ Backend API is ready"

# Wait for frontend to be ready
echo "   Waiting for frontend..."
timeout=30
counter=0
while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Frontend failed to start within $timeout seconds"
    docker-compose logs frontend
    exit 1
fi

echo "✅ Frontend is ready"

echo ""
echo "🎉 Deep Research Comparator is now running!"
echo "==========================================="
echo "🌐 Frontend: http://localhost:5173"
echo "🔗 Backend API: http://localhost:5001"
echo "📚 API Docs: http://localhost:5001/docs"
echo ""
echo "📊 Services Status:"
echo "   - PostgreSQL: http://localhost:5432"
echo "   - Backend App: http://localhost:5001"
echo "   - Frontend: http://localhost:5173"
echo "   - Baseline Agent: http://localhost:5003"
echo "   - GPT Researcher: http://localhost:5004"
echo "   - Perplexity Agent: http://localhost:5005"
echo ""
echo "🛑 To stop all services: docker-compose down"
echo "📋 To view logs: docker-compose logs -f"
echo "🔄 To restart: docker-compose restart"