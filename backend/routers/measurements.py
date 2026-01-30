"""
Measurements API router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Measurement
from ..schemas import MeasurementCreate, MeasurementResponse, AnalysisResponse
from ..services.measurements import MeasurementService
from ..services.arduino import get_arduino_service, BaseArduinoService

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.post("/", response_model=dict)
async def create_measurement(
    data: MeasurementCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new temperature measurement from manual input.
    Automatically calculates metrics and performs risk analysis.
    """
    service = MeasurementService(db)
    return await service.create_measurement(data)


@router.post("/simulate", response_model=dict)
async def simulate_measurement(
    db: AsyncSession = Depends(get_db),
    arduino_service: BaseArduinoService = Depends(get_arduino_service)
):
    """
    Simulate a measurement using the Arduino mock service.
    Generates random data and saves it as a new measurement.
    """
    # Get simulated data
    temps = arduino_service.read_data()
    
    # Create DTO for existing logic re-use
    # Assuming device_id=0 and source="simulation" for mock data
    data = MeasurementCreate(
        device_id=0,
        source="simulation",
        sensor_1=temps[0],
        sensor_2=temps[1],
        sensor_3=temps[2],
        sensor_4=temps[3],
        sensor_5=temps[4],
        sensor_6=temps[5],
        sensor_7=temps[6],
        sensor_8=temps[7]
    )
    
    service = MeasurementService(db)
    return await service.create_measurement(data)


@router.get("/", response_model=List[MeasurementResponse])
async def get_measurements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    days: Optional[int] = Query(None, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get list of measurements with optional filtering by date range."""
    service = MeasurementService(db)
    return await service.get_measurements(skip, limit, days)


@router.get("/{measurement_id}", response_model=MeasurementResponse)
async def get_measurement(
    measurement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific measurement by ID."""
    service = MeasurementService(db)
    measurement = await service.get_measurement_by_id(measurement_id)
    
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    return measurement


@router.get("/{measurement_id}/analysis", response_model=AnalysisResponse)
async def get_measurement_analysis(
    measurement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get analysis result for a specific measurement."""
    service = MeasurementService(db)
    analysis = await service.get_analysis_by_measurement_id(measurement_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis
