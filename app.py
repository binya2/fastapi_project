from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import random

# FastAPI app initialization
app = FastAPI()

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")

# Database setup (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./db.sqlite"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, index=True, unique=True)
    password = Column(String)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Pydantic model for user input validation
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    class Config:
        orm_mode = True

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Server status route with HTML
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "message": "Welcome to the FastAPI server!"}
    )

# Register new user route with HTML
@app.post("/register", response_class=HTMLResponse)
async def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Create a new user in the database
    db_user = User(username=user.username, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return templates.TemplateResponse(
        "register_success.html",
        {"request": request, "username": db_user.username, "email": db_user.email}
    )

# Get all users route
@app.get("/users", response_class=HTMLResponse)
async def get_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

# Generate random number route with HTML
@app.post("/random", response_class=HTMLResponse)
async def generate_random(min: int, max: int, request: Request):
    if min >= max:
        raise HTTPException(status_code=400, detail="min must be less than max")
    random_number = random.randint(min, max)
    return templates.TemplateResponse(
        "random.html",
        {"request": request, "min": min, "max": max, "random_number": random_number}
    )
