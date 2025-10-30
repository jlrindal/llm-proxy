# Simple LLM Proxy Backend

A lightweight Python backend for your iOS app that handles auth, subscription checks, and proxies requests to OpenAI.

## Features

- ✅ Supabase authentication (JWT verification)
- ✅ Subscription & usage limit checks
- ✅ OpenAI API proxy
- ✅ Usage logging
- ✅ Docker deployment
- ✅ Simple and easy to understand (~150 lines of code)

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

You need:
- **SUPABASE_URL**: Your Supabase project URL
- **SUPABASE_SERVICE_KEY**: Service role key (from Supabase dashboard)
- **JWT_SECRET**: JWT secret (Supabase Settings → API → JWT Settings)
- **OPENAI_API_KEY**: Your OpenAI API key

### 2. Run with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

The API will be available at `http://localhost:8080`

### 3. Run Locally (for development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## API Endpoints

### `GET /`
Health check

### `GET /api/me`
Get current user info and usage limits
- Requires: `Authorization: Bearer <supabase_jwt>`

### `POST /api/chat`
Send messages to OpenAI
- Requires: `Authorization: Bearer <supabase_jwt>`
- Body:
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

## iOS App Integration

```swift
// 1. Get Supabase token
let session = try await supabase.auth.session
let token = session.accessToken

// 2. Call your backend
var request = URLRequest(url: URL(string: "http://your-backend:8080/api/chat")!)
request.httpMethod = "POST"
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let body = [
    "messages": [
        ["role": "user", "content": "Hello!"]
    ],
    "model": "gpt-3.5-turbo"
]
request.httpBody = try JSONSerialization.data(withJSONObject: body)

let (data, response) = try await URLSession.shared.data(for: request)
```

## Customize for Your Database

Edit `database.py` to match your existing Supabase tables:

### `check_user_limits(user_id)`
Query your subscription/plan tables to determine if user can make a request.

### `log_request(user_id, model, tokens)`
Insert usage logs into your tracking table.

## Project Structure

```
backend/
├── main.py              # FastAPI app & endpoints (80 lines)
├── auth.py              # JWT verification (30 lines)
├── database.py          # Database queries (40 lines - customize this)
├── config.py            # Environment config (20 lines)
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker compose
└── .env                 # Your credentials (create from .env.example)
```

## How It Works

```
iOS App
  ↓ (with Supabase JWT)
Backend API
  ↓
1. Verify JWT token
2. Check user's plan & usage limits (query your Supabase tables)
3. If allowed → Call OpenAI
4. Log usage
5. Return response
```

## Deployment

### Docker (Recommended)
Already configured with Docker Compose. Just run on any server with Docker.

### Traditional Server
```bash
# Install
pip install -r requirements.txt

# Run with systemd or supervisor
uvicorn main:app --host 0.0.0.0 --port 8080
```

## Security Notes

1. Use HTTPS in production
2. Restrict CORS origins in `main.py`
3. Keep `.env` file secure
4. Use Supabase RLS policies for additional security

## Troubleshooting

**Invalid token error?**
- Make sure JWT_SECRET matches your Supabase project
- Check that your iOS app is sending the correct token

**Supabase connection error?**
- Verify SUPABASE_URL is accessible from your backend
- Check SUPABASE_SERVICE_KEY is correct

**OpenAI error?**
- Verify OPENAI_API_KEY is valid
- Check API usage/billing on OpenAI dashboard

## License

MIT

