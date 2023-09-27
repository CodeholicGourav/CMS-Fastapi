import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from database import Base, SessionLocal


class FrontendUser(Base):
    """
    The `FrontendUser` class represents a table in a database that stores information about frontend users.
    """
    __tablename__ = 'frontendusers'

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    verification_token = Column(String(255), nullable=True, unique=True)
    email_verified_at = Column(DateTime, nullable=True)
    storage_token = Column(Text, nullable=True)
    storage_platform = Column(String(10), nullable=True)
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="Asia/Kolkata", comment="Should be a valid codename from table `timezones`")
    active_plan = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    profile_photo = Column(String(50), nullable=True)
    social_token = Column(Text, nullable=True)
    social_platform = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscription = relationship("Subscription", foreign_keys=active_plan)

    def __repr__(self):
        return f"<FrontendUser(id={self.id}, username='{self.username}')>"

    def __str__(self):
        return f"FrontendUser: {self.username}"


class FrontendToken(Base):
    """
    Represents a token for frontend users.
    """
    __tablename__ = 'frontendtokens'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("frontendusers.id"))
    details = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('FrontendUser', foreign_keys=user_id)

    def __repr__(self):
        return f"FrontendToken(id={self.id}, token='{self.token}', user_id={self.user_id}, details='{self.details}')"
    
    def __str__(self):
        return f"Id: {self.id}\nToken: {self.token}\nUser Id: {self.user_id}\nDetails: {self.details}"


class Timezone(Base):
    """
    The `Timezone` class represents a table in a database that stores information about different timezones.
    It inherits from the `Base` class, which is the base class for all SQLAlchemy models.
    """
    __tablename__ = 'timezones'

    id = Column(Integer, primary_key=True, index=True)
    timezone_name = Column(String(255))
    code = Column(String(255), unique=True)
    time_difference = Column(String(50))

    def __repr__(self):
        pass

    def __str__(self):
        pass


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
     
    id = Column(Integer, primary_key=True, index=True)
    ouid = Column(String(50), index=True, unique=True)
    user_id = Column(Integer, ForeignKey("frontendusers.id"))
    total_amount = Column(Float)
    final_amount = Column(Float)
    currency = Column(String(50))
    conversion_rate = Column(Float)
    coupon_amount = Column(Float)
    coupon_code = Column(String(50))
    coupon_id = Column(Integer, ForeignKey("coupons.id"))
    status = Column(Text, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("FrontendUser", foreign_keys=user_id)
    coupon = relationship("Coupon", foreign_keys=coupon_id)

    def __repr__(self):
        pass

    def __str__(self):
        pass


class Transaction(Base):
    """
    The `Transaction` class represents a table in a database that stores information about transactions.
    It contains fields to store details such as the order ID, status, payment gateway, payment ID, and timestamps for creation and update.
    """
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    status = Column(String(50))
    payment_gateway = Column(String(50))
    payment_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"Transaction(id={self.id}, order_id={self.order_id}, status='{self.status}', payment_gateway='{self.payment_gateway}', payment_id='{self.payment_id}', created_at='{self.created_at}', updated_at='{self.updated_at}')"

    def __str__(self):
        return f"Transaction ID: {self.id}\nOrder ID: {self.order_id}\nStatus: {self.status}\nPayment Gateway: {self.payment_gateway}\nPayment ID: {self.payment_id}\nCreated At: {self.created_at}\nUpdated At: {self.updated_at}"


class OrderProduct(Base):
    """
    The `OrderProduct` class represents a table in a database that stores information about products in an order.
    """

    __tablename__ = 'order_products'

    id = Column(Integer, primary_key=True)
    product_price = Column(Integer)
    product_sale_price = Column(Integer)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('subscriptions.id'))
    quantity = Column(Integer, default=1)

    order = relationship("Order", foreign_keys=order_id)
    product = relationship("Subscription", foreign_keys=product_id)

    def __repr__(self):
        return f"OrderProduct(id={self.id}, product_price={self.product_price}, product_sale_price={self.product_sale_price}, order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})"

    def __str__(self):
        return f"OrderProduct(id={self.id}, product_price={self.product_price}, product_sale_price={self.product_sale_price}, order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})"


