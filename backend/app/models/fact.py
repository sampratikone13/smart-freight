from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.database import Base

class FactShipping(Base):
    __tablename__ = "fact_shipping"

    shipping_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys referencing Dimensions
    date_key = Column(Integer, ForeignKey("dim_date.date_key", ondelete="CASCADE"), nullable=False, index=True)
    product_key = Column(Integer, ForeignKey("dim_product.product_key", ondelete="CASCADE"), nullable=False, index=True)
    customer_key = Column(Integer, ForeignKey("dim_customer.customer_key", ondelete="CASCADE"), nullable=False, index=True)
    location_key = Column(Integer, ForeignKey("dim_location.location_key", ondelete="CASCADE"), nullable=False, index=True)
    shipping_key = Column(Integer, ForeignKey("dim_shipping.shipping_key", ondelete="CASCADE"), nullable=False, index=True)

    # Measures
    order_quantity = Column(Integer, nullable=False)
    product_price = Column(Numeric(10, 2))
    discount_amount = Column(Numeric(10, 2))
    discount_rate = Column(Numeric(6, 4))
    sales_amount = Column(Numeric(10, 2))
    order_item_total = Column(Numeric(10, 2))
    profit_amount = Column(Numeric(10, 2))
    profit_ratio = Column(Numeric(6, 4))
    scheduled_shipping_days = Column(Integer, nullable=False, index=True)
    actual_shipping_days = Column(Integer, nullable=False, index=True)
    late_delivery_risk = Column(Integer, nullable=False, index=True)
    
    # Degenerate Attributes
    payment_type = Column(String(50), index=True)
    order_status = Column(String(50), index=True)

    # Relationships
    dim_date = relationship("DimDate", backref="facts")
    dim_product = relationship("DimProduct", backref="facts")
    dim_customer = relationship("DimCustomer", backref="facts")
    dim_location = relationship("DimLocation", backref="facts")
    dim_shipping = relationship("DimShipping", backref="facts")

    __table_args__ = (
        Index("idx_fact_loc_ship", "location_key", "shipping_key"),
        Index("idx_fact_date_loc", "date_key", "location_key"),
        Index("idx_fact_prod_date", "product_key", "date_key"),
    )
