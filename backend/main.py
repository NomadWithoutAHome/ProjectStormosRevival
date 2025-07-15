from fastapi import FastAPI, Request, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from .database import SessionLocal, engine, Base
from . import models, schemas, auth, crud
import os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='your-secret-key')

# Ensure database tables are created
Base.metadata.create_all(bind=engine)

# Mount static files (for Tailwind CSS, etc.)
static_dir = os.path.join(os.path.dirname(__file__), '../frontend/static')
app.mount('/static', StaticFiles(directory=static_dir), name='static')

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), '../frontend/templates'))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    user = request.session.get('user')
    return templates.TemplateResponse('index.html', {"request": request, "user": user})

@app.post('/signup')
def signup(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if auth.get_user_by_username(db, username):
        return templates.TemplateResponse('index.html', {"request": request, "error": "Username already exists."})
    user = auth.create_user(db, username, password)
    request.session['user'] = user.username
    return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)

@app.post('/login')
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse('index.html', {"request": request, "error": "Invalid credentials."})
    request.session['user'] = user.username
    return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)

@app.get('/logout')
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)

@app.get('/forum', response_class=HTMLResponse)
def forum(request: Request, db: Session = Depends(get_db)):
    posts = crud.get_posts(db)
    user = request.session.get('user')
    return templates.TemplateResponse('forum.html', {"request": request, "posts": posts, "user": user})

@app.post('/forum')
def post_forum(request: Request, content: str = Form(...), db: Session = Depends(get_db)):
    username = request.session.get('user')
    if not username:
        return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    user = auth.get_user_by_username(db, username)
    crud.create_post(db, user.id, content)
    return RedirectResponse(url='/forum', status_code=status.HTTP_303_SEE_OTHER)

@app.get('/chat', response_class=HTMLResponse)
def chat(request: Request, db: Session = Depends(get_db)):
    messages = crud.get_messages(db)
    user = request.session.get('user')
    return templates.TemplateResponse('chat.html', {"request": request, "messages": messages, "user": user})

@app.post('/chat')
def post_chat(request: Request, content: str = Form(...), db: Session = Depends(get_db)):
    username = request.session.get('user')
    if not username:
        return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    user = auth.get_user_by_username(db, username)
    crud.create_message(db, user.id, content)
    return RedirectResponse(url='/chat', status_code=status.HTTP_303_SEE_OTHER) 