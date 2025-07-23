# Sentix: Real-time Cryptocurrency News Aggregator

A full-stack cryptocurrency sentiment analysis platform that aggregates real-time news from multiple sources, performs AI-powered sentiment analysis, and provides market insights to help users make informed trading decisions.

## 🌟 Features

### Core Functionality

- **Real-time News Aggregation**: Streams live cryptocurrency news from multiple sources (TreeNews, CoinDesk)
- **AI Sentiment Analysis**: Uses a fine-tuned CryptoBERT model (`hstoklosa/finetuned-cryptobert`) to analyze sentiment (Bearish/Neutral/Bullish)
- **Market Data Integration**: Real-time market statistics from CoinMarketCap and CoinGecko
- **WebSocket Support**: Live news updates pushed to connected clients
- **Bookmarking System**: Save and organize important news articles
- **Watchlist Management**: Track your favorite cryptocurrencies
- **Sentiment Divergence Analysis**: Compare sentiment trends against price movements
- **Trending Coins**: Discover the most mentioned cryptocurrencies in recent news

### Dashboard Features

- **News Feed**: Real-time stream of cryptocurrency news with sentiment indicators
- **Market Overview**: Global market statistics including market cap, volume, BTC dominance, and Fear & Greed Index
- **Price Charts**: Interactive price charts with multiple timeframes (1D to MAX)
- **Trending Analysis**: Visualize the most mentioned coins in the news
- **Sentiment Divergence Charts**: Compare sentiment polarity against price movements
- **Coin-specific Views**: Filter news and data by specific cryptocurrencies

### Technical Highlights

- **JWT Authentication**: Secure user authentication with access and refresh tokens
- **Scheduled Tasks**: Automated token cleanup and coin synchronization
- **Caching**: Efficient API response caching with aiocache
- **Database**: PostgreSQL with SQLModel ORM
- **Modern Frontend**: React 19 with TanStack Router and Query
- **Beautiful UI**: Tailwind CSS with Radix UI components and dark mode support

## 🏗️ Architecture

### Backend (FastAPI)

```
backend/
├── app/
│   ├── api/              # API routes (REST & WebSocket)
│   ├── core/             # Core functionality (config, database, market clients, news providers)
│   ├── ml_models/        # Sentiment analysis model
│   ├── models/           # SQLModel database models
│   ├── schemas/          # Pydantic schemas for validation
│   ├── services/         # Business logic layer
│   └── tests/            # Unit and integration tests
```

**Key Technologies:**

- FastAPI with async support
- PostgreSQL + SQLModel
- PyTorch + Transformers (HuggingFace)
- APScheduler for background tasks
- CCXT for exchange data
- WebSocket for real-time updates

### Frontend (React + TypeScript)

```
frontend/
├── src/
│   ├── app/              # TanStack Router configuration
│   ├── components/       # Reusable UI components
│   ├── features/         # Feature-based modules (auth, news, market, etc.)
│   ├── hooks/            # Custom React hooks
│   └── lib/              # Utilities and API client
```

**Key Technologies:**

- React 19 with TypeScript
- TanStack Router (file-based routing)
- TanStack Query (data fetching & caching)
- Tailwind CSS + Radix UI
- Zustand (state management)
- Recharts & Lightweight Charts (data visualization)
- React Hook Form + Zod (form validation)

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.12+ (for local development)

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASS=your_password
POSTGRES_DB=sentix

# Authentication
SECRET_KEY=your_secret_key_here
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=admin_password

# API Keys
TREENEWS_API_KEY=your_treenews_api_key
COINMARKETCAP_API_KEY=your_cmc_api_key
COINGECKO_API_KEY=your_coingecko_api_key
COINDESK_API_KEY=your_coindesk_api_key

# CORS
BACKEND_CORS_ORIGINS=http://localhost:5173

# Frontend
VITE_API_URL=http://localhost:8000
```

### Running with Docker Compose

1. **Clone the repository**

```bash
git clone <repository-url>
cd sentix
```

2. **Start all services**

```bash
docker-compose up --build
```

3. **Access the application**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/v1/docs

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
fastapi dev app/main.py
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📊 API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/logout` - Logout user
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### News

- `GET /api/v1/news/` - Get paginated news feed
- `GET /api/v1/news/{post_id}` - Get specific post
- `GET /api/v1/news/search` - Search news articles
- `GET /api/v1/news/coins` - Get all coins mentioned in news
- `WS /api/v1/ws/news` - WebSocket for real-time news

### Market

- `GET /api/v1/market/` - Get global market statistics
- `GET /api/v1/market/chart/{symbol}` - Get price chart data
- `GET /api/v1/market/coins` - Get coin list with market data

### Trending

- `GET /api/v1/trending/coins` - Get trending coins by mentions

### Bookmarks

- `GET /api/v1/bookmarks/` - Get user bookmarks
- `POST /api/v1/bookmarks/` - Create bookmark
- `DELETE /api/v1/bookmarks/{bookmark_id}` - Delete bookmark

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

The test suite includes:

- Unit tests for services, security, and news providers
- Integration tests for API endpoints and WebSocket connections

## 🔧 Configuration

### Backend Configuration

Key settings in `backend/app/core/config.py`:

- Token expiration times
- API polling intervals
- Database connection settings
- CORS origins

### Frontend Configuration

- `vite.config.ts` - Vite build configuration
- `tailwind.config.js` - Tailwind CSS customization
- `components.json` - Shadcn UI configuration

## 📦 Key Dependencies

### Backend

- `fastapi` - Modern web framework
- `sqlmodel` - SQL databases with Python type annotations
- `transformers` - HuggingFace transformers for ML
- `torch` - PyTorch for deep learning
- `ccxt` - Cryptocurrency exchange integration
- `apscheduler` - Background task scheduling
- `pyjwt` - JSON Web Token implementation

### Frontend

- `@tanstack/react-router` - Type-safe routing
- `@tanstack/react-query` - Data fetching & caching
- `react-hook-form` - Form management
- `recharts` - Chart library
- `lightweight-charts` - Financial charts
- `zustand` - State management
- `zod` - Schema validation

## 🎨 UI Components

The application uses a custom component library built on:

- Radix UI primitives
- Tailwind CSS for styling
- CVA (Class Variance Authority) for component variants
- Lucide React for icons

## 🔐 Security Features

- Password hashing with bcrypt
- JWT-based authentication (access + refresh tokens)
- HTTP-only cookies for refresh tokens
- CORS protection
- SQL injection prevention via SQLModel
- Input validation with Pydantic

## 📈 Sentiment Analysis

The sentiment analysis uses a fine-tuned BERT model specifically trained for cryptocurrency content:

- **Model**: `hstoklosa/finetuned-cryptobert`
- **Classes**: Bearish (0), Neutral (1), Bullish (2)
- **Output**: Label, confidence score, and polarity (-1 to +1)

## 🌐 News Sources

- **TreeNews**: Real-time cryptocurrency news aggregator
- **CoinDesk**: Leading cryptocurrency news platform

News is streamed via WebSocket connections and processed in real-time with sentiment analysis.

## 📝 License

This project is part of a Final Year Project (FYP).

## 🤝 Contributing

This is an academic project. For questions or suggestions, please contact the project maintainer.

## 📧 Support

For issues or questions, please open an issue in the repository.
