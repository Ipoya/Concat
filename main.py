from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, get_db, SessionLocal
from app.core.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models import models
from app.schemas import schemas

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Soccer Field Booking System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize time slots
def init_time_slots(db: Session):
    slots = [
        {"shift_name": "Shift 1", "start_time": "06:00", "end_time": "07:30", "price": 500000},
        {"shift_name": "Shift 2", "start_time": "07:30", "end_time": "09:00", "price": 500000},
        {"shift_name": "Shift 3", "start_time": "09:00", "end_time": "10:30", "price": 400000},
        {"shift_name": "Shift 4", "start_time": "10:30", "end_time": "12:00", "price": 400000},
        {"shift_name": "Shift 5", "start_time": "13:00", "end_time": "14:30", "price": 400000},
        {"shift_name": "Shift 6", "start_time": "14:30", "end_time": "16:00", "price": 400000},
        {"shift_name": "Shift 7", "start_time": "16:00", "end_time": "17:30", "price": 600000},
        {"shift_name": "Shift 8", "start_time": "18:30", "end_time": "20:00", "price": 800000},
        {"shift_name": "Shift 9", "start_time": "20:00", "end_time": "21:30", "price": 800000},
        {"shift_name": "Shift 10", "start_time": "21:30", "end_time": "23:00", "price": 800000},
    ]
    
    for slot in slots:
        db_slot = db.query(models.TimeSlot).filter(models.TimeSlot.shift_name == slot["shift_name"]).first()
        if not db_slot:
            db_slot = models.TimeSlot(**slot)
            db.add(db_slot)
    db.commit()

@app.get("/")
async def root():
    return {
        "message": "Welcome to Soccer Field Booking System API",
        "documentation": "/docs",
        "available_endpoints": {
            "public": [
                "GET /time-slots - View all available time slots",
                "POST /bookings - Create a new booking"
            ],
            "authentication": [
                "POST /token - Login to get access token"
            ],
            "admin": [
                "GET /admin/bookings - View all bookings (requires auth)",
                "PUT /admin/bookings/{booking_id}/status - Update booking status (requires auth)"
            ],
            "inventory": [
                "POST /admin/inventory - Create inventory check (requires auth)",
                "GET /admin/inventory/latest - View latest inventory (requires auth)"
            ]
        }
    }

# Authentication endpoints
@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Public endpoints
@app.get("/time-slots", response_model=List[schemas.TimeSlot])
async def get_time_slots(db: Session = Depends(get_db)):
    return db.query(models.TimeSlot).all()

@app.post("/bookings", response_model=schemas.Booking)
async def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    # Check if slot exists
    time_slot = db.query(models.TimeSlot).filter(models.TimeSlot.id == booking.time_slot_id).first()
    if not time_slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    
    # Check if slot is already booked for the given date
    existing_booking = db.query(models.Booking).filter(
        models.Booking.booking_date == booking.booking_date,
        models.Booking.time_slot_id == booking.time_slot_id,
        models.Booking.status.in_([schemas.BookingStatus.BOOKED, schemas.BookingStatus.DEPOSIT_PAID])
    ).first()
    
    if existing_booking:
        raise HTTPException(status_code=400, detail="This time slot is already booked for the selected date")
    
    db_booking = models.Booking(**booking.dict())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

# Admin endpoints
@app.get("/admin/bookings", response_model=List[schemas.Booking])
async def get_all_bookings(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [schemas.UserRole.ADMIN, schemas.UserRole.MANAGER, schemas.UserRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Booking).offset(skip).limit(limit).all()

@app.put("/admin/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: int,
    status_update: schemas.BookingStatusUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [schemas.UserRole.ADMIN, schemas.UserRole.MANAGER, schemas.UserRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = status_update.status
    booking.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Booking status updated successfully"}

# Inventory endpoints
@app.post("/admin/inventory", response_model=schemas.Inventory)
async def create_inventory_check(
    inventory: schemas.InventoryCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [schemas.UserRole.ADMIN, schemas.UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_inventory = models.Inventory(**inventory.dict(), updated_by=current_user.id)
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

@app.get("/admin/inventory/latest", response_model=schemas.Inventory)
async def get_latest_inventory(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [schemas.UserRole.ADMIN, schemas.UserRole.MANAGER, schemas.UserRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    latest_inventory = db.query(models.Inventory).order_by(models.Inventory.check_date.desc()).first()
    if not latest_inventory:
        raise HTTPException(status_code=404, detail="No inventory records found")
    return latest_inventory

# Initialize time slots on startup
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        init_time_slots(db)
    finally:
        db.close()
