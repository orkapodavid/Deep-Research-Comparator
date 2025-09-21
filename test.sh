#!/bin/bash

# Test script to validate Docker setup

echo "🧪 Testing Deep Research Comparator Docker Setup"
echo "================================================"

# Test if all services are running
echo "Checking service health..."

services=("postgres:5432" "backend_app:5001" "frontend:5173" "baseline_server:5003" "gpt_researcher:5004" "perplexity_server:5005")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if docker-compose ps | grep -q "$name.*Up"; then
        echo "✅ $name is running"
    else
        echo "❌ $name is not running"
    fi
done

echo ""
echo "Testing API endpoints..."

# Test backend health
if curl -s http://localhost:5001/health | grep -q "ok"; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
fi

# Test frontend
if curl -s http://localhost:5173 > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
fi

# Test database connection
if docker-compose exec -T postgres pg_isready -U deepresearch_user -d deepresearch_db > /dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
fi

echo ""
echo "Testing agent services..."

# Test agent services
agents=("5003:baseline" "5004:gpt-researcher" "5005:perplexity")
for agent in "${agents[@]}"; do
    IFS=':' read -r port name <<< "$agent"
    if curl -s "http://localhost:$port/health" | grep -q "ok"; then
        echo "✅ $name agent is healthy"
    else
        echo "⚠️  $name agent health check failed (may be starting up)"
    fi
done

echo ""
echo "🎯 Test Summary"
echo "==============="
echo "If all tests pass, your Deep Research Comparator is ready to use!"
echo "Access the application at: http://localhost:5173"