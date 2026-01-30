"""
Analysis API router
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models import Measurement, AnalysisResult
from ..schemas import AnalysisResponse, MetricsResponse
from ..services import analyzer


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/current", response_model=dict)
async def get_current_analysis(
    db: AsyncSession = Depends(get_db)
):
    """Get the most recent analysis result."""
    # Get latest measurement
    result = await db.execute(
        select(Measurement)
        .order_by(Measurement.timestamp.desc())
        .limit(1)
    )
    measurement = result.scalar_one_or_none()
    
    if not measurement:
        return {
            "status": "no_data",
            "message": "Нет данных для анализа. Добавьте измерение или загрузите термограмму."
        }
    
    # Get analysis
    result = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.measurement_id == measurement.id)
    )
    analysis = result.scalar_one_or_none()
    
    return {
        "status": "ok",
        "measurement": {
            "id": measurement.id,
            "timestamp": measurement.timestamp.isoformat(),
            "source": measurement.source,
            "avg_left": measurement.avg_left,
            "avg_right": measurement.avg_right,
            "asymmetry": measurement.asymmetry,
            "max_temp": measurement.max_temp
        },
        "analysis": {
            "risk_level": analysis.risk_level if analysis else "UNKNOWN",
            "anomaly_zones": analysis.anomaly_zones if analysis else [],
            "conclusion": analysis.llm_conclusion if analysis else ""
        }
    }


@router.get("/history", response_model=List[dict])
async def get_analysis_history(
    days: int = Query(30, ge=1, le=365),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get analysis history for specified number of days."""
    since = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Measurement, AnalysisResult)
        .join(AnalysisResult, Measurement.id == AnalysisResult.measurement_id)
        .where(Measurement.timestamp >= since)
        .order_by(Measurement.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    
    history = []
    for measurement, analysis in result.all():
        history.append({
            "measurement_id": measurement.id,
            "timestamp": measurement.timestamp.isoformat(),
            "source": measurement.source,
            "avg_left": measurement.avg_left,
            "avg_right": measurement.avg_right,
            "asymmetry": measurement.asymmetry,
            "risk_level": analysis.risk_level
        })
    
    return history


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db)
):
    """Get current metrics summary."""
    # Get latest measurement
    result = await db.execute(
        select(Measurement)
        .order_by(Measurement.timestamp.desc())
        .limit(1)
    )
    measurement = result.scalar_one_or_none()
    
    # Get total count
    count_result = await db.execute(select(func.count(Measurement.id)))
    total_count = count_result.scalar() or 0
    
    if not measurement:
        return MetricsResponse(
            avg_left=0,
            avg_right=0,
            avg_total=0,
            asymmetry=0,
            max_temp=0,
            min_temp=0,
            risk_level="UNKNOWN",
            last_measurement_time=None,
            total_measurements=total_count
        )
    
    # Get analysis for risk level
    result = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.measurement_id == measurement.id)
    )
    analysis = result.scalar_one_or_none()
    
    temps = [
        measurement.sensor_1, measurement.sensor_2,
        measurement.sensor_3, measurement.sensor_4,
        measurement.sensor_5, measurement.sensor_6,
        measurement.sensor_7, measurement.sensor_8
    ]
    
    return MetricsResponse(
        avg_left=measurement.avg_left,
        avg_right=measurement.avg_right,
        avg_total=(measurement.avg_left + measurement.avg_right) / 2,
        asymmetry=measurement.asymmetry,
        max_temp=max(temps),
        min_temp=min(temps),
        risk_level=analysis.risk_level if analysis else "UNKNOWN",
        last_measurement_time=measurement.timestamp,
        total_measurements=total_count
    )


@router.get("/statistics", response_model=dict)
async def get_statistics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get statistical analysis for the specified period."""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get measurements in period
    result = await db.execute(
        select(Measurement)
        .where(Measurement.timestamp >= since)
    )
    measurements = result.scalars().all()
    
    if not measurements:
        return {
            "period_days": days,
            "total_measurements": 0,
            "message": "Нет данных за указанный период"
        }
    
    # Calculate statistics
    asymmetries = [m.asymmetry for m in measurements if m.asymmetry is not None]
    avg_lefts = [m.avg_left for m in measurements if m.avg_left is not None]
    avg_rights = [m.avg_right for m in measurements if m.avg_right is not None]
    
    # Count risk levels
    result = await db.execute(
        select(AnalysisResult.risk_level, func.count(AnalysisResult.id))
        .join(Measurement, Measurement.id == AnalysisResult.measurement_id)
        .where(Measurement.timestamp >= since)
        .group_by(AnalysisResult.risk_level)
    )
    risk_counts = {level: count for level, count in result.all()}
    
    return {
        "period_days": days,
        "total_measurements": len(measurements),
        "avg_asymmetry": round(sum(asymmetries) / len(asymmetries), 2) if asymmetries else 0,
        "max_asymmetry": round(max(asymmetries), 2) if asymmetries else 0,
        "avg_left_temp": round(sum(avg_lefts) / len(avg_lefts), 2) if avg_lefts else 0,
        "avg_right_temp": round(sum(avg_rights) / len(avg_rights), 2) if avg_rights else 0,
        "risk_distribution": {
            "normal": risk_counts.get("NORMAL", 0),
            "elevated": risk_counts.get("ELEVATED", 0),
            "high": risk_counts.get("HIGH", 0)
        }
    }
