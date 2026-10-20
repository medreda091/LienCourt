"""HTTP routes: link creation and redirection."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Link
from app.schemas import LinkCreate, LinkResponse
from app.services import generate_unique_code, get_link_by_code

router = APIRouter()


@router.post("/api/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED, tags=["links"])
def create_link(payload: LinkCreate, db: Session = Depends(get_db)) -> Link:
    """Create a short link, optionally with a custom alias and expiration."""
    if payload.custom_alias:
        if get_link_by_code(db, payload.custom_alias) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Custom alias already in use")
        code = payload.custom_alias
        is_custom = True
    else:
        code = generate_unique_code(db)
        is_custom = False

    link = Link(
        code=code,
        original_url=payload.original_url,
        is_custom_alias=is_custom,
        expires_at=payload.expires_at,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.get("/{code}", tags=["redirect"])
def redirect_to_original(code: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """Redirect to the original URL and count the click."""
    link = get_link_by_code(db, code)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    if link.is_expired():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")

    link.click_count += 1
    link.last_accessed_at = datetime.now(timezone.utc)
    db.commit()

    return RedirectResponse(url=link.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
