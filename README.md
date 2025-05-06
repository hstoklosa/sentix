# Project Product Package

The project consisted of developing an NLP pipeline for sentiment analysis of cryptocurrency-related text. Consequently, this has resulted in a fine-tuned language model that exceeds Moodle's size limit, hence the source code for this project can be found in the following OneDrive folder: [https://cityuni-my.sharepoint.com/:f:/g/personal/hubert_stoklosa_city_ac_uk/Ej8ltfC7h6BMrWLwMZ3l3bgBgOkLD06SmFShkvrBs4OIog?e=RRTQKg](https://cityuni-my.sharepoint.com/:f:/g/personal/hubert_stoklosa_city_ac_uk/Ej8ltfC7h6BMrWLwMZ3l3bgBgOkLD06SmFShkvrBs4OIog?e=RRTQKg)

As a side-note, there are 2 separate GitHub repositories for the project:

- Full-stack Web Application: [https://github.com/hstoklosa/sentix](https://github.com/hstoklosa/sentix)
- Natural Language Processing Engine: [https://github.com/hstoklosa/sentix-nlp](https://github.com/hstoklosa/sentix-nlp)

## Setting up Sentix

Once the application is running, you w

### Prerequisites

You need Docker and Docker Compose installed on your system. Docker Desktop includes both. You can download it from the official Docker website: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).

Docker will allow for the easiest setup of the web application since it orchestrates the backend, frontend, and database services and does not require the user to install any additional software. Otherwise, the user would need to install Python, Node.js, PostgreSQL, and anything else that full-stack web applications requires.

## Running the application

1. Download the project files from the OneDrive link and place them in a desired location on your computer.

2. If `.env` doesn't exist, then proceed to create it and using the following contents:

```bash
FRONTEND_URL=http://localhost:5173

BACKEND_CORS_ORIGINS="http://localhost,http://localhost:5173,https://localhost,https://localhost:5173,http://localhost.tiangolo.com"
SECRET_KEY=7123ac49576369cb05c6efa938dad6b19979aa9c74ea92134ad5cb33b9241411

SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@gmail.com
SUPERUSER_PASSWORD=Password123!

COINMARKETCAP_API_KEY=793d7cdf-c940-40f9-8ebc-dc6b348e2172
COINGECKO_API_KEY=CG-Gkh8Z3KS1npaAts2MNZaChm8
TREENEWS_API_KEY=3d97f7319b028d1590e25f2b2f4fe544cd70bb64e9f23fc53e0bbd7affab4b93
COINDESK_API_KEY=d77c11241b74b5412d5bab0a6ca79c7280ebe8ac0217f2a3c3858c00fc8388c1

POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=sentix
POSTGRES_PASS=jdjd123
```

2. Open a terminal and navigate to the project directory.

3. Run the following command to start the application:

```bash
docker-compose up --build
```

4. Wait for the application to start. Once it is running, you will be able to access the web application with a web browser using this link: `http://localhost:5173/`.

### Testing the application

Once you have the web application running, the user interface will be easily accessible. Simply use the credentials "admin" and "Password123!" to log in. The application will automatically redirect you to the homepage, where you can explore its features.

## Folder Structure

```
.
├── backend/          # FastAPI backend application
│   ├── app/          # Main application source code
│   │   ├── api/      # API endpoints and routing
│   │   │   └── routes/ # Specific route modules
│   │   │       ├── rest/     # REST API routes
│   │   │       └── websocket/# WebSocket routes
│   │   ├── core/     # Core logic (config, db, security, domain logic)
│   │   │   ├── market/ # Market data related core logic
│   │   │   └── news/   # News related core logic
│   │   ├── ml_models/ # Machine learning models
│   │   │   └── finetuned_cryptobert/ # Specific ML model directory
│   │   ├── models/   # Database ORM models (SQLAlchemy)
│   │   ├── schemas/  # Pydantic data validation schemas
│   │   └── services/ # Business logic services
└── frontend/         # React/Vite/TypeScript frontend application
    ├── public/       # Static assets served directly by the web server
    └── src/          # Main frontend source code
        ├── app/      # Core application setup (routing, providers)
        │   └── routes/ # File-based routes (TanStack Router)
        │       ├── (auth)/ # Route group for authentication pages
        │       └── _app/   # Route group for authenticated application pages
        ├── assets/   # Static assets like images, logos used within the app
        ├── components/ # Reusable UI components
        │   ├── error/  # Error handling components (e.g., Not Found)
        │   ├── layout/ # Page layout components
        │   └── ui/     # Base UI components (shadcn/ui)
        ├── features/ # Feature-specific modules
        │   ├── auth/ # Authentication feature
        │   │   ├── api/      # API hooks for auth
        │   │   ├── components/ # UI components for auth
        │   │   └── types/    # Types specific to auth
        │   ├── bookmarks/ # Bookmarks feature
        │   │   ├── api/      # API hooks for bookmarks
        │   │   └── components/ # UI components for bookmarks
        │   ├── coins/    # Coins/Cryptocurrency feature
        │   │   ├── api/      # API hooks for coin data
        │   │   ├── components/ # UI components for coins
        │   │   ├── context/  # React context for coin data
        │   │   └── hooks/    # Custom hooks for coins
        │   ├── market/   # Market data feature
        │   │   ├── api/      # API hooks for market data
        │   │   └── components/ # UI components for market data
        │   ├── news/     # News feed feature
        │   │   ├── api/      # API hooks for news
        │   │   ├── components/ # UI components for news
        │   │   └── context/  # React context for news data
        │   └── watchlist/ # Watchlist feature
        │       ├── api/      # API hooks for watchlist
        │       └── components/ # UI components for watchlist
        ├── hooks/    # Shared custom React hooks
        ├── lib/      # Utility libraries configuration (API client, query client)
        ├── types/    # Shared TypeScript types and interfaces
        └── utils/    # General utility functions
```
