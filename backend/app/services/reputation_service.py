import logging

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispute import Dispute
from app.models.milestone import Milestone, MilestoneStatus
from app.models.project import Project, ProjectStatus
from app.models.rating import Rating

logger = logging.getLogger(__name__)

AUTO_APPROVE_DAYS = 5


class ClientScore(BaseModel):
    email: str
    average_rating: float | None
    total_ratings: int
    total_projects: int
    total_amount_paid_cents: int
    avg_approval_days: float | None
    on_time_percentage: float | None
    dispute_rate: float | None
    trust_tier: str


def get_trust_tier(
    total_projects: int,
    avg_rating: float | None,
    on_time_pct: float | None,
) -> str:
    if total_projects < 3:
        return "new"
    rating = avg_rating or 0.0
    on_time = on_time_pct or 0.0
    if total_projects >= 25 and rating >= 4.5 and on_time >= 90:
        return "premium"
    if total_projects >= 10 and rating >= 4.0 and on_time >= 80:
        return "trusted"
    if total_projects >= 3 and rating >= 3.5:
        return "verified"
    return "new"


async def calculate_client_score(
    db: AsyncSession, client_email: str
) -> ClientScore:
    # ── Ratings ────────────────────────────────────────────────────────
    rating_result = await db.execute(
        select(
            func.avg(Rating.score).label("avg_score"),
            func.count(Rating.id).label("cnt"),
        ).where(Rating.rated_user_email == client_email)
    )
    row = rating_result.one()
    avg_rating = float(row.avg_score) if row.avg_score is not None else None
    total_ratings = row.cnt

    # ── Projects ───────────────────────────────────────────────────────
    project_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.client_email == client_email,
            Project.status.in_([
                ProjectStatus.COMPLETED,
                ProjectStatus.ACTIVE,
            ]),
        )
    )
    total_projects = project_result.scalar() or 0

    # ── Total amount paid (from released milestones) ───────────────────
    paid_result = await db.execute(
        select(func.coalesce(func.sum(Milestone.amount_cents), 0)).where(
            Milestone.project_id.in_(
                select(Project.id).where(Project.client_email == client_email)
            ),
            Milestone.status == MilestoneStatus.RELEASED,
        )
    )
    total_paid = paid_result.scalar() or 0

    # ── Approval speed ─────────────────────────────────────────────────
    # Get milestones that were both delivered and approved
    approval_result = await db.execute(
        select(
            Milestone.delivered_at,
            Milestone.approved_at,
        ).where(
            Milestone.project_id.in_(
                select(Project.id).where(Project.client_email == client_email)
            ),
            Milestone.delivered_at.is_not(None),
            Milestone.approved_at.is_not(None),
        )
    )
    approval_rows = approval_result.all()

    avg_approval_days = None
    on_time_pct = None
    if approval_rows:
        days_list = []
        on_time_count = 0
        for delivered_at, approved_at in approval_rows:
            delta = (approved_at - delivered_at).total_seconds() / 86400
            days_list.append(delta)
            if delta <= AUTO_APPROVE_DAYS:
                on_time_count += 1
        avg_approval_days = sum(days_list) / len(days_list)
        on_time_pct = (on_time_count / len(days_list)) * 100

    # ── Dispute rate ───────────────────────────────────────────────────
    total_milestones_result = await db.execute(
        select(func.count(Milestone.id)).where(
            Milestone.project_id.in_(
                select(Project.id).where(Project.client_email == client_email)
            ),
            Milestone.status != MilestoneStatus.DRAFT,
        )
    )
    total_milestones = total_milestones_result.scalar() or 0

    disputed_result = await db.execute(
        select(func.count(Dispute.id)).where(
            Dispute.milestone_id.in_(
                select(Milestone.id).where(
                    Milestone.project_id.in_(
                        select(Project.id).where(
                            Project.client_email == client_email
                        )
                    )
                )
            )
        )
    )
    disputed_count = disputed_result.scalar() or 0
    dispute_rate = (
        (disputed_count / total_milestones * 100) if total_milestones > 0 else None
    )

    # ── Trust tier ─────────────────────────────────────────────────────
    tier = get_trust_tier(total_projects, avg_rating, on_time_pct)

    return ClientScore(
        email=client_email,
        average_rating=round(avg_rating, 2) if avg_rating is not None else None,
        total_ratings=total_ratings,
        total_projects=total_projects,
        total_amount_paid_cents=total_paid,
        avg_approval_days=(
            round(avg_approval_days, 1) if avg_approval_days is not None else None
        ),
        on_time_percentage=(
            round(on_time_pct, 1) if on_time_pct is not None else None
        ),
        dispute_rate=round(dispute_rate, 1) if dispute_rate is not None else None,
        trust_tier=tier,
    )
