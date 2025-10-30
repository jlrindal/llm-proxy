"""
Simple database operations using Supabase.
Modify these functions to match your existing table structure.
"""

from supabase import create_client, Client
from config import settings
from datetime import datetime

# Initialize Supabase client (using service key for backend operations)
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)


def check_user_limits(user_id: str) -> dict:
    """
    Check if user can make a request based on their plan and usage.
    
    Should return: {
        "allowed": True/False,
        "plan": "free"/"pro"/etc,
        "remaining": number
    }
    """
    try:
        # 1. Find the user by UUID
        user_response = supabase.table("users").select("*").eq("uuid", user_id).single().execute()
        
        if not user_response.data:
            print(f"User not found: {user_id}")
            return {"allowed": False, "plan": "none", "remaining": 0}
        
        user = user_response.data
        
        # 2. Check if user is active
        if not user.get("active", False):
            print(f"User inactive: {user_id}")
            return {"allowed": False, "plan": user.get("plan_id", "inactive"), "remaining": 0}
        
        # 3. Check if subscription is still valid (if current_period_end exists)
        if user.get("current_period_end"):
            period_end = datetime.fromisoformat(user["current_period_end"].replace("Z", "+00:00"))
            if datetime.utcnow().replace(tzinfo=period_end.tzinfo) > period_end:
                print(f"User subscription expired: {user_id}")
                return {"allowed": False, "plan": user.get("plan_id", "expired"), "remaining": 0}
        
        # 4. Get the plan details
        plan_id = user.get("plan_id")
        if not plan_id:
            print(f"User has no plan_id: {user_id}")
            return {"allowed": False, "plan": "none", "remaining": 0}
        
        plan_response = supabase.table("plan").select("*").eq("plan_id", plan_id).eq("active", True).single().execute()
        
        if not plan_response.data:
            print(f"Plan not found or inactive: {plan_id}")
            return {"allowed": False, "plan": plan_id, "remaining": 0}
        
        plan = plan_response.data
        token_limit = plan.get("token_limit", 0)
        
        if not token_limit:
            print(f"Plan has no token_limit set: {plan_id}")
            return {"allowed": False, "plan": plan_id, "remaining": 0}
        
        # 5. Calculate token usage within the current billing period
        current_period_start = user.get("current_period_start")
        
        # Query usage within the current period
        usage_response = supabase.table("usage").select("token_count").eq("uuid", user_id).gte("datetime", current_period_start).execute()
        
        # Sum all token_count values
        total_tokens_used = sum(record.get("token_count", 0) for record in usage_response.data) if usage_response.data else 0
        
        # 6. Check if user is within their token limit
        remaining_tokens = token_limit - total_tokens_used
        
        if remaining_tokens <= 0:
            print(f"User exceeded token limit: {user_id} (used: {total_tokens_used}, limit: {token_limit})")
            return {
                "allowed": False,
                "plan": plan_id,
                "remaining": 0,
                "message": "Usage limits exceeded. Please upgrade your plan."
            }
        
        return {
            "allowed": True,
            "plan": plan_id,
            "remaining": remaining_tokens
        }
        
    except Exception as e:
        print(f"Error checking limits: {e}")
        # On error, allow request (fail open)
        return {"allowed": True, "plan": "unknown", "remaining": 0}


def log_request(user_id: str, model: str, tokens: int):
    """
    Log API usage to the usage table.
    """
    try:
        data = {
            "uuid": user_id,
            "token_count": tokens
        }
        
        supabase.table("usage").insert(data).execute()
        print(f"Logged usage: user={user_id}, tokens={tokens}")
        
    except Exception as e:
        print(f"Error logging usage: {e}")
        raise
