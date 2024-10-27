from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from ..auth.auth_service import auth_service

security = HTTPBearer()

async def verify_token(request: Request):
    if request.url.path in ["/auth/token", "/auth/register", "/auth/refresh"]:
        return
        
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="
[Timestamp: 2024/10/27 09:23:57]

**user**: Continue 
[Timestamp: 2024/10/27 09:24:02]

**ai**: I'll continue with the authentication implementation:

4. Continuing with auth middleware (`backend/middleware/auth_middleware.py`):

```python
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return await auth_service.get_current_user(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )