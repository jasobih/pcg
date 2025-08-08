from fastapi import FastAPI, Depends, HTTPException, Request, Header, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from . import models, schemas, security
from .database import SessionLocal, engine
from .config import settings
from .security import get_current_user

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:8080",  # Allow requests from your frontend
    "http://localhost",
    "http://127.0.0.1:8080",
    "http://127.0.0.1",
    "http://51.161.134.191",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS
)

fm = FastMail(conf)

async def send_email_notification(email: List[str], subject: str, message: str):
    message = MessageSchema(
        subject=subject,
        recipients=email,
        body=message,
        subtype="html"
    )
    await fm.send_message(message)

# --- Dependencies ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Security ---
ADMIN_API_KEY = "your_super_secret_admin_key"  # Should be in env var
BLACKLISTED_WORDS = {"pills", "gun", "drugs", "escort", "gambling"}

# Rate limiting (in-memory, basic implementation)
request_counts = {}
request_timestamps = {}

def rate_limit(ip: str, max_requests: int, period_minutes: int):
    now = datetime.now()
    
    # Get current timestamp for the IP, or a very old one if not present
    timestamp = request_timestamps.get(ip, datetime.min)

    if now - timestamp > timedelta(minutes=period_minutes):
        # If the period has expired, reset the count and timestamp
        request_counts[ip] = 1
        request_timestamps[ip] = now
    else:
        # Otherwise, increment the count
        request_counts[ip] = request_counts.get(ip, 0) + 1
    
    if request_counts[ip] > max_requests:
        raise HTTPException(status_code=429, detail="Too Many Requests")

def get_admin_api_key(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid Admin API Key")

# --- Endpoints ---

@app.post("/api/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/users/register", response_model=schemas.User, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/api/users/me", response_model=schemas.User)
def update_user_me(user_update: schemas.UserBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.bio = user_update.bio
    db.commit()
    db.refresh(current_user)
    return current_user

@app.get("/api/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/gigs/me", response_model=List[schemas.Gig])
def read_my_gigs(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    gigs = db.query(models.Gig).filter(models.Gig.owner_id == current_user.id).all()
    return gigs

@app.get("/api/messages/me", response_model=List[schemas.Message])
def read_my_messages(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    messages = db.query(models.Message).filter(models.Message.sender_id == current_user.id).all()
    return messages

@app.post("/api/gigs/{gig_id}/reviews", response_model=schemas.Review, status_code=201)
async def create_review(gig_id: int, review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    gig = db.query(models.Gig).filter(models.Gig.id == gig_id).first()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")

    # You can add more complex logic here to ensure only relevant parties can review

    db_review = models.Review(**review.dict(), gig_id=gig_id, reviewer_id=current_user.id, reviewee_id=gig.owner_id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Send email notification
    reviewee = db.query(models.User).filter(models.User.id == gig.owner_id).first()
    await send_email_notification([reviewee.username], "You have a new review!", f"<p>You have received a new review for your gig: {gig.title}</p>")

    return db_review

@app.get("/api/users/{user_id}/reviews", response_model=List[schemas.Review])
def read_user_reviews(user_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).filter(models.Review.reviewee_id == user_id).all()
    return reviews

@app.post("/api/gigs/{gig_id}/complete", response_model=schemas.Gig)
def complete_gig(gig_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    gig = db.query(models.Gig).filter(models.Gig.id == gig_id).first()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")
    if gig.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to complete this gig")

    gig.status = "COMPLETED"
    db.commit()
    db.refresh(gig)
    return gig


@app.post("/api/gigs", response_model=schemas.Gig, status_code=201)
def create_gig(gig: schemas.GigCreate, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    rate_limit(current_user.username, 3, 60)  # 3 posts per hour per user

    # Keyword filter
    if any(word in gig.title.lower() or word in gig.details.lower() for word in BLACKLISTED_WORDS):
        raise HTTPException(status_code=400, detail="Post contains blacklisted words.")

    client_ip = request.client.host if request.client else None

    db_gig = models.Gig(**gig.dict(), owner_id=current_user.id, client_ip=client_ip)
    db.add(db_gig)
    db.commit()
    db.refresh(db_gig)
    return db_gig

@app.post("/api/gigs/{gig_id}/upload-image", response_model=schemas.Gig)
def upload_gig_image(gig_id: int, image: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    gig = db.query(models.Gig).filter(models.Gig.id == gig_id).first()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")
    if gig.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload an image for this gig")

    file_location = f"uploads/{image.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(image.file.read())
    image_url = f"/{file_location}"

    gig.image_url = image_url
    db.commit()
    db.refresh(gig)
    return gig

@app.post("/api/gigs/{gig_id}/messages", response_model=schemas.Message, status_code=201)
async def create_message(gig_id: int, message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    gig = db.query(models.Gig).filter(models.Gig.id == gig_id).first()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")
    
    db_message = models.Message(**message.dict(), gig_id=gig_id, sender_id=current_user.id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Send email notification
    gig_owner = db.query(models.User).filter(models.User.id == gig.owner_id).first()
    await send_email_notification([gig_owner.username], f"New message about your gig: {gig.title}", f"<p>You have a new message from {current_user.username}:</p><p>{message.content}</p>")

    return db_message

@app.get("/api/gigs/{gig_id}/messages", response_model=List[schemas.Message])
def read_messages(gig_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    gig = db.query(models.Gig).filter(models.Gig.id == gig_id).first()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")

    if current_user.id != gig.owner_id:
         raise HTTPException(status_code=403, detail="Not authorized to view these messages")

    messages = db.query(models.Message).filter(models.Message.gig_id == gig_id).all()
    return messages

@app.get("/api/gigs", response_model=List[schemas.Gig])
def read_gigs(db: Session = Depends(get_db), search: Optional[str] = None, gig_type: Optional[str] = None, suburb: Optional[str] = None):
    query = db.query(models.Gig).join(models.User).filter(models.Gig.status == "LIVE")
    if search:
        query = query.filter(models.Gig.title.contains(search) | models.Gig.details.contains(search))
    if gig_type:
        query = query.filter(models.Gig.gig_type == gig_type)
    if suburb:
        query = query.filter(models.Gig.suburb.contains(suburb))
    
    gigs = query.order_by(models.Gig.created_at.desc()).all()
    return [schemas.Gig.from_orm(gig) for gig in gigs]

@app.post("/api/gigs/{gig_id}/report", status_code=200)
def report_gig(gig_id: int, request: Request, db: Session = Depends(get_db)):
    rate_limit(f"{request.client.host}_{gig_id}", 1, 60 * 24) # 1 report per gig per IP per day

    gig = db.query(models.Gig).filter(models.Gig.id == gig_id).first()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")

    gig.report_count += 1
    if gig.report_count >= 3:
        gig.status = "FLAGGED"
    
    db.commit()
    return {"message": "Gig reported successfully"}

@app.get("/api/admin/flagged", response_model=List[schemas.Gig], dependencies=[Depends(get_admin_api_key)])
def get_flagged_gigs(db: Session = Depends(get_db)):
    gigs = db.query(models.Gig).filter(models.Gig.status == "FLAGGED").all()
    return gigs

@app.post("/api/admin/gigs/{gig_id}/approve", response_model=schemas.Gig, dependencies=[Depends(get_admin_api_key)])
def approve_gig(gig_id: int, db: Session = Depends(get_db)):
    gig = db.query(models.Gig).filter(models.Gig.id == gig_id).first()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")
    
    gig.status = "LIVE"
    gig.report_count = 0
    db.commit()
    db.refresh(gig)
    return gig

@app.delete("/api/admin/gigs/{gig_id}", status_code=200, dependencies=[Depends(get_admin_api_key)])
def delete_gig(gig_id: int, db: Session = Depends(get_db)):
    gig = db.query(models.Gig).filter(models.Gig.id == gig_id).first()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")
        
    gig.status = "DELETED"
    db.commit()
    return {"message": "Gig deleted successfully"}
