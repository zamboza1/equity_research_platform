from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import re

router = APIRouter()

PRIMERS_DIR = os.path.join(os.path.dirname(__file__), "../../content/primers")

class PrimerResponse(BaseModel):
    slug: str
    content: str

@router.get("/primers/{slug}", response_model=PrimerResponse)
def get_primer(slug: str):
    if not re.fullmatch(r"[a-z0-9_-]+",slug): raise HTTPException(422,"Invalid primer name")
    file_path = os.path.join(PRIMERS_DIR, f"{slug}.md")
    if not os.path.exists(file_path):
        # Fallback to check if user meant just the name without extension or different path
        # But generally we expect consistent naming
        raise HTTPException(status_code=404, detail="Primer not found")

    with open(file_path, "r") as f:
        content = f.read()

    return PrimerResponse(slug=slug, content=content)
