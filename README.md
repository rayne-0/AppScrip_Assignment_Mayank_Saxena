# Trade Opportunities API

A FastAPI service that analyzes market data and provides trade opportunity insights for specific sectors in India. Powered by **Google Gemini AI** and real-time **DuckDuckGo web search**.

## Features

- **Single powerful endpoint**: `GET /analyze/{sector}` returns a structured markdown report
- **AI-Powered Analysis**: Uses Google Gemini API for intelligent market insights
- **Real-Time Data**: Searches the web for current market news and trends
- **JWT Authentication**: Supports registered users and instant guest tokens
- **Rate Limiting**: In-memory sliding window rate limiter (10 req/min default)
- **Response Caching**: 30-minute cache to avoid redundant API calls
- **Input Validation**: Strict sector name validation
- **Interactive Docs**: Auto-generated Swagger UI at `/docs`

## Quick Start

### 1. Clone & Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Gemini API key
# Get a FREE key at: https://aistudio.google.com/apikey
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Interactive docs are available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### System

| Method | Endpoint   | Description          | Auth Required |
|--------|-----------|----------------------|---------------|
| GET    | `/`       | API info & quick start | No           |
| GET    | `/health` | Health check          | No            |

### Authentication

| Method | Endpoint          | Description                        | Auth Required |
|--------|------------------|------------------------------------|---------------|
| POST   | `/auth/token`    | Get a guest JWT token (instant)    | No            |
| POST   | `/auth/register` | Register with username/password    | No            |
| POST   | `/auth/login`    | Login with credentials             | No            |

### Analysis

| Method | Endpoint             | Description                          | Auth Required |
|--------|---------------------|--------------------------------------|---------------|
| GET    | `/analyze/{sector}` | Get trade opportunity analysis report | Yes (Bearer)  |

## Usage Examples

### Step 1: Get a Token

```bash
# Guest token (instant, no signup)
curl -X POST http://localhost:8000/auth/token

# Or register an account
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "trader1", "password": "securepass123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "username": "guest_a1b2c3d4"
}
```

### Step 2: Analyze a Sector

```bash
curl -X GET http://localhost:8000/analyze/pharmaceuticals \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

Response:
```json
{
  "sector": "pharmaceuticals",
  "report": "# Trade Opportunities Report: Pharmaceuticals Sector — India\n\n## Executive Summary\n...",
  "generated_at": "2026-04-20T12:00:00Z",
  "sources": [
    {
      "title": "India Pharma Market Analysis 2026",
      "url": "https://example.com/article",
      "snippet": "The Indian pharmaceutical market..."
    }
  ],
  "cached": false
}
```

### Example Sectors

- `pharmaceuticals`
- `technology`
- `agriculture`
- `textiles`
- `automobile`
- `renewable energy`
- `steel`
- `chemicals`
- `oil & gas`
- `food processing`

## Architecture

```
AppScrip/
├── app/
│   ├── main.py              # FastAPI app, middleware, error handlers
│   ├── config.py             # Pydantic settings from .env
│   ├── auth.py               # JWT auth + guest mode
│   ├── rate_limiter.py       # Sliding window rate limiter
│   ├── models.py             # Pydantic request/response models
│   ├── services/
│   │   ├── search.py         # DuckDuckGo web search
│   │   └── analyzer.py       # Gemini AI analysis
│   └── routes/
│       ├── auth_routes.py    # Auth endpoints
│       └── analyze.py        # GET /analyze/{sector}
├── .env.example
├── requirements.txt
└── README.md
```

### Request Flow

```
Client Request
    ↓
[Input Validation] → 400 if invalid
    ↓
[JWT Authentication] → 401 if no/bad token
    ↓
[Rate Limiting] → 429 if exceeded
    ↓
[Cache Check] → Return cached if fresh
    ↓
[DuckDuckGo Search] → Collect market data
    ↓
[Gemini AI Analysis] → Generate report
    ↓
[Cache & Return] → JSON response with markdown report
```

## Security Features

- **JWT Authentication**: All analysis requests require a valid Bearer token
- **Input Validation**: Sector names are validated (alpha chars, 2-50 length)
- **Rate Limiting**: Sliding window limiter prevents abuse (configurable)
- **CORS**: Configured via middleware
- **Error Handling**: Global exception handler prevents stack trace leaks

## Configuration

All settings are configurable via `.env` file or environment variables:

| Variable                   | Default                        | Description                    |
|---------------------------|-------------------------------|--------------------------------|
| `GEMINI_API_KEY`          | (required)                     | Google Gemini API key          |
| `JWT_SECRET`              | `dev-secret-key-...`          | Secret key for JWT signing     |
| `JWT_ALGORITHM`           | `HS256`                        | JWT signing algorithm          |
| `JWT_EXPIRY_MINUTES`      | `60`                           | Token expiry time              |
| `RATE_LIMIT_REQUESTS`     | `10`                           | Max requests per window        |
| `RATE_LIMIT_WINDOW_SECONDS` | `60`                         | Rate limit window in seconds   |
| `APP_ENV`                 | `development`                  | Environment name               |

## Tech Stack

- **Framework**: FastAPI
- **AI**: Google Gemini API (gemini-2.0-flash)
- **Search**: DuckDuckGo Search (no API key needed)
- **Auth**: JWT via python-jose + passlib bcrypt
- **Validation**: Pydantic v2
- **Server**: Uvicorn (ASGI)
- **Storage**: In-memory (no database required)
