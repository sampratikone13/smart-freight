from sqlalchemy import Column, Integer, String, Numeric, Index, UniqueConstraint
from backend.app.database import Base

class DimDate(Base):
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True, autoincrement=True)
    order_month = Column(Integer, nullable=False, index=True)
    month_name = Column(String(20), nullable=False)
    order_day = Column(Integer, nullable=False)
    order_weekday = Column(Integer, nullable=False, index=True)
    weekday_name = Column(String(20), nullable=False)
    order_hour = Column(Integer, nullable=False)
    is_weekend = Column(Integer, nullable=False)
    quarter = Column(String(10), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("order_month", "order_day", "order_weekday", "order_hour", "is_weekend", name="uq_dim_date"),
    )


class DimProduct(Base):
    __tablename__ = "dim_product"

    product_key = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(255), nullable=False, unique=True, index=True)
    category_name = Column(String(100), nullable=False, index=True)
    department_name = Column(String(100), nullable=False, index=True)
    product_price = Column(Numeric(10, 2))


class DimCustomer(Base):
    __tablename__ = "dim_customer"

    customer_key = Column(Integer, primary_key=True, autoincrement=True)
    customer_segment = Column(String(50), nullable=False, index=True)
    customer_city = Column(String(100), nullable=False, index=True)
    customer_state = Column(String(50))
    customer_country = Column(String(100))
    latitude = Column(Numeric(10, 6))
    longitude = Column(Numeric(10, 6))

    __table_args__ = (
        UniqueConstraint("customer_city", "customer_state", "customer_country", "customer_segment", name="uq_dim_customer"),
    )


class DimLocation(Base):
    __tablename__ = "dim_location"

    location_key = Column(Integer, primary_key=True, autoincrement=True)
    order_city = Column(String(100), nullable=False, index=True)
    order_state = Column(String(100), index=True)
    order_country = Column(String(100), nullable=False, index=True)
    order_region = Column(String(100), nullable=False, index=True)
    market = Column(String(50), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("order_city", "order_state", "order_country", "order_region", "market", name="uq_dim_location"),
    )


class DimShipping(Base):
    __tablename__ = "dim_shipping"

    shipping_key = Column(Integer, primary_key=True, autoincrement=True)
    shipping_mode = Column(String(50), nullable=False, index=True)
    scheduled_shipping_days = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("shipping_mode", "scheduled_shipping_days", name="uq_dim_shipping"),
    )
