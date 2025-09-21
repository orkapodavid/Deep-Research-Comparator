# Multi-Agent Deep Research Comparator

This is an enhanced version of the Deep Research Comparator that supports comparing multiple LLM agents simultaneously with full conversation history storage and retrieval.

## 🚀 New Features

### 1. Multi-Agent Comparison
- **Simultaneous Comparison**: View responses from multiple different LLM agents side by side
- **Named Agents**: Each agent window shows the LLM name (Perplexity, Simple Deepresearch (Gemini 2.5 Flash), GPT Researcher)
- **Real-time Streaming**: All agents stream their responses in real-time

### 2. Conversation History Storage
- **Automatic Saving**: All conversations are automatically saved to PostgreSQL database
- **Complete Data**: Stores questions, responses, intermediate steps, and citations for all agents
- **Session Tracking**: Links conversations to specific user sessions

### 3. Historical Data Viewing
- **Conversation History Page**: New `/history` route to view past conversations
- **Paginated Display**: Browse through conversations with pagination controls
- **Detailed View**: Click on any conversation to see full details including thinking processes
- **Search and Filter**: Easy access to past research comparisons

## 🛠 Technical Implementation

### Backend Changes
- **New API Endpoints**:
  - `GET /api/deepresearch-agents` - Returns all three agents with names
  - `POST /api/deepresearch-question` - Handles three-agent streaming
  - `POST /api/save-conversation` - Saves complete conversations
  - `GET /api/conversation-history` - Retrieves paginated history
  - `GET /api/conversation/{id}` - Gets specific conversation details

- **Database Schema**:
  - New `conversation_history` table with fields for all three agents
  - Stores responses, intermediate steps, and citations
  - UUID-based session and conversation tracking

### Frontend Changes
- **New Components**:
  - `ThreeAgentsPage.tsx` - Main page with three agent windows
  - `ConversationHistory.tsx` - History viewing component
  - `streamingThreeAgents.ts` - Three-agent streaming utility

- **Enhanced Navigation**:
  - Added "Three Agents" and "History" menu items
  - Responsive three-column layout for agent comparison

## 🚀 Quick Start

### Option 1: Using Three-Agent Backend (Recommended for New Features)

1. **Start the Three-Agent Backend**:
   ```bash
   cd backend/app
   conda activate deepresearch_comparator
   python app_three_agents.py
   ```

2. **Start the Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the Application**:
   - Three Agents Comparison: http://localhost:5173/three-agents
   - Conversation History: http://localhost:5173/history
   - Original Two-Agent Version: http://localhost:5173/

### Option 2: Using Original Backend (For Compatibility)

1. **Start the Original Backend**:
   ```bash
   cd backend/app
   conda activate deepresearch_comparator
   python app.py
   ```

2. **Access**: http://localhost:5173/ (original two-agent comparison)

## 📊 Database Setup

The conversation history feature requires the new database table:

```bash
cd backend/app
python create_conversation_table.py
```

This creates the `conversation_history` table with the following schema:
- Session tracking and timestamps
- Question and agent information
- Responses, intermediate steps, and citations for all three agents

## 🎯 Usage Workflow

1. **Ask a Question**: Navigate to `/three-agents` and enter your research question
2. **View Real-time Responses**: Watch all three agents respond simultaneously with their names displayed
3. **Automatic Saving**: Conversations are automatically saved when complete
4. **Review History**: Visit `/history` to browse past conversations
5. **Detailed Analysis**: Click any conversation to see full details including thinking processes

## 🔧 Configuration

The three-agent backend uses the same environment variables as the original:
- Database connection settings
- API keys for all three services (Perplexity, OpenAI, Gemini)
- Service URLs for each agent

## 📈 Benefits

1. **Better Comparison**: See three different approaches to the same question simultaneously
2. **Transparency**: Agent names are visible, making comparison more meaningful
3. **Research Continuity**: Access to conversation history enables follow-up research
4. **Data Collection**: Systematic storage of LLM responses for analysis
5. **User Experience**: Streamlined interface with easy navigation between features

## 🧪 Testing

The implementation has been tested with:
- ✅ Three-agent simultaneous streaming
- ✅ Automatic conversation saving
- ✅ History page pagination and search
- ✅ Backend API endpoints
- ✅ Database schema and operations
- ✅ Frontend integration and navigation

## 🔄 Migration Path

Users can gradually migrate from the two-agent to three-agent version:
- Both backends can run simultaneously on different ports
- Existing database tables remain unchanged
- New conversation history is stored separately
- Frontend supports both modes through different routes

This enhanced version maintains full backward compatibility while adding powerful new features for comprehensive LLM research comparison.