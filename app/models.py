from sqlalchemy import Column, Integer, Date, Float, Boolean

from database import Base


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    order_num = Column(Integer, index=True)
    price_usd = Column(Float)
    delivery_time = Column(Date)
    price_rub = Column(Float)
    notify = Column(Boolean, default=False)
