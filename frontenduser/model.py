from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from database import Base, SessionLocal
from datetime import datetime
from pathlib import Path
import csv


class FrontendUser(Base):
    __tablename__ = 'frontendusers'

    id = Column(
        Integer,
        primary_key=True, 
        index=True
    )
    uuid = Column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True
    )
    first_name = Column(
        String(50),
        nullable=True
    )
    last_name = Column(
        String(50),
        nullable=True
    )
    username = Column(
        String(50), 
        unique=True, 
        index=True
    )
    email = Column(
        String(255), 
        unique=True, 
        index=True
    )
    password = Column(
        String, 
    )
    verification_token = Column(
        String, 
        nullable=True,
        unique=True
    )
    email_verified_at = Column(
        DateTime, 
        nullable=True
    )
    storage_token = Column(
        String,
        nullable=True
    )
    storage_platform = Column(
        String(10),
        nullable=True
    )
    language = Column(
        String(10),
        default="en"
    )
    timezone = Column(
        String(10),
        default="Asia/Kolkata"
    )
    active_plan = Column(
        String,
        nullable=True
    )
    profile_photo = Column(
        String,
        nullable=True
    )
    social_token = Column(
        String,
        nullable=True
    )
    social_platform = Column(
        String,
        nullable=True
    )
    is_active = Column(
        Boolean, 
        default=True
    )
    is_deleted = Column(
        Boolean, 
        default=False
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow
    )


class FrontendToken(Base):
    __tablename__ = 'frontendtokens'

    id = Column(
        Integer, 
        primary_key=True,
        index=True
    )
    token = Column(
        String, 
        unique=True, 
        index=True,
        nullable=False
    )
    user_id = Column(
        Integer, 
        ForeignKey("frontendusers.id")
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    expire_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

    user = relationship('FrontendUser', foreign_keys=user_id)


class Timezone(Base):
    __tablename__ = 'timezones'

    id = Column(
        Integer,
        primary_key=True, 
        index=True
    )
    timezone_name = Column(
        String(255)
    )
    code = Column(
        String(255),
        unique=True
    )
    time_difference = Column(
        String(50)
    )

def create_timezones():
    print("creating timezone data...")
    csv_file_path = Path(__file__).parent.parent / "timezones.csv"

    try:
        db = SessionLocal()
        with open(csv_file_path, "r", newline="") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                name = row["Name"]
                code = row["Code"]
                time_difference = row["Difference"]

                timezone_entry = Timezone(
                    timezone_name=name, 
                    code=code, 
                    time_difference=time_difference
                )
                db.add(timezone_entry)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

