from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.analytics import OverviewMetrics
from app.services.analytics_service import get_overview_metrics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewMetrics)
def overview(db: Session = Depends(get_db)) -> OverviewMetrics:
    return get_overview_metrics(db)

