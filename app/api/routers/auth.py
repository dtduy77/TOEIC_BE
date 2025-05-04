from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.core.security import create_access_token
from app.db.session import get_session
from app.schemas import user as schema_user, token as schema_token
from app.crud import user as crud_user
import firebase_admin
from firebase_admin import auth, credentials
import os
from dotenv import load_dotenv
from app.core.config import get_settings
from typing import Dict

# Initialize Firebase
if not firebase_admin._apps:
    # Load environment variables
    load_dotenv()
    settings = get_settings()

    # Create a credentials dictionary only with non-None values
    cred_dict = {
        "type": settings.TYPE,
        "project_id": settings.PROJECT_ID,
        "private_key_id": settings.PRIVATE_KEY_ID,
        "private_key": settings.PRIVATE_KEY.replace("\\n", "\n") if settings.PRIVATE_KEY else None,
        "client_email": settings.CLIENT_EMAIL,
        "client_id": settings.CLIENT_ID,
        "auth_uri": settings.AUTH_URI,
        "token_uri": settings.TOKEN_URI,
        "auth_provider_x509_cert_url": settings.AUTH_PROVIDER_X509_CERT_URL,
        "client_x509_cert_url": settings.CLIENT_X509_CERT_URL,
        "universe_domain": settings.UNIVERSE_DOMAIN
    }

    # Filter out None values
    cred_dict = {k: v for k, v in cred_dict.items() if v is not None}

    # Initialize Firebase only if we have all required credentials
    required_keys = ["type", "project_id", "private_key", "client_email"]
    if all(key in cred_dict for key in required_keys):
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        print("Warning: Firebase initialization skipped - missing required credentials")

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schema_token.Token, status_code=201)
async def register(data: schema_user.UserCreate, db: Session = Depends(get_session)):
    try:
        # Create user in Firebase
        firebase_user = auth.create_user(
            email=data.email,
            password=data.password,
            display_name=data.username
        )

        # Create user in your database (you may adjust fields as needed)
        user_data = data.dict()
        user_data["firebase_uid"] = firebase_user.uid
        user = crud_user.create(db, **user_data)

        # Create custom token for the user
        token = auth.create_custom_token(firebase_user.uid)

        return {"access_token": token.decode('utf-8'), "token_type": "bearer"}
    except auth.EmailAlreadyExistsError:
        raise HTTPException(400, "Email already exists")
    except auth.UidAlreadyExistsError:
        raise HTTPException(400, "User ID already exists")
    except Exception as e:
        raise HTTPException(500, f"Error creating user: {str(e)}")

@router.post("/login", response_model=schema_token.Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    try:
        # We can't verify passwords on the backend with Firebase
        # This endpoint is mainly for compatibility with OAuth2PasswordRequestForm
        # The actual authentication should happen on the frontend with Firebase SDK
        # Here we just verify the user exists
        user = auth.get_user_by_email(form.username)  # Using email as username
        
        # Create a custom token that the frontend can use to sign in
        token = auth.create_custom_token(user.uid)
        
        return {"access_token": token.decode('utf-8'), "token_type": "bearer"}
    except auth.UserNotFoundError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Authentication failed: {str(e)}")

@router.post("/verify-token")
async def verify_token(request: Request):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token format")

        token = auth_header.split("Bearer ")[1]
        
        try:
            # Try to verify as an ID token first
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token["uid"]
            email = decoded_token.get("email")
            return {"uid": uid, "email": email, "token_type": "id_token"}
        except Exception as e:
            # If ID token verification fails, log the error
            print(f"ID token verification failed: {str(e)}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {str(e)}")


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(request: Request) -> Dict[str, str]:
    try:
        # Get the token from the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token format")

        token = auth_header.split("Bearer ")[1]
        
        try:
            # Verify the token is valid before attempting to revoke it
            decoded_token = auth.verify_id_token(token)
            
            # In Firebase, we can't directly invalidate tokens on the server side
            # The best practice is to revoke refresh tokens for the user
            # This will force the user to re-authenticate
            auth.revoke_refresh_tokens(decoded_token["uid"])
            
            return {"message": "Successfully logged out"}
        except Exception as e:
            # Log the error but return success anyway
            print(f"Error during logout: {str(e)}")
            return {"message": "Logged out"}
            
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Logout error: {str(e)}")
        return {"message": "Logged out"}