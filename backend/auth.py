from fastapi import (
    Header,
    HTTPException
)

from supabase import (
    create_client,
    Client
)

from config import (
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


# ---------------------------------------------------------
# Get currently logged-in user
# ---------------------------------------------------------
def get_current_user(
    authorization: str = Header(None)
):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is missing"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format"
        )

    token = authorization.split(
        " ",
        1
    )[1]

    try:
        response = (
            supabase
            .auth
            .get_user(token)
        )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

    if not response.user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return response.user


# ---------------------------------------------------------
# Get currently logged-in ADMIN
# ---------------------------------------------------------
def get_current_admin(
    authorization: str = Header(None)
):

    # First authenticate the user
    user = get_current_user(
        authorization=authorization
    )

    try:
        # Check role in profiles table
        response = (
            supabase
            .table("profiles")
            .select("role")
            .eq("id", user.id)
            .single()
            .execute()
        )

    except Exception:
        raise HTTPException(
            status_code=403,
            detail="Unable to verify admin access"
        )

    profile = response.data

    if not profile:
        raise HTTPException(
            status_code=403,
            detail="User profile not found"
        )

    if profile.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user
