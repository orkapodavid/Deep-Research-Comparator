# Deep-Research-Comparator

Official repository for Deep Research Comparator: A Platform For Fine-grained Human Annotations of Deep Research Agents [Submitted to : EMNLP System Demo 2025]
Preprint Link : https://arxiv.org/abs/2507.05495


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
The main backend present in `/app` directory expects the PostgresSQL Database connection parameters and the HTTP API endpoints of the participating agents through the file `keys.env` whose structure is presented below	

```bash
AWS_ENDPOINT = "YOUR DATABASE URL"
DB_NAME = "YOUR DATABASE NAME"
DB_USERNAME = "YOUR DATABASE USERNAME"
DB_PASSWORD = "YOUR DATABASE PASSWORD"
GPT_RESEARCHER_URL = http://localhost:5004/run
PERPLEXITY_URL = http://localhost:5005/run
BASELINE_URL = http://localhost:5003/run
```
#### SIMPLE DEEPRESEARCH (Gemini 2.5 Flash)
This agent expects the Gemini API key in a file titled `keys.env` whose structure is presented below
```bash
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" 
```
#### Perplexity DeepResearch
This agent expects the Perplexity API key in a file titled `keys.env` whose structure is presented below
```bash
PERPLEXITY_API_KEY = "YOUR_PERPLEXITY_API_KEY"
```
#### GPT Researcher
Since we have used Serper as the search engine instead of the default Tavily for our experimented the environment  for GPT Researcher is configured as follows
```bash
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
export SERPER_API_KEY = "YOUR_SERPER_API_KEY"
export RETRIEVER=serper
```
### 2. Platform Setup (dev environment)
To set up the platform, we need 5 bash terminals: one for the frontend, one for the main backend, and three for the agents.
```bash
cd frontend
npm run dev
```
```bash
cd backend/app
python app.py
```

```bash
cd backend/gpt_researcher_server
python main.py
```
```bash
cd backend/perplexity_server
python main.py
```
```bash
cd backend/Simple_DeepResearch_server
python main.py
```
If all the default settings the followed the platform should be available in : http://localhost:5173/

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