from datetime import datetime

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

from sqlalchemy.orm import Session

from starlette import status
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from models import Base, Order
from database import engine, SessionLocal, get_db
from utils import get_google_sheet, get_usd_rate, send_message_to_telegram

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
async def admin(request: Request, db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "orders": orders}
    )


@app.get("/update", response_class=HTMLResponse)
async def update():
    await update_backgound()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.on_event("startup")
@repeat_every(seconds=60*60)
async def update_backgound():
    with SessionLocal() as session:
        usd_rate = get_usd_rate()
        orders_from_db = session.query(Order) \
            .with_entities(Order.order_num).all()
        orders_from_db = [order[0] for order in orders_from_db]
        orders = get_google_sheet()
        orders_from_sheet = []
        for order in orders[1:]:
            order_num = int(order[1])
            price_usd = float(order[2].replace(',', '.'))
            delivery_time = datetime.strptime(order[3], '%d.%m.%Y').date()
            price_rub = price_usd * usd_rate
            price_rub = round(price_rub, 3)
            orders_from_sheet.append(order_num)
            if order_num not in orders_from_db:
                order_model = Order()
                order_model.order_num = order_num
                order_model.delivery_time = delivery_time
                order_model.price_usd = price_usd
                order_model.price_rub = price_rub
            else:
                order_model = session.query(Order) \
                    .filter(Order.order_num == order_num).first()
                order_model.delivery_time = delivery_time
            session.add(order_model)
        if orders_to_delete := set(orders_from_db) - set(orders_from_sheet):
            session.query(Order) \
                .filter(Order.order_num.in_(orders_to_delete)).delete()
        session.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.on_event("startup")
@repeat_every(seconds=60*60*24)
async def notify():
    with SessionLocal() as session:
        today = datetime.now().date()
        orders = session.query(Order) \
            .filter(Order.delivery_time < today) \
            .filter(Order.notify == False).all()
        for order in orders:
            if send_message_to_telegram(order.order_num):
                order.notify = True
                session.add(order)
        session.commit()
