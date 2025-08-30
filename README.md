# TaskManagerAPI: AI-Enhanced Task Management System

## Overview
TaskManagerAPI is an intelligent task management application featuring:
- RESTful API with CRUD operations for tasks
- AI-powered task categorization and priority scoring
- User authentication with JWT
- Simple React frontend
- Docker containerization

## Tech Stack
- Backend: Python FastAPI
- Database: SQLite
- Frontend: React (Vite)
- AI: OpenAI GPT-3.5-turbo
- Containerization: Docker

## Prerequisites
- Python 3.9+
- Docker
- Docker Compose
- OpenAI API Key

## Quick Start

### Local Development Setup
1. Clone the repository
```bash
git clone https://github.com/yourusername/taskmanagerapi.git
cd taskmanagerapi
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file with the following:
```
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_jwt_secret
DATABASE_URL=sqlite:///tasks.db
```

### Docker Deployment
```bash
docker-compose up --build
```

## API Documentation
Access Swagger UI at: `http://localhost:8000/docs`

## Features
- Create, Read, Update, Delete tasks
- AI-powered task categorization
- Smart priority scoring
- User authentication
- Rate limiting
- Comprehensive error handling

## Development
- Run tests: `pytest`
- Generate coverage report: `pytest --cov=.`

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

## Support
For issues or questions, please open a GitHub issue.