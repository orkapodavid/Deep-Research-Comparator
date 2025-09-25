# Deep-Research-Comparator

Official repository for Deep Research Comparator: A Platform For Fine-grained Human Annotations of Deep Research Agents [Submitted to : EMNLP System Demo 2025]

Preprint Link : https://arxiv.org/abs/2507.05495

## 🐳 Quick Start with Docker (Recommended)

The easiest way to run the entire application is using Docker:

### Prerequisites
- Docker and Docker Compose installed
- API keys for required services

### Setup
1. **Clone and navigate to the repository:**
   ```bash
   git clone <repository-url>
   cd Deep-Research-Comparator
   ```

2. **Run the startup script:**
   ```bash
   ./start.sh
   ```
   
   This will:
   - Create a `.env` file template
   - Guide you through setting up API keys
   - Build and start all services
   - Automatically set up the database tables and initial data
   - Verify everything is working

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5001
   - API Documentation: http://localhost:5001/docs

For detailed Docker instructions, see [DOCKER_README.md](DOCKER_README.md).

## 📋 Manual Setup (Development)

If you prefer to run services manually:

### Database Setup (Required for Manual Setup)

Before running the application manually, you need to set up the PostgreSQL database:

1. **Create a PostgreSQL database** and note the connection details
2. **Set up environment variables** (see Environment Setup section below)
3. **Initialize the database tables:**
   ```bash
   cd backend/app
   python create_tables.py
   ```
4. **Insert initial agent data:**
   ```bash
   python insert_databases.py
   ```


## ⚙️ Backend - Environment Setup

Run the following commands to set up the Python environment:

```bash
cd backend 
# Create and activate conda environment
conda create -n deepresearch_comparator python=3.12
conda activate deepresearch_comparator

# Install the packages  in development mode
pip install - r master_requirements.txt

# We can also create separate virtual environments for the main backend and the three supported agents
cd app
pip install -r requirements.txt

cd gpt_researcher_server
pip install -r requirements.txt

cd perplexity_server
pip install -r requirements.txt

cd Simple_DeepResearch_server
pip install -r requirements.txt
```
## ⚙️ Frontend - Setup

Run the following commands to set up the Frontend :

```bash
cd frontend

npm install 
```


## 🚀 Run 

### 1. Environment Setup 

#### Main Backend 
The main backend present in `backend/app` directory expects the PostgreSQL Database connection parameters and the HTTP API endpoints of the participating agents through environment variables. Create a `.env` file in the root directory with the following structure:

```bash
# Database Configuration
DB_ENDPOINT="YOUR_DATABASE_URL"
DB_NAME="YOUR_DATABASE_NAME"
DB_USERNAME="YOUR_DATABASE_USERNAME"
DB_PASSWORD="YOUR_DATABASE_PASSWORD"

# Agent Service URLs (for manual setup)
GPT_RESEARCHER_URL=http://localhost:5004/run
PERPLEXITY_URL=http://localhost:5005/run
BASELINE_URL=http://localhost:5003/run

# API Keys
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
SERPER_API_KEY="YOUR_SERPER_API_KEY"
```

#### Individual Agent Environment Variables
Each agent service will automatically load the environment variables from the root `.env` file.

**SIMPLE DEEPRESEARCH (Gemini 2.5 Flash)**
- Requires: `GEMINI_API_KEY`

**Perplexity DeepResearch**
- Requires: `PERPLEXITY_API_KEY`

**GPT Researcher**
- Requires: `OPENAI_API_KEY`, `SERPER_API_KEY`
- Automatically configured to use Serper as the search engine

> **Note**: For legacy compatibility, you can also create individual `keys.env` files in each service directory, but using the root `.env` file is recommended.
### 2. Platform Setup (dev environment)
To set up the platform, we need 5 bash terminals: one for the frontend, one for the main backend, and three for the agents.

**Terminal 1 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 2 - Main Backend:**
```bash
cd backend/app
python app.py
```

**Terminal 3 - GPT Researcher:**
```bash
cd backend/gpt_researcher_server
python main.py
```

**Terminal 4 - Perplexity Server:**
```bash
cd backend/perplexity_server
python main.py
```

**Terminal 5 - Simple DeepResearch (Baseline):**
```bash
cd backend/Simple_DeepResearch_server
python main.py
```

If all the default settings are followed, the platform should be available at: http://localhost:5173/

> **Important**: Make sure you've completed the database setup steps before starting the services. Each service will print environment variable status on startup to help you verify your configuration.

## 🚀 Deployment Options

### Docker (Recommended)
- **Pros**: Easy setup, isolated environment, automatic database management, consistent across platforms
- **Cons**: Requires Docker knowledge, uses more system resources
- **Best for**: Production deployment, quick testing, users who want minimal setup

### Manual Setup
- **Pros**: More control, easier debugging, lighter resource usage
- **Cons**: Complex setup, dependency management, manual database setup required
- **Best for**: Development, customization, environments where Docker isn't available

## 🔧 Development

Both Docker and manual setups support development with hot-reload:
- **Docker**: Code changes are automatically reflected (volume mounts)
- **Manual**: Standard development server hot-reload

For detailed development instructions, see the respective setup sections above.

## 📊 Database Management

The application uses PostgreSQL with the following key tables:
- `deepresearch_agents`: Stores agent configurations (perplexity, baseline, gpt-researcher)
- `deepresearch_user_response`: Stores user preferences between agents
- `answer_span_votes`: Tracks user votes on specific text spans
- `intermediate_step_votes`: Tracks user votes on reasoning steps
- `deepresearch_rankings`: Stores computed Bradley-Terry rankings

**Rankings System**: The platform uses Bradley-Terry modeling to compute agent rankings based on user preferences. Run `python rankings.py` to update rankings after collecting user data.

## 📝 Citation

If you find this work useful, please consider starring our repo and citing our paper:

```bibtex
@misc{chandrahasan2025deepresearchcomparatorplatform,
      title={Deep Research Comparator: A Platform For Fine-grained Human Annotations of Deep Research Agents}, 
      author={Prahaladh Chandrahasan and Jiahe Jin and Zhihan Zhang and Tevin Wang and Andy Tang and Lucy Mo and Morteza Ziyadi and Leonardo F. R. Ribeiro and Zimeng Qiu and Markus Dreyer and Akari Asai and Chenyan Xiong},
      year={2025},
      eprint={2507.05495},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2507.05495}, 
}
```