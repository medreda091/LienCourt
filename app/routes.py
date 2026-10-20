"""HTTP routes: link creation and redirection."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Link
from app.schemas import LinkCreate, LinkResponse, LinkStatsResponse
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


@router.get("/api/links", response_model=list[LinkResponse], tags=["links"])
def list_links(db: Session = Depends(get_db), limit: int = 100, offset: int = 0) -> list[Link]:
    """List links, most recent first."""
    return (
        db.query(Link)
        .order_by(Link.created_at.desc(), Link.id.desc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 500))
        .all()
    )


@router.get("/api/links/{code}/stats", response_model=LinkStatsResponse, tags=["links"])
def link_stats(code: str, db: Session = Depends(get_db)) -> LinkStatsResponse:
    """Return click statistics for a single link."""
    link = get_link_by_code(db, code)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return LinkStatsResponse(
        code=link.code,
        original_url=link.original_url,
        is_custom_alias=link.is_custom_alias,
        click_count=link.click_count,
        created_at=link.created_at,
        last_accessed_at=link.last_accessed_at,
        expires_at=link.expires_at,
        is_expired=link.is_expired(),
    )


@router.delete("/api/links/{code}", status_code=status.HTTP_204_NO_CONTENT, tags=["links"])
def delete_link(code: str, db: Session = Depends(get_db)) -> None:
    """Delete a link. Returns 404 when the code does not exist."""
    link = get_link_by_code(db, code)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    db.delete(link)
    db.commit()
    return None


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
