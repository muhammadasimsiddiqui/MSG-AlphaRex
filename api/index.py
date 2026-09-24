"""Vercel serverless entry point for the SkillSprint FastAPI application."""
import sys
from pathlib import Path

from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.main import app as skillsprint_app

app = FastAPI(title="SkillSprint AI Serverless")
app.mount("/api", skillsprint_app)
