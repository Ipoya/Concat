from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class BookingStatus(str, Enum):
    BOOKED = "Booked"
    DEPOSIT_PAID = "Deposit Paid"
    DONE = "Done"
    RESCHEDULED = "Rescheduled"
    CANCELLED = "Cancelled"

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OWNER = "owner"

class TimeSlotBase(BaseModel):
    shift_name: str
    start_time: str
    end_time: str
    price: float

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlot(TimeSlotBase):
    id: int

    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    customer_name: str
    email: EmailStr
    phone: str
    booking_date: date
    time_slot_id: int
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    time_slot: TimeSlot

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    last_login: Optional[datetime] = None
    last_logout: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class InventoryBase(BaseModel):
    balls: int
    shoes: int
    jerseys: int
    gloves: int
    check_date: date

class InventoryCreate(InventoryBase):
    pass

class Inventory(InventoryBase):
    id: int
    updated_by: int

    class Config:
        from_attributes = True

class BookingStatusUpdate(BaseModel):
    status: BookingStatus
