from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date, Float, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.core.database import Base

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OWNER = "owner"

class BookingStatus(enum.Enum):
    BOOKED = "Booked"
    DEPOSIT_PAID = "Deposit Paid"
    DONE = "Done"
    RESCHEDULED = "Rescheduled"
    CANCELLED = "Cancelled"

class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)
    shift_name = Column(String, unique=True)
    start_time = Column(String)
    end_time = Column(String)
    price = Column(Float)

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    email = Column(String)
    phone = Column(String)
    booking_date = Column(Date, index=True)
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"))
    notes = Column(String, nullable=True)
    status = Column(String, default=BookingStatus.BOOKED.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    time_slot = relationship("TimeSlot")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    last_login = Column(DateTime, nullable=True)
    last_logout = Column(DateTime, nullable=True)

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    balls = Column(Integer, default=0)
    shoes = Column(Integer, default=0)
    jerseys = Column(Integer, default=0)
    gloves = Column(Integer, default=0)
    check_date = Column(Date)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User")
