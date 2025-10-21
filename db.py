import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, BigInteger, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database engine and create tables"""
    Base.metadata.create_all(engine)
    return engine, SessionLocal

# ========== MODELS ==========
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    field = Column(String(50), nullable=False)
    slot = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

# Create tables on startup (called from bot.py)
# Base.metadata.create_all(engine)  # Bu yerda emas, bot.py dan chaqiriladi

# ========== DATABASE FUNCTIONS ==========
def get_session():
    """Get database session"""
    return SessionLocal()

def add_user(telegram_id, name, surname, phone):
    """Add new user"""
    session = get_session()
    try:
        user = User(telegram_id=telegram_id, name=name, surname=surname, phone=phone)
        session.add(user)
        session.commit()
        return user
    except IntegrityError:
        session.rollback()
        return None
    finally:
        session.close()

def get_user(telegram_id):
    """Get user by telegram_id"""
    session = get_session()
    try:
        return session.query(User).filter(User.telegram_id == telegram_id).first()
    finally:
        session.close()

def get_user_by_id(user_id):
    """Get user by internal user_id (for admin)"""
    session = get_session()
    try:
        return session.query(User).filter(User.id == user_id).first()
    finally:
        session.close()

def add_booking(user_id, date, field, slot):
    """Add new booking and return ID"""
    session = get_session()
    try:
        exists = session.query(Booking).filter(
            Booking.date == date,
            Booking.field == field,
            Booking.slot == slot
        ).first()
        if exists:
            return None

        booking = Booking(user_id=user_id, date=date, field=field, slot=slot)
        session.add(booking)
        session.commit()
        session.refresh(booking)

        from excel_manager import append_booking_to_excel
        append_booking_to_excel(booking.id)
        return booking.id
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return None
    finally:
        session.close()

def get_user_bookings(user_id):
    """Get all bookings for user"""
    session = get_session()
    try:
        return session.query(Booking).filter(Booking.user_id == user_id).order_by(Booking.date, Booking.slot).all()
    finally:
        session.close()

def get_booking_by_id(booking_id):
    """Get booking by ID"""
    session = get_session()
    try:
        return session.query(Booking).filter(Booking.id == booking_id).first()
    finally:
        session.close()

def delete_booking(booking_id):
    """Delete booking by ID"""
    session = get_session()
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            from excel_manager import delete_booking_from_excel
            delete_booking_from_excel(booking_id)
            session.delete(booking)
            session.commit()
            return True
        return False
    finally:
        session.close()

def get_booked_slots(date, field):
    """Get booked slots for specific date and field"""
    session = get_session()
    try:
        bookings = session.query(Booking.slot).filter(
            Booking.date == date,
            Booking.field == field
        ).all()
        return [b[0] for b in bookings]
    finally:
        session.close()

def get_all_bookings():
    """Get all bookings ordered by date descending"""
    session = get_session()
    try:
        return session.query(Booking).order_by(Booking.date.desc(), Booking.slot).all()
    finally:
        session.close()

def get_today_stats():
    """Get today's statistics"""
    session = get_session()
    try:
        today = datetime.date.today()
        return session.query(
            Booking.field,
            func.count(Booking.id)
        ).filter(Booking.date == today).group_by(Booking.field).all()
    finally:
        session.close()

def get_month_stats():
    """Get month statistics"""
    session = get_session()
    try:
        month_start = datetime.date.today().replace(day=1)
        count = session.query(func.count(Booking.id)).filter(
            Booking.date >= month_start
        ).scalar()
        return count or 0
    finally:
        session.close()

def get_today_revenue():
    """Get today's revenue based on PRICES from config"""
    session = get_session()
    try:
        today = datetime.date.today()
        bookings = session.query(Booking).filter(Booking.date == today).all()
        from config import PRICES
        revenue = sum(PRICES.get(b.field, 0) for b in bookings)
        return revenue
    finally:
        session.close()

def get_month_revenue():
    """Get month's revenue based on PRICES from config"""
    session = get_session()
    try:
        month_start = datetime.date.today().replace(day=1)
        bookings = session.query(Booking).filter(Booking.date >= month_start).all()
        from config import PRICES
        revenue = sum(PRICES.get(b.field, 0) for b in bookings)
        return revenue
    finally:
        session.close()