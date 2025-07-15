from fastapi import FastAPI, Request, Depends, Form, status, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from .database import SessionLocal, engine, Base
from . import models, schemas, auth, crud
import os
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .game_routes import router as game_router

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='your-secret-key')

# Ensure database tables are created
Base.metadata.create_all(bind=engine)

# Mount static files (for Tailwind CSS, etc.)
static_dir = os.path.join(os.path.dirname(__file__), '../frontend/static')
app.mount('/static', StaticFiles(directory=static_dir), name='static')

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), '../frontend/templates'))

# Store connected WebSocket clients
chat_connections = set()

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
    from zoneinfo import ZoneInfo
    from fastapi import Query
    page = int(request.query_params.get('page', 1))
    per_page = 8
    total_posts = db.query(models.ForumPost).count()
    total_pages = (total_posts + per_page - 1) // per_page
    posts = db.query(models.ForumPost).order_by(models.ForumPost.created_at.asc()).offset((page-1)*per_page).limit(per_page).all()
    formatted_posts = []
    for p in posts:
        username = p.user.username if p.user else 'Unknown'
        created_at = p.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        timestamp = created_at.astimezone(ZoneInfo('US/Eastern')).strftime('%m/%d/%Y %I:%M%p')
        formatted_posts.append({
            'username': username,
            'content': p.content,
            'timestamp': timestamp
        })
    user = request.session.get('user')
    return templates.TemplateResponse('forum.html', {"request": request, "posts": formatted_posts, "user": user, "page": page, "total_pages": total_pages})

@app.post('/forum')
def post_forum(request: Request, content: str = Form(...), db: Session = Depends(get_db)):
    username = request.session.get('user')
    if not username:
        return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    user = auth.get_user_by_username(db, username)
    crud.create_post(db, user.id, content)
    return RedirectResponse(url='/forum', status_code=status.HTTP_303_SEE_OTHER)

@app.get('/clear_chat_history')
def clear_chat_history(db: Session = Depends(get_db)):
    db.query(models.ChatMessage).delete()
    db.commit()
    return {'status': 'chat history cleared'}

@app.get('/chat', response_class=HTMLResponse)
def chat(request: Request, db: Session = Depends(get_db)):
    from zoneinfo import ZoneInfo
    messages = db.query(models.ChatMessage).order_by(models.ChatMessage.created_at.asc()).limit(50).all()
    formatted_messages = []
    for m in messages:
        username = m.user.username if m.user else 'Unknown'
        created_at = m.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        timestamp = created_at.astimezone(ZoneInfo('US/Eastern')).strftime('%m/%d/%Y %I:%M%p')
        html = f"<span class='font-bold' title='{timestamp} EST'>{username}:</span> {m.content}"
        formatted_messages.append(html)
    user = request.session.get('user')
    return templates.TemplateResponse('chat.html', {"request": request, "messages": formatted_messages, "user": user})

@app.post('/chat')
def post_chat(request: Request, content: str = Form(...), db: Session = Depends(get_db)):
    username = request.session.get('user')
    if not username:
        return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    user = auth.get_user_by_username(db, username)
    crud.create_message(db, user.id, content)
    return RedirectResponse(url='/chat', status_code=status.HTTP_303_SEE_OTHER)

@app.websocket('/ws/chat')
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    chat_connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Expect JSON: {"username": ..., "content": ...}
            try:
                msg = json.loads(data)
                username = msg.get('username')
                content = msg.get('content')
            except Exception:
                continue
            # Store in DB
            db = SessionLocal()
            user = auth.get_user_by_username(db, username)
            if user:
                chat_msg = crud.create_message(db, user.id, content)
                created_at = chat_msg.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                timestamp = created_at.astimezone(ZoneInfo('US/Eastern')).strftime('%m/%d/%Y %I:%M%p')
            else:
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                timestamp = now.astimezone(ZoneInfo('US/Eastern')).strftime('%m/%d/%Y %I:%M%p')
            db.close()
            # Clean format: User1: Message (timestamp as title)
            formatted = f"<span class='font-bold' title='{timestamp} EST'>{username}:</span> {content}"
            for connection in chat_connections:
                await connection.send_text(formatted)
    except WebSocketDisconnect:
        chat_connections.remove(websocket)

app.include_router(game_router) 