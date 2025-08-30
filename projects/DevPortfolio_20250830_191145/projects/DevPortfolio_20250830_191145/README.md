# DevPortfolio: Professional Developer Portfolio Platform

## Project Overview
DevPortfolio is a full-stack web application designed to showcase developer projects, technical blog, and professional experience with AI-powered content assistance.

### Key Features
- 🚀 Project Showcase System
- [DOC] Markdown Blog Engine
- 🤖 AI Writing Assistant
- [DOC] Visitor Analytics
- 🔐 Secure Admin Authentication

## Tech Stack
- **Frontend**: React + TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Caching**: Redis
- **Deployment**: Docker, AWS/Vercel
- **CI/CD**: GitHub Actions

## Prerequisites
- Node.js 16+
- Python 3.9+
- Docker
- PostgreSQL
- Redis

## Quick Start

### Local Development
1. Clone the repository
```bash
git clone https://github.com/yourusername/devportfolio.git
cd devportfolio
```

2. Setup Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

3. Setup Frontend
```bash
# Install npm dependencies
npm install
```

4. Configure Environment
- Copy `.env.example` to `.env`
- Fill in required credentials

5. Run Development Servers
```bash
# Start backend
uvicorn backend.main:app --reload

# Start frontend
npm run dev
```

## Deployment
- Containerized with Docker
- Supports AWS and Vercel deployment
- GitHub Actions for CI/CD

## Security Features
- JWT Authentication
- OAuth Integration
- Two-Factor Authentication
- OWASP Top 10 Compliance

## Performance Targets
- Initial Load: < 3 seconds
- API Response: < 200ms
- Uptime: 99.9%

## Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push and create Pull Request

## License
MIT License

## Support
Open an issue on GitHub for bugs or feature requests.