# Deep Research Comparator - Docker Setup

This document provides step-by-step instructions for running the entire Deep Research Comparator application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- API keys for the required services (see Environment Variables section)

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd Deep-Research-Comparator
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and replace the placeholder API keys with your actual keys:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `OPENAI_API_KEY`: Your OpenAI API key  
   - `SERPER_API_KEY`: Your Serper API key (for web search)
   - `PERPLEXITY_API_KEY`: Your Perplexity API key

3. **Start all services:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5001
   - API Documentation: http://localhost:5001/docs

## Environment Variables

The application requires several API keys. Create a `.env` file in the project root with the following variables:

```env
# API Keys - Replace with your actual keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Database Configuration (automatically set for Docker)
DB_ENDPOINT=postgres
DB_NAME=deepresearch_db
DB_USERNAME=deepresearch_user
DB_PASSWORD=deepresearch_password

# Service URLs (automatically set for Docker)
GPT_RESEARCHER_URL=http://gpt_researcher:5004/run
PERPLEXITY_URL=http://perplexity_server:5005/run
BASELINE_URL=http://baseline_server:5003/run

# Other Configuration
RETRIEVER=serper
```

## Services

The Docker setup includes the following services:

### Core Services
- **postgres**: PostgreSQL database (port 5432)
- **backend_app**: Main FastAPI backend (port 5001)
- **frontend**: React frontend with Vite (port 5173)

### AI Agent Services
- **baseline_server**: Simple DeepResearch using Gemini (port 5003)
- **gpt_researcher**: GPT Researcher agent (port 5004)
- **perplexity_server**: Perplexity API agent (port 5005)

## Docker Commands

### Start all services:
```bash
docker-compose up --build
```

### Start in background:
```bash
docker-compose up -d --build
```

### Stop all services:
```bash
docker-compose down
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend_app
```

### Rebuild specific service:
```bash
docker-compose up --build backend_app
```

### Remove all data (including database):
```bash
docker-compose down -v
```

## Database Management

The PostgreSQL database is automatically set up with:
- Database initialization on first run
- Table creation via `create_tables.py`
- Initial data seeding via `insert_databases.py`

### Access PostgreSQL directly:
```bash
docker exec -it deepresearch_postgres psql -U deepresearch_user -d deepresearch_db
```

### Database commands:
```sql
-- List tables
\dt

-- View agent data
SELECT * FROM deepresearchagent;

-- Exit
\q
```

## Development Mode

The Docker setup includes volume mounts for development:
- Backend services have hot-reload enabled
- Frontend has Vite dev server with hot-reload
- Code changes are reflected immediately without rebuilding

## Troubleshooting

### Service won't start:
1. Check logs: `docker-compose logs -f [service_name]`
2. Verify API keys in `.env` file
3. Ensure no port conflicts (ports 5001, 5003-5005, 5173, 5432)

### Database connection issues:
1. Wait for PostgreSQL to fully start (check health status)
2. Verify database credentials in `.env`
3. Check network connectivity between services

### API key issues:
1. Verify all required API keys are set in `.env`
2. Check API key validity and quotas
3. Ensure no extra spaces or quotes in `.env` values

### Port conflicts:
```bash
# Check what's using a port
lsof -i :5001

# Kill process using a port
sudo kill -9 $(lsof -t -i:5001)
```

### Reset everything:
```bash
docker-compose down -v
docker system prune -f
docker-compose up --build
```

## Production Deployment

For production deployment:

1. Update environment variables for production
2. Use production-ready Docker images
3. Set up proper SSL/TLS certificates
4. Configure external database if needed
5. Set up monitoring and logging

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend App    │    │   PostgreSQL    │
│   (React)       │◄──►│   (FastAPI)      │◄──►│   Database      │
│   Port: 5173    │    │   Port: 5001     │    │   Port: 5432    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   AI Agent Services │
                    ├─────────────────────┤
                    │ Baseline (5003)     │
                    │ GPT Researcher (5004)│
                    │ Perplexity (5005)   │
                    └─────────────────────┘
```

All services communicate through a Docker network called `deepresearch_network`.