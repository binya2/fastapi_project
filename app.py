from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import random

# FastAPI app
app = FastAPI()

# Database setup
DATABASE_URL = "sqlite:///db.sqlite"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Models
class User(Base):
    __tablename__ = "users"
    email = Column(String(120), primary_key=True, nullable=False, unique=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)


# Create tables in the database
Base.metadata.create_all(bind=engine)


# Pydantic models for request and response
class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr
    password: str

    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    email: EmailStr
    username: str

    class Config:
        orm_mode = True


class RandomRequest(BaseModel):
    min: int
    max: int


# Dependency for database session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoints
@app.get("/")
async def status() -> dict:
    return {
        "exists": True,
        "routes": [
            {"path": "/", "method": "GET", "description": "Get server status"},
            {
                "path": "/register",
                "method": "POST",
                "description": "Register a new user",
                "parameters": {"username": "string", "email": "string", "password": "string"},
            },
            {"path": "/users", "method": "GET", "description": "Get all registered users"},
            {
                "path": "/random",
                "method": "POST",
                "description": "Generate a random number",
                "parameters": {"min": "int", "max": "int"},
            },
        ],
    }


@app.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")
    new_user = User(username=user.username, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users")
async def list_users(db: Session = Depends(get_db)) -> dict:
    users = db.query(User).all()
    return {"users": users}


@app.post("/random")
async def random_number(req: RandomRequest) -> dict:
    if req.min >= req.max:
        raise HTTPException(status_code=400, detail="min must be less than max")
    return {"random_number": random.randint(req.min, req.max)}
