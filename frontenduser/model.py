import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,String, Text
)
from sqlalchemy.orm import relationship

from database import Base, SessionLocal


class FrontendUser(Base):
    """
    The `FrontendUser` class represents a table in a database that stores information about frontend users.
    It contains various fields to store user details such as name, email, password, and other optional information.
    The class also defines relationships with other tables in the database.
    """

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
        String(255), 
    )
    verification_token = Column(
        String(255), 
        nullable=True,
        unique=True
    )
    email_verified_at = Column(
        DateTime(255), 
        nullable=True
    )
    storage_token = Column(
        Text,
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
        String(50),
        default="Asia/Kolkata",
        comment = "Should be a valid codename from table `timezones`",
    )
    active_plan = Column(
        Integer,
        ForeignKey("subscriptions.id"),
        nullable=True
    )
    profile_photo = Column(
        String(50),
        nullable=True
    )
    social_token = Column(
        Text,
        nullable=True
    )
    social_platform = Column(
        String(10),
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

    # Relationships
    # orders = relationship("FrontendUser", back_populates="user")


class FrontendToken(Base):
    """
    Represents a token for frontend users.
    """
     
    __tablename__ = 'frontendtokens'

    id = Column(
        Integer, 
        primary_key=True,
        index=True
    )
    token = Column(
        String(255), 
        unique=True, 
        index=True,
        nullable=False
    )
    user_id = Column(
        Integer, 
        ForeignKey("frontendusers.id")
    )
    details = Column(
        String(255),
        nullable=True
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    expire_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

    # Relationships
    user = relationship('FrontendUser', foreign_keys=user_id)


class Timezone(Base):
    """
    The `Timezone` class represents a table in a database that stores information about different timezones.
    It inherits from the `Base` class, which is the base class for all SQLAlchemy models.
    """
     
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
    """
    Reads data from a CSV file and inserts it into the Timezone table in the database.

    :return: None
    """
    print("Creating timezone data...")
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


class Order(Base):
    """
    Represents a table in a database that stores information about orders.
    Inherits from the Base class, which is the base class for all SQLAlchemy models.
    """
    __tablename__ = 'orders'
     
    id = Column(
        Integer, 
        primary_key=True,
        index=True
    )
    ouid = Column(
        String(50), 
        index=True,
        unique=True, 
    )
    user_id = Column(
        Integer, 
        ForeignKey("frontendusers.id")
    )
    total_amount = Column(
        Float
    )
    final_amount = Column(
        Float
    )
    currency = Column(
        String(50)
    )
    conversion_rate = Column(
        Float
    )
    coupon_amount = Column(
        Float
    )
    cuoupon_code = Column(
        String(50)
    )
    coupon_id = Column(
        Integer,
        ForeignKey("coupons.id")
    )
    status = Column(
        Text,
        default="pending"
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

    # Relationships
    user = relationship("FrontendUser", foreign_keys=user_id)
    coupon = relationship("Coupon", foreign_keys=coupon_id)


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(
        Integer,
        primary_key=True 
    )
    order_id = Column(
        Integer,
        ForeignKey('orders.id'),
    )
    status = Column(
        String(50)
    )
    payment_gateway = Column(
        String(50)
    )
    payment_id = Column(
        String(255)
    )
    # billing_address = Column(
    #     Text
    # )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime,
        default = datetime.utcnow
    )


class OrderProduct(Base):
    __tablename__ = 'order_products'

    id = Column(
        Integer,
        primary_key=True 
    )
    product_price = Column(
        Integer
    )
    product_sale_price = Column(
        Integer
    )
    order_id = Column(
        Integer,
        ForeignKey('orders.id')
    )
    product__id = Column(
        Integer,
        ForeignKey('subscriptions.id')
    )
    quantity = Column(
        Integer,
        default=1
    )



