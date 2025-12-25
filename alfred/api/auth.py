from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, Dict
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os
import jwt
from alfred.core.interfaces import MemoryStorage
from alfred.core.entities import UserProfile

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: str
    password: str

class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    work_type: Optional[str] = None
    voice_id: Optional[str] = None
    personality_prompt: Optional[str] = None
    interaction_type: Optional[str] = None

# Helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency placeholder (injected in main.py usually, but here we can't easily access the global 'alfred.storage' without circular deps or global var)
# For this clean architecture, we'll assume the storage provider is passed or available.
# To keep it simple, we will use a global reference that main.py sets, or dependency injection.
# Let's use a workaround: The `storage` will be set on the router app state or similar.
# Actually, proper FastAPI way is dependency.
# constructing a get_storage dependency that imports from main implies circular import.
# We will define `get_storage` in main.py and pass it to routes, or use `request.app.state.storage`.

def get_storage():
    from alfred.main import storage_provider
    if not storage_provider:
        raise HTTPException(status_code=503, detail="Storage not available")
    return storage_provider

# Routes
@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate):
    storage = get_storage()
    # Simple user_id gen
    user_id = str(hash(user_data.email)) # In PROD use UUID
    hashed_pw = get_password_hash(user_data.password)
    
    success = storage.create_user(user_id, user_data.email, hashed_pw)
    if not success:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    access_token = create_access_token(data={"sub": user_data.email, "user_id": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    storage = get_storage()
    creds = storage.get_user_credentials(form_data.username) # username is email
    if not creds or not verify_password(form_data.password, creds["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username, "user_id": creds["user_id"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Current User Dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.get("/profile")
async def get_profile(user_id: str = Depends(get_current_user)):
    storage = get_storage()
    profile = storage.get_user_profile(user_id)
    return profile or {}

@router.put("/profile")
async def update_profile(profile_update: ProfileUpdate, user_id: str = Depends(get_current_user)):
    storage = get_storage()
    # Filter None values
    update_data = {k: v for k, v in profile_update.dict().items() if v is not None}
    storage.update_user_profile(user_id, update_data)
    return {"status": "updated", "profile": update_data}
