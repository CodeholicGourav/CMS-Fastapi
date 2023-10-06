"""
frontenduser/model.py
Author: Gourav Sahu
Date: 23/09/2023
"""
import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean, Column, DateTime, exc, Float,
    ForeignKey, Integer,String, Text
)
from sqlalchemy.orm import relationship

from database import Base, SessionLocal


class FrontendUser(Base):
    """
    Represents a table in a database that stores information about frontend users.
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
    timezone = Column(
        String(50),
        default="Asia/Kolkata",
        comment="Should be a valid codename from table `timezones`"
    )
    active_plan = Column(
        Integer,
        ForeignKey("subscriptions.id"),
        nullable=True
    )
    profile_photo = Column(String(50), nullable=True)
    social_token = Column(Text, nullable=True)
    social_platform = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    subscription = relationship("Subscription", foreign_keys=active_plan)


    def __repr__(self):
        """String representation of object"""
        return (
            "<FrontendUser("
                f"id={self.id}, "
                f"username='{self.username}'"
            ")>"
        )

    def __str__(self):
        """String representation of object"""
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
        """String representation of object"""
        return (
            "FrontendToken("
                f"id={self.id}, "
                f"token='{self.token}', "
                f"user_id={self.user_id}, "
                f"details='{self.details}'"
            ")"
        )

    def __str__(self):
        """String representation of object"""
        return f"FrontendToken: {self.token}"


class Timezone(Base):
    """
    Represents a table that stores information about different timezones.
    """
    __tablename__ = 'timezones'

    id = Column(Integer, primary_key=True, index=True)
    timezone_name = Column(String(255))
    code = Column(String(255), unique=True)
    time_difference = Column(String(50))

    def __repr__(self):
        """String representation of object"""
        return (
            "Timezone("
                f"id={self.id}, "
                f"timezone_name='{self.timezone_name}', "
                f"code='{self.code}', "
                f"time_difference='{self.time_difference}'"
            ")"
        )

    def __str__(self):
        """String representation of object"""
        return f"Timezone: {self.timezone_name}'"


def create_timezones():
    """
    Reads data from a CSV file and 
    inserts it into the Timezone table in the database.
    """
    print("Creating timezone data...")
    csv_file_path = Path(__file__).parent.parent / "timezones.csv"

    try:
        sql = SessionLocal()
        with open(csv_file_path, "r", newline="", encoding="UTF-8") as csvfile:
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
                sql.add(timezone_entry)
        sql.commit()
    except exc.IntegrityError:
        sql.rollback()
    except csv.Error as error:
        sql.rollback()
        raise error
    finally:
        sql.close()


class Order(Base):
    """
    Represents a table in a database that stores information about orders.
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
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("FrontendUser", foreign_keys=user_id)
    coupon = relationship("Coupon", foreign_keys=coupon_id)

    def __repr__(self):
        """String representation of object"""
        return (
            "Order("
                f"id={self.id}, "
                f"ouid={self.ouid}, "
                f"user_id={self.user_id}, "
                f"total_amount={self.total_amount}, "
                f"final_amount={self.final_amount}, "
                f"currency={self.currency}, "
                f"conversion_rate={self.conversion_rate}, "
                f"coupon_amount={self.coupon_amount}, "
                f"coupon_code={self.coupon_code}, "
                f"coupon_id={self.coupon_id}, "
                f"status={self.status}, "
                f"created_at={self.created_at}, "
                f"updated_at={self.updated_at}"
            ")"
        )
    def __str__(self):
        """String representation of object"""
        return f"Order: {self.ouid}"


class Transaction(Base):
    """
    Represents a table in a database that stores information about transactions.
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
        """String representation of object"""
        return (
            "Transaction("
                f"id={self.id}, "
                f"order_id={self.order_id}, "
                f"status='{self.status}', "
                f"payment_gateway='{self.payment_gateway}', "
                f"payment_id='{self.payment_id}', "
                f"created_at='{self.created_at}', "
                f"updated_at='{self.updated_at}'"
            ")"
        )

    def __str__(self):
        """String representation of object"""
        return (
            "Transaction("
                f"id={self.id}, "
                f"order_id={self.order_id}, "
                f"status='{self.status}', "
                f"payment_gateway='{self.payment_gateway}', "
                f"payment_id='{self.payment_id}', "
                f"created_at='{self.created_at}', "
                f"updated_at='{self.updated_at}'"
            ")"
        )


class OrderProduct(Base):
    """
    Represents a table that stores information about products in an order.
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
        """String representation of object"""
        return (
            "OrderProduct("
                f"id={self.id}, "
                f"product_price={self.product_price}, "
                f"product_sale_price={self.product_sale_price}, "
                f"order_id={self.order_id}, "
                f"product_id={self.product_id}, "
                f"quantity={self.quantity}"
            ")"
        )

    def __str__(self):
        """String representation of object"""
        return (
            "OrderProduct("
                f"id={self.id}, "
                f"product_price={self.product_price}, "
                f"product_sale_price={self.product_sale_price}, "
                f"order_id={self.order_id}, "
                f"product_id={self.product_id}, "
                f"quantity={self.quantity}"
            ")"
        )
