"""
AI Text Summarization Backend for iOS App
- Verifies Supabase auth tokens
- Checks subscription/usage limits
- Accepts user-customizable formats and personas
- Maintains backend prompt engineering for quality
- Calls OpenAI for summarization
- Logs usage
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from config import settings
from auth import get_current_user
from database import check_user_limits, log_request

# Initialize FastAPI
app = FastAPI(title="AI Summarization API", version="2.0.0")

# Allow CORS for your iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.openai_api_key)


# ===== PROMPT ENGINEERING =====
# Core instructions maintained by backend for optimal performance
CORE_SYSTEM_PROMPT = """You are an expert at extracting compelling, standalone insights from longer content. Your goal is to identify the most interesting, impactful, and thought-provoking moments that would resonate with an audience.

Core Guidelines:
- Extract key ideas, fascinating facts, or powerful statements that stand alone
- Each snippet should be complete and understandable on its own
- Focus on what's interesting, surprising, or emotionally resonant
- Maintain accuracy - never add information not in the source
- Use clear, engaging language that draws readers in
- Each snippet should feel natural and authentic"""


def calculate_snippet_count(text: str) -> int:
    """
    Calculate how many snippets to generate based on text length.
    
    Rule: ~1 snippet per 300 words
    Min: 1 snippet, Max: 10 snippets
    """
    word_count = len(text.split())
    
    if word_count < 300:
        return 1
    elif word_count < 600:
        return 2
    elif word_count < 1200:
        return 3
    elif word_count < 2000:
        return 5
    elif word_count < 3000:
        return 7
    else:
        return 10  # Cap at 10 for very long texts


def build_prompt(text: str, format: str | None = None, persona: str | None = None) -> tuple[list[dict], int]:
    """
    Combines backend prompt engineering with user preferences.
    
    Args:
        text: The text to process
        format: User's preferred output format
        persona: User's preferred tone/style
    
    Returns:
        Tuple of (messages for OpenAI API, number of snippets to generate)
    """
    # Calculate how many snippets based on text length
    snippet_count = calculate_snippet_count(text)
    
    # Start with core backend instructions
    system_message = CORE_SYSTEM_PROMPT
    
    # Add user's format preference if provided
    if format:
        system_message += f"\n\nOutput Format for Each Snippet: {format}"
    
    # Add user's persona preference if provided
    if persona:
        system_message += f"\n\nTone/Style: {persona}"
    
    # Build the messages array
    user_message = f"""Extract {snippet_count} distinct, compelling snippets from the following text. Each snippet should be independent and capture a different interesting aspect, idea, or moment.

Present each snippet on its own line, separated by "---"

Text:
{text}"""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    return messages, snippet_count


# Request/Response models
class Message(BaseModel):
    role: str  # "user", "assistant", or "system"
    content: str


class ChatRequest(BaseModel):
    text: str  # The text to summarize
    format: str | None = None  # User's custom format (e.g., "bullet points", "numbered list")
    persona: str | None = None  # User's custom persona (e.g., "professional", "casual")
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.5  # Lower for more consistent summaries
    max_tokens: int = 500


class ChatResponse(BaseModel):
    snippets: list[str]  # Multiple short-form snippets
    snippet_count: int   # How many snippets were generated
    model: str
    usage: dict
    plan_info: dict


@app.get("/")
def root():
    """Health check"""
    return {"status": "ok", "service": "AI Summarization API"}


@app.get("/api/me")
def get_user_info(user: dict = Depends(get_current_user)):
    """Get current user info and usage limits"""
    limits = check_user_limits(user["id"])
    return {
        "user_id": user["id"],
        "email": user["email"],
        "limits": limits
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user)
):
    """
    Main endpoint: Generate multiple short-form snippets from long-form text
    
    Your iOS app calls this with:
    - Authorization header with Supabase JWT
    - JSON body with text, optional format and persona
    
    The backend automatically determines how many snippets to generate based on text length.
    
    Example request:
    {
        "text": "Long article or content...",
        "format": "Short, engaging format under 280 characters",
        "persona": "Conversational and thought-provoking",
        "model": "gpt-3.5-turbo"
    }
    
    Example response:
    {
        "snippets": [
            "First compelling snippet...",
            "Second interesting insight...",
            "Third thought-provoking idea..."
        ],
        "snippet_count": 3,
        ...
    }
    """
    user_id = user["id"]
    
    # 1. Check if user is allowed to make request
    limits = check_user_limits(user_id)
    if not limits["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="Usage limit exceeded. Please upgrade your plan."
        )
    
    # 2. Build prompt combining backend engineering + user preferences
    # Also get the expected snippet count
    messages, expected_count = build_prompt(
        text=request.text,
        format=request.format,
        persona=request.persona
    )
    
    # 3. Call OpenAI with increased max_tokens for multiple snippets
    try:
        # Adjust max_tokens based on snippet count (allow ~100 tokens per snippet)
        adjusted_max_tokens = min(request.max_tokens * expected_count, 2000)
        
        response = openai_client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=adjusted_max_tokens
        )
        
        content = response.choices[0].message.content
        
        # 4. Parse response into individual snippets
        # Split by "---" separator and clean up each snippet
        snippets = [
            snippet.strip() 
            for snippet in content.split("---") 
            if snippet.strip()
        ]
        
        # Fallback: if parsing failed, return as single snippet
        if not snippets:
            snippets = [content.strip()]
        
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        # 5. Log usage
        log_request(user_id, request.model, usage["total_tokens"])
        
        return ChatResponse(
            snippets=snippets,
            snippet_count=len(snippets),
            model=response.model,
            usage=usage,
            plan_info=limits
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
