from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import auth
import random
from urllib.parse import parse_qs
import hashlib
from . import models

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @router.get('/game/login')
# def game_login(uin: str = Query(...), pass_: str = Query(..., alias='pass'), hash: str = Query(...), eip: str = Query('127.0.0.1'), db: Session = Depends(get_db)):
#     user = auth.authenticate_user(db, uin, pass_)
#     if user:
#         fake_id = random.randint(100000, 999999)
#         return JSONResponse({'user_id': fake_id})
#     else:
#         return JSONResponse({'error': 'wrong username or password'})

@router.get('/game/login{params:path}')
def game_login_hack(params: str, db: Session = Depends(get_db)):
    # params will be like '&uin=Test&pass=Test&hash=...&eip=...'
    # Remove leading '&' if present
    if params.startswith('&'):
        params = params[1:]
    # Parse params
    parsed = parse_qs(params)
    uin = parsed.get('uin', [''])[0]
    pass_ = parsed.get('pass', [''])[0]
    # hash and eip are optional for now
    # hash = parsed.get('hash', [''])[0]
    # eip = parsed.get('eip', ['127.0.0.1'])[0]
    user = auth.authenticate_user(db, uin, pass_)
    if user:
        fake_id = random.randint(100000, 999999)
        return PlainTextResponse(str(fake_id))
    else:
        return PlainTextResponse('wrong username or password')

@router.get('/game/orders')
def game_orders(uin: str = Query(...)):
    return PlainTextResponse('completed')

@router.get('/game/sendscores')
def game_sendscores(uid: int = Query(...), lname: str = Query(...), score: float = Query(...), hash: str = Query(...), lv: float = Query(...), gv: float = Query(...), db: Session = Depends(get_db)):
    # Secret key for hash validation (should match your game)
    secret_key = 'your_secret_key_here'  # TODO: set this securely
    expected_hash = hashlib.md5(f"{uid}{score}{secret_key}".encode()).hexdigest()
    if hash != expected_hash:
        return PlainTextResponse('There was an error posting the high score: invalid hash')
    # Store the score
    new_score = models.LeaderboardScore(
        uid=uid,
        level_name=lname,
        score=score,
        hash=hash,
        level_version=lv,
        game_version=gv
    )
    db.add(new_score)
    db.commit()
    return PlainTextResponse('Score uploaded successfully') 