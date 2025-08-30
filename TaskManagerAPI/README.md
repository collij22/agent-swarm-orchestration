# TaskManagerAPI - AI-Enhanced Task Management

A full-stack task management application with AI-powered categorization and priority scoring.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose

### Local Development

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

3. **Docker Deployment**
```bash
docker-compose up --build
```

## 🏗️ Architecture

- **Backend**: FastAPI + SQLite + JWT Authentication
- **Frontend**: React + Vite + Tailwind CSS
- **AI**: OpenAI GPT-3.5-turbo for categorization & priority scoring
- **Database**: SQLite with proper indexing
- **Deployment**: Docker + Docker Compose

## 📚 API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## 🔧 Environment Variables

Create `.env` files in backend and frontend directories:

**Backend (.env)**
```
DATABASE_URL=sqlite:///./taskmanager.db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

**Frontend (.env)**
```
VITE_API_URL=http://localhost:8000/api/v1
```

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests  
cd frontend && npm test
```

## [DOC] Features

- [DONE] User Authentication (JWT)
- [DONE] CRUD Operations for Tasks
- [DONE] AI Task Categorization
- [DONE] AI Priority Scoring
- [DONE] Category Management
- [DONE] Responsive UI
- [DONE] API Documentation
- [DONE] Docker Deployment

## 🎯 Success Metrics

- All CRUD endpoints functional [DONE]
- AI categorization accuracy >80% 🎯
- API response time <100ms ⚡
- Test coverage >85% 🧪
- Docker deployment successful 🐳