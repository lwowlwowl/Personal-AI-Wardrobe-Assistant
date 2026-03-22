"""衣櫥分析 API（路徑與行為與重構前 main 一致）。"""
import traceback
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.analysis_suggestions_service import run_suggested_additions
from app.services.analysis_trend_service import (
    run_category_distribution,
    run_export_trend_data,
    run_total_items_summary,
    run_total_items_trend,
)
from app.services.analysis_wardrobe_insights_service import (
    run_idle_items_detail,
    run_idle_rate,
    run_most_worn_items,
    run_top_color,
    run_top_style,
    run_weekly_activity,
)

router = APIRouter(tags=["analysis"])


@router.get("/api/analysis/total-items/trend")
async def get_total_items_trend(
    token: str = Query(...),
    db: Session = Depends(get_db),
    view_by: str = Query("yearly", regex="^(yearly|monthly|daily|weekly)$"),
    start_year: Optional[int] = Query(None, ge=2000, le=2100),
    end_year: Optional[int] = Query(None, ge=2000, le=2100),
    include_projection: bool = Query(True, description="是否包含预测数据"),
):
    try:
        current_user = get_current_user(token, db)
        return run_total_items_trend(
            db,
            current_user.id,
            view_by,
            start_year,
            end_year,
            include_projection,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis total-items/trend error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load item trend data: {str(e)}",
        )


@router.get("/api/analysis/total-items/summary")
async def get_total_items_summary(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        current_user = get_current_user(token, db)
        return run_total_items_summary(db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis total-items/summary error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load wardrobe summary: {str(e)}",
        )


@router.get("/api/analysis/total-items/category-distribution")
async def get_category_distribution(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        current_user = get_current_user(token, db)
        return run_category_distribution(db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis category-distribution error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load category breakdown: {str(e)}",
        )


@router.get("/api/analysis/total-items/export")
async def export_trend_data(
    token: str = Query(...),
    db: Session = Depends(get_db),
    format: str = Query("json", regex="^(json|csv)$"),
    view_by: str = Query("yearly", regex="^(yearly|monthly|daily|weekly)$"),
    start_year: Optional[int] = Query(None),
    end_year: Optional[int] = Query(None),
):
    try:
        current_user = get_current_user(token, db)
        return run_export_trend_data(db, current_user.id, format, view_by, start_year, end_year)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis total-items/export error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not export trend data: {str(e)}",
        )


@router.get("/api/analysis/idle-rate")
async def get_idle_rate(
    token: str = Query(...),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="闲置天数阈值"),
):
    try:
        current_user = get_current_user(token, db)
        return run_idle_rate(db, current_user.id, days)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis idle-rate error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load idle rate: {str(e)}",
        )


@router.get("/api/analysis/idle-items/detail")
async def get_idle_items_detail(
    token: str = Query(...),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    time_filter: Optional[str] = Query(None, regex="^(never|over_season|over_year|over_six_months|over_three_months)$"),
    season_filter: Optional[str] = Query(None),
):
    try:
        current_user = get_current_user(token, db)
        return run_idle_items_detail(db, current_user.id, page, page_size, time_filter, season_filter)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis idle-items/detail error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load idle items: {str(e)}",
        )


@router.get("/api/analysis/top-color")
async def get_top_color(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        current_user = get_current_user(token, db)
        return run_top_color(db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis top-color error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load color stats: {str(e)}",
        )


@router.get("/api/analysis/top-style")
async def get_top_style(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        current_user = get_current_user(token, db)
        return run_top_style(db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis top-style error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load style stats: {str(e)}",
        )


@router.get("/api/analysis/most-worn")
async def get_most_worn_items(
    token: str = Query(...),
    db: Session = Depends(get_db),
    time_range: str = Query("yearly", regex="^(yearly|monthly|daily|weekly)$"),
    limit: int = Query(5, ge=1, le=20, description="返回数量"),
):
    current_user = get_current_user(token, db)
    return run_most_worn_items(db, current_user.id, time_range, limit)


@router.get("/api/analysis/weekly-activity")
async def get_weekly_activity(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        current_user = get_current_user(token, db)
        return run_weekly_activity(db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis weekly-activity error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load weekly activity: {str(e)}",
        )


@router.get("/api/analysis/suggested-additions")
async def get_suggested_additions(
    token: str = Query(...),
    db: Session = Depends(get_db),
    limit: int = Query(3, ge=1, le=3, description="固定返回 3 条建议"),
):
    try:
        current_user = get_current_user(token, db)
        return await run_suggested_additions(db, current_user.id, limit)
    except HTTPException:
        raise
    except Exception as e:
        print(f"analysis suggested-additions error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load suggested additions: {str(e)}",
        )
