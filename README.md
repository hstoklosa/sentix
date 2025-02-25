# SentiX: Real-Time Cryptocurrency Sentiment Analysis and Personalised Content Delivery System

## Features

- Real-time cryptocurrency sentiment analysis
- Personalised content delivery system
- ...

## Technologies

- React
- FastAPI
- ...

## Usage

The first step is to clone the repository:

```bash
git clone git@github.com:hstoklosa/sentix.git
```

### Manual Installation

#### Backend

1. After cloning the repository, navigate into the back-end directory:

   ```bash
   cd sentix/backend
   ```

2. Set up a virtual environment:

   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

4. Install the `requirements.txt` dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Run the development backend server:

   ```bash
   fastapi dev main.py
   ```

#### Frontend

6. Open a new terminal window and navigate into the front-end directory:

   ```bash
   cd sentix/frontend
   ```

7. Install the `package.json` dependencies:

   ```bash
   npm install
   ```

8. Run the development frontend app:

   ```bash
   npm start
   ```

### Docker Installation

1. After cloning the repository, navigate into the root directory:

   ```bash
   cd sentix
   ```

2. There are two recommended ways to build and run the Docker containers:

   1. Run in the foreground:

      ```bash
       docker-compose up --build
      ```

   2. or run in detached mode:

      ```bash
      docker-compose up --build -d
      ```

### Accessing the app

Regardless of the method chosen, the frontend app should now be running on http://localhost:3000 and should be accessible from the browser. Additionally, the interactive API documentation for the backend can be accessed at http://localhost:8000/docs.

## Copyright & Licenses

### Code

All code is written by [me](https://github.com/hstoklosa), unless it has been referenced.

Imported libraries (authors and licenses):

- FastAPI (Open-Source) - MIT License
- ...

<br />

© 2025 H. Stoklosa - hubert.stoklosa23@gmail.com

https://github.com/hstoklosa
