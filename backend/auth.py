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


def get_current_user(

    authorization: str = Header(None)

):

    if not authorization:

        raise HTTPException(

            status_code=401,

            detail=
                "Authorization header is missing"
        )


    if not authorization.startswith(
        "Bearer "
    ):

        raise HTTPException(

            status_code=401,

            detail=
                "Invalid authorization format"
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


        if not response.user:

            raise HTTPException(

                status_code=401,

                detail=
                    "Invalid or expired token"
            )


        return response.user


    except Exception:

        raise HTTPException(

            status_code=401,

            detail=
                "Authentication failed"
        )
