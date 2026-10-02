from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv
import os

from routers import auth, groups, expenses, payments, reminders, profile
from utils import format_currency

load_dotenv()

app = FastAPI(title="Fair Share")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "supersecret-viva-key-123"))

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
templates.env.filters["currency"] = format_currency

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(payments.router)
app.include_router(reminders.router)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 303:
        pass # Handle redirects naturally
    return templates.TemplateResponse("error.html", {"request": request, "status_code": exc.status_code, "detail": exc.detail}, status_code=exc.status_code)

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    import traceback
    error_detail = traceback.format_exc() if hasattr(exc, '__traceback__') else str(exc)
    return templates.TemplateResponse("error.html", {"request": request, "status_code": 500, "detail": error_detail}, status_code=500)

@app.get("/")
async def root(request: Request):
    from utils import get_current_user
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})
