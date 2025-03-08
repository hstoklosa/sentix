# SentiX: Real-Time Insights into Cryptocurrency Markets

A modern web application that provides real-time sentiment analysis for cryptocurrency markets, helping traders and investors make data-driven decisions.

## Features

- Real-time cryptocurrency sentiment analysis
- Personalized content delivery system
- Secure user authentication and authorization
- Interactive data visualization
- RESTful API with comprehensive documentation

## Tech Stack

### Frontend

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 6
- **State Management**: React Query (TanStack Query)
- **Styling**: TailwindCSS 4
- **HTTP Client**: Axios
- **UI Components**: Custom components with Lucide React icons

### Backend

- **Framework**: FastAPI with Python
- **Database**: PostgreSQL with SQLAlchemy/SQLModel
- **Authentication**: PassLib with JWT (python-jose)
- **API Documentation**: FastAPI Swagger/OpenAPI
- **Environment**: Python dotenv for configuration

### DevOps

- **Containerization**: Docker and Docker Compose
- **Development**: Hot-reloading for both frontend and backend

## Project Structure

```
sentix/
├── frontend/          # React + Vite frontend application
├── backend/           # FastAPI backend service
├── nlp-engine/        # Natural Language Processing service
└── docker-compose.yml # Docker composition for all services
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+
- Docker and Docker Compose (optional)
- PostgreSQL (if running without Docker)

### Environment Setup

1. Clone the repository:

   ```bash
   git clone git@github.com:hstoklosa/sentix.git
   cd sentix
   ```

2. Set up environment variables:
   ```bash
   cp .env.sample .env
   cp frontend/.env.sample frontend/.env
   cp backend/.env.sample backend/.env
   ```

### Development Setup

#### Using Docker (Recommended)

1. Build and start all services:

   ```bash
   docker-compose up --build
   ```

   This will start the frontend, backend, and database services in development mode with hot-reloading.

#### Manual Setup

##### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the development server:

   ```bash
   fastapi dev main.py
   ```

   <!-- ```bash
   uvicorn app.main:app --reload --port 8000
   ``` -->

##### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Accessing the Application

- Frontend Application: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Copyright & Licenses

### Code

All code is authored by [hstoklosa](https://github.com/hstoklosa), unless it has been referenced.

Imported libraries (authors and licenses):

- FastAPI (Open-Source) - MIT License
- React (Meta Open Source) - MIT License
- Vite (Open Source) - MIT License
- TailwindCSS (Open Source) - MIT License
- SQLAlchemy (Open Source) - MIT License
- PassLib (Open Source) - BSD License
- Python-Jose (Open Source) - MIT License

<br />

© 2025 H. Stoklosa - hubert.stoklosa23@gmail.com

https://github.com/hstoklosa
