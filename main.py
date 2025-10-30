"""
Simple LLM Proxy Backend for iOS App
- Verifies Supabase auth tokens
- Checks subscription/usage limits
- Proxies requests to OpenAI
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
app = FastAPI(title="LLM Proxy API", version="1.0.0")

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


# Request/Response models
class Message(BaseModel):
    role: str  # "user", "assistant", or "system"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000


class ChatResponse(BaseModel):
    content: str
    model: str
    usage: dict
    plan_info: dict


@app.get("/")
def root():
    """Health check"""
    return {"status": "ok", "service": "LLM Proxy"}


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
    Main endpoint: Send messages to OpenAI
    
    Your iOS app calls this with:
    - Authorization header with Supabase JWT
    - JSON body with messages and model
    """
    user_id = user["id"]
    
    # 1. Check if user is allowed to make request
    limits = check_user_limits(user_id)
    if not limits["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="Usage limit exceeded. Please upgrade your plan."
        )
    
    # 2. Call OpenAI
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        response = openai_client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        content = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        # 3. Log usage
        log_request(user_id, request.model, usage["total_tokens"])
        
        return ChatResponse(
            content=content,
            model=response.model,
            usage=usage,
            plan_info=limits
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
