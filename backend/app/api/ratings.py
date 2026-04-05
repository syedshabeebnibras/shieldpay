import uuid

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.project import Project, ProjectStatus
from app.models.rating import Rating
from app.schemas.rating import ClientScoreResponse, RatingCreate, RatingResponse
from app.services import reputation_service
from app.utils.exceptions import BadRequestError, ForbiddenError, NotFoundError

router = APIRouter(prefix="/api/ratings", tags=["ratings"])


@router.post(
    "/projects/{project_id}/rate",
    response_model=RatingResponse,
    status_code=201,
)
async def rate_client(
    project_id: uuid.UUID,
    body: RatingCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> RatingResponse:
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")

    if project.freelancer_id != current_user.id:
        raise ForbiddenError("Only the freelancer can rate the client")

    if project.status != ProjectStatus.COMPLETED:
        raise BadRequestError("Can only rate after project completion")

    # Check for existing rating
    existing = await db.execute(
        select(Rating).where(
            Rating.project_id == project_id,
            Rating.rated_by_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise BadRequestError("You have already rated this client")

    rating = Rating(
        project_id=project_id,
        rated_by_id=current_user.id,
        rated_user_email=project.client_email,
        score=body.score,
        comment=body.comment,
    )
    db.add(rating)
    await db.flush()
    await db.refresh(rating)

    return RatingResponse.model_validate(rating)


@router.get("/client-score/{email}", response_model=ClientScoreResponse)
async def get_client_score(email: str, db: DbSession) -> ClientScoreResponse:
    """Public endpoint — returns aggregate client reputation score."""
    score = await reputation_service.calculate_client_score(db, email)
    return ClientScoreResponse(**score.model_dump())
