from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from app.db import get_db_connection
from app.utils import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, msg: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    if not conn:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Database Connection Failed. Check Railway Variables!"})
    cursor = conn.cursor(dictionary=True)
    # Authenticate via email or username
    user = None
    try:
        try:
            cursor.execute("SELECT * FROM Users WHERE (email = %s OR user_name = %s) AND (deleted_at IS NULL)", (email, email))
        except:
            cursor.execute("SELECT * FROM Users WHERE email = %s OR user_name = %s", (email, email))
        user = cursor.fetchone()
    except Exception as e:
        conn.close()
        return templates.TemplateResponse("login.html", {"request": request, "error": "Database is empty! You must create the tables first."})
        
    conn.close()

    if user and pwd_context.verify(password, user['password_hash']):
        request.session['user_id'] = user['user_id']
        return RedirectResponse(url="/groups", status_code=303)
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials or account deleted."})

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
async def signup(request: Request, first_name: str = Form(...), last_name: str = Form(...), 
                 user_name: str = Form(...), email: str = Form(...), 
                 password: str = Form(...), confirm_password: str = Form(...), dob: str = Form(...)):
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match."})
    
    if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Password must be at least 8 chars with a letter and a digit."})

    hashed_password = pwd_context.hash(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Users (first_name, last_name, user_name, email, password_hash, date_of_birth) VALUES (%s, %s, %s, %s, %s, %s)",
            (first_name, last_name, user_name, email, hashed_password, dob)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return templates.TemplateResponse("signup.html", {"request": request, "error": f"Username or email already exists. {e}"})
    
    conn.close()
    return RedirectResponse(url="/login?msg=Account created successfully. Please login.", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
