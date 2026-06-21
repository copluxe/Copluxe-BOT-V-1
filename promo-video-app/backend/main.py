import os
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import aiofiles

from database import engine, get_db, Base
from models import User, VideoProject
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from video_generator import generate_video

# Initialize DB
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Promo Video Generator API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Serve generated videos
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_IMAGE_SIZE_MB = 50


# ─── Schemas ────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str


class VideoStatusResponse(BaseModel):
    id: int
    status: str
    description: str
    output_url: Optional[str]
    thumbnail_url: Optional[str]
    duration: Optional[int]
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email déjà utilisé")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Nom d'utilisateur déjà pris")
    if len(data.password) < 6:
        raise HTTPException(400, "Mot de passe trop court (minimum 6 caractères)")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        email=user.email,
    )


@app.post("/auth/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Email ou mot de passe incorrect")

    token = create_access_token({"sub": str(user.id)})
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        email=user.email,
    )


@app.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}


# ─── Video Routes ─────────────────────────────────────────────────────────────

def _run_video_generation(video_id: int, image_paths: List[str], description: str,
                           output_path: str, db_url: str, seed: Optional[int] = None):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    local_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    LocalSession = sessionmaker(bind=local_engine)
    db = LocalSession()

    try:
        video = db.query(VideoProject).filter(VideoProject.id == video_id).first()
        video.status = "processing"
        db.commit()

        result_path = generate_video(image_paths, description, output_path, variation_seed=seed)

        thumb_path = result_path.replace(".mp4", "_thumb.jpg")
        video.status = "completed"
        video.output_path = result_path
        video.thumbnail_path = thumb_path if os.path.exists(thumb_path) else None
        video.completed_at = datetime.utcnow()

        # Estimate duration from clip count
        video.duration = max(10, min(60, len(image_paths) * 4))
        db.commit()
    except Exception as e:
        video = db.query(VideoProject).filter(VideoProject.id == video_id).first()
        if video:
            video.status = "failed"
            video.error_message = str(e)[:500]
            db.commit()
    finally:
        db.close()


@app.post("/videos/generate", status_code=202)
async def generate_video_endpoint(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (3 <= len(files) <= 10):
        raise HTTPException(400, "Envoyez entre 3 et 10 photos")

    if not description.strip():
        raise HTTPException(400, "La description est requise")

    # Save uploaded images
    project_id = str(uuid.uuid4())[:8]
    project_upload_dir = os.path.join(UPLOAD_DIR, project_id)
    os.makedirs(project_upload_dir, exist_ok=True)

    image_paths = []
    for i, file in enumerate(files):
        if file.content_type not in ALLOWED_IMAGE_TYPES and not file.filename.lower().endswith(
            ('.jpg', '.jpeg', '.png', '.webp', '.heic')
        ):
            raise HTTPException(400, f"Type de fichier non supporté: {file.content_type}")

        ext = Path(file.filename).suffix.lower() or ".jpg"
        save_path = os.path.join(project_upload_dir, f"photo_{i:02d}{ext}")

        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise HTTPException(400, f"Photo trop grande (max {MAX_IMAGE_SIZE_MB}MB)")

        async with aiofiles.open(save_path, "wb") as f:
            await f.write(content)
        image_paths.append(save_path)

    output_path = os.path.join(OUTPUT_DIR, f"{project_id}.mp4")

    # Create DB record
    video_project = VideoProject(
        user_id=current_user.id,
        description=description,
        status="pending",
        image_paths=image_paths,
        output_path=None,
        style_settings={"project_id": project_id},
    )
    db.add(video_project)
    db.commit()
    db.refresh(video_project)

    from database import DATABASE_URL
    background_tasks.add_task(
        _run_video_generation,
        video_project.id,
        image_paths,
        description,
        output_path,
        DATABASE_URL,
    )

    return {
        "video_id": video_project.id,
        "status": "pending",
        "message": "Génération vidéo démarrée",
    }


@app.get("/videos/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = db.query(VideoProject).filter(
        VideoProject.id == video_id,
        VideoProject.user_id == current_user.id
    ).first()
    if not video:
        raise HTTPException(404, "Vidéo introuvable")

    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    output_url = None
    thumbnail_url = None

    if video.output_path and os.path.exists(video.output_path):
        filename = os.path.basename(video.output_path)
        output_url = f"{base_url}/outputs/{filename}"

    if video.thumbnail_path and os.path.exists(video.thumbnail_path):
        filename = os.path.basename(video.thumbnail_path)
        thumbnail_url = f"{base_url}/outputs/{filename}"

    return VideoStatusResponse(
        id=video.id,
        status=video.status,
        description=video.description,
        output_url=output_url,
        thumbnail_url=thumbnail_url,
        duration=video.duration,
        error_message=video.error_message,
        created_at=video.created_at.isoformat(),
        completed_at=video.completed_at.isoformat() if video.completed_at else None,
    )


@app.post("/videos/{video_id}/regenerate", status_code=202)
def regenerate_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = db.query(VideoProject).filter(
        VideoProject.id == video_id,
        VideoProject.user_id == current_user.id
    ).first()
    if not video:
        raise HTTPException(404, "Vidéo introuvable")
    if video.status == "processing":
        raise HTTPException(409, "Une génération est déjà en cours")

    # New output path
    project_id = video.style_settings.get("project_id", str(uuid.uuid4())[:8])
    new_seed = random.randint(1, 999999)
    output_path = os.path.join(OUTPUT_DIR, f"{project_id}_v{new_seed}.mp4")

    video.status = "pending"
    video.output_path = None
    video.error_message = None
    video.completed_at = None
    db.commit()

    from database import DATABASE_URL
    background_tasks.add_task(
        _run_video_generation,
        video.id,
        video.image_paths,
        video.description,
        output_path,
        DATABASE_URL,
        new_seed,
    )

    return {"video_id": video_id, "status": "pending", "message": "Nouvelle variation en cours de génération"}


@app.get("/videos/my-videos")
def list_my_videos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    videos = db.query(VideoProject).filter(
        VideoProject.user_id == current_user.id
    ).order_by(VideoProject.created_at.desc()).limit(20).all()

    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    result = []
    for v in videos:
        thumbnail_url = None
        if v.thumbnail_path and os.path.exists(v.thumbnail_path):
            thumbnail_url = f"{base_url}/outputs/{os.path.basename(v.thumbnail_path)}"
        result.append({
            "id": v.id,
            "description": v.description[:80],
            "status": v.status,
            "thumbnail_url": thumbnail_url,
            "duration": v.duration,
            "created_at": v.created_at.isoformat(),
        })
    return result


@app.get("/health")
def health():
    return {"status": "ok"}
