# Sentix Framework: Project Product Package

The source code for the project is fully avilable within the following GitHub repositories:

- **Full-Stack Web Application**: [https://github.com/hstoklosa/sentix](https://github.com/hstoklosa/sentix)
- **NLP Pipeline**: [https://github.com/hstoklosa/sentix-nlp](https://github.com/hstoklosa/sentix-nlp)

## Getting Started

### Prerequisites

You need Docker and Docker Compose installed on your system. You can download it from the official Docker website: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).

### Setup

1. Download the project files, unzip them, and place them in a desired location on your computer.

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

3. Open a terminal and navigate to the project directory.

4. Run the following command to start the application:

   ```bash
   docker compose up --build
   ```

5. Wait for the application to start. Once it is running, you will be able to access the web application with a web browser using this link: `http://localhost:5173/`.

## Using the web application

Once the web application is running, the user interface will be easily accessible. Simply use the credentials "admin" and "Password123!" to log in. The application will automatically redirect you to the homepage, where you can explore its features.

## Project Structure

- `backend/`: Contains the Python-based FastAPI backend, responsible for handling API requests, authentication, and data processing.
  - `app`: Stores the core application logic, including API routes, database models, business services, and configuration.
    - `api/`: Defines the application's API endpoints, separating them into REST and WebSocket routes.
      - `rest/`: Contains all the REST API endpoints for features like authentication, news, market data, and bookmarks.
      - `websocket/`: Manages the WebSocket connections for pushing real-time data such as news updates to connected clients.
    - `core/`: Includes essential modules for backend configuration, database management, security, and API clients for external services.
      - `market/`: Contains client modules for fetching cryptocurrency market data from third-party APIs like CoinGecko and CoinMarketCap.
      - `news/`: Manages the ingestion of news from various providers and coordinates its distribution through the system.
    - `models/`: Defines the SQLModel ORM models that represent the structure of database tables for users, posts, coins, etc.
    - `schema/`: Contains Pydantic models used for data validation and for the request and response bodies of the API.
    - `services/`: Encapsulates the application's business logic, acting as an intermediary between API routes and database models.
  - `tests/`: All automated tests for the backend application to ensure code quality and correctness.
    - `unit/`: Contains unit tests that verify the functionality of individual components and functions in isolation.
    - `integration/`: Stores integration tests that check the interaction and data flow between multiple components of the application (e.g., API endpoints, database operations, and external services).
- `frontend/`: Contains the React-based frontend application built with Vite and TypeScript, which serves as the user interface.
  - `public/`: Stores static assets such as index.html, favicons, and images that are served directly to the browser.
  - `src/`: Contains all the source code for the React application, including components, routes, and business logic.
    - `app/`: Manages the application's core structure, including the main provider setup and file-based routing configuration.
      - `routes/`: Defines the application's routes/pages and URL structure using the TanStack Router's file-based routing system.
        - `_app/`: Contains layouts and dashboard routes that are protected and require user authentication.
        - `(auth)/`: Holds the routes related to the user authentication process, including the login and registration pages.
    - `assets/`: Stores static assets like images and logos that are imported and used within the React components.
    - `components/`: Contains globally reusable UI components that are shared across different features of the application.
      - `error/`: Holds components for displaying various error states, such as a "404 Not Found" page.
      - `layout/`: Provides structural components that define the overall layout of the application, like headers and sidebars.
      - `ui/`: Consists of general-purpose UI elements like buttons, inputs, and cards provided by shadcn/ui library.
    - `features/`: Organises code into distinct domains, wherew each folder contains all related components, hooks, and API calls.
      - `auth/`: Manages all aspects of user authentication, including forms, API requests, and state.
      - `bookmarks/`: Contains the logic for creating, viewing, and deleting user-specific post bookmarks.
      - `coins/`: Includes components and hooks for displaying cryptocurrency data like trending charts and sentiment divergence.
      - `market/`: Handles the fetching and display of overall market statistics and detailed price charts for individual coins.
      - `news/`: Contains the functionality for displaying, filtering, searching, and receiving real-time updates for news items.
    - `hooks/`: Provides custom, reusable React hooks that encapsulate shared logic like authentication state or local storage management.
    - `lib/`: Holds core library configurations and helper modules. For example, the Axios API client and React Query setup for server‑state management.
    - `types/`: Defines shared TypeScript type definitions used throughout the frontend codebase.
    - `utils/`: Contains miscellaneous utility functions for common tasks like formatting data or merging class names.
