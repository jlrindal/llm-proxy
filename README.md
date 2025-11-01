# Simple LLM Summarization Backend

A lightweight Python backend for your iOS app that handles auth, subscription checks, and AI-powered text summarization.

## Features

- ✅ Supabase authentication (JWT verification)
- ✅ Subscription & usage limit checks
- ✅ AI-powered text summarization via OpenAI
- ✅ User-customizable output formats (bullet points, numbered lists, etc.)
- ✅ User-customizable personas/tones (professional, casual, etc.)
- ✅ Backend-maintained prompt engineering for quality & cost optimization
- ✅ Usage logging & token tracking
- ✅ Docker deployment
- ✅ Simple and maintainable (~200 lines of code)

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
Summarize text with optional user preferences
- Requires: `Authorization: Bearer <supabase_jwt>`
- Body:
```json
{
  "text": "Text to summarize...",
  "format": "Bullet points with emoji (optional)",
  "persona": "Professional tone (optional)",
  "model": "gpt-3.5-turbo",
  "temperature": 0.5,
  "max_tokens": 500
}
```

See `API_EXAMPLES.md` for detailed usage examples

## iOS App Integration

```swift
// 1. Get Supabase token
let session = try await supabase.auth.session
let token = session.accessToken

// 2. Call your backend with user's selected profile
var request = URLRequest(url: URL(string: "http://your-backend:8080/api/chat")!)
request.httpMethod = "POST"
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let body: [String: Any] = [
    "text": "Your text to summarize...",
    "format": userProfile.format,  // e.g., "Bullet points with emoji"
    "persona": userProfile.persona, // e.g., "Professional tone"
    "model": "gpt-3.5-turbo"
]
request.httpBody = try JSONSerialization.data(withJSONObject: body)

let (data, response) = try await URLSession.shared.data(for: request)
// Parse response.content to display the summary
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
iOS App (sends text + optional format/persona from user profile)
  ↓ (with Supabase JWT)
Backend API
  ↓
1. Verify JWT token
2. Check user's plan & usage limits (query your Supabase tables)
3. Build prompt: Core backend instructions + user's format/persona
4. If allowed → Call OpenAI with optimized prompt
5. Log usage
6. Return summarized content
```

**Key Design:**
- Backend maintains core prompt engineering for quality/cost optimization
- Users can customize output format and tone via client-side profiles
- Simple separation: backend handles quality, users handle preferences

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


