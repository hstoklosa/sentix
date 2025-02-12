# SentiX: Real-Time Cryptocurrency Sentiment Analysis and Personalised Content Delivery System

## Installation

Clone the repository as the first step.

```bash
git clone git@github.com:hstoklosa/sentix.git
```

### Manual

#### Backend

After cloning the repository, navigate into the back-end directory:

```bash
cd sentix/backend
```

Set up a virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install the `requirements.txt` dependencies:

```bash
pip install -r requirements.txt
```

Run the development backend server:

```bash
fastapi dev main.py
```

#### Frontend

Open a new terminal window and navigate into the front-end directory:

```bash
cd sentix/frontend
```

Install the `package.json` dependencies:

```bash
npm install
```

Run the development frontend app:

```bash
npm start
```

### Docker

COMING SOON
