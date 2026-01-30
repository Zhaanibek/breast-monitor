"""
Measurement Service
Handles business logic for temperature measurements.
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..models import Measurement, AnalysisResult
from ..schemas import MeasurementCreate
from .analyzer import analyzer

class MeasurementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_measurement(self, data: MeasurementCreate) -> Dict:
        """
        Create a new measurement, perform analysis, and save to DB.
        """
        # Extract temperatures
        temps = [
            data.sensor_1, data.sensor_2, data.sensor_3, data.sensor_4,
            data.sensor_5, data.sensor_6, data.sensor_7, data.sensor_8
        ]
        
        # Calculate metrics using the analyzer service
        metrics = analyzer.calculate_metrics(temps)
        
        # Classify risk
        risk_level, anomalies = analyzer.classify_risk(
            metrics["asymmetry"], 
            metrics["max_temp"]
        )
        
        # Find anomaly zones
        anomaly_zones = analyzer.find_anomaly_zones(temps)
        
        # Generate conclusion
        conclusion = analyzer.generate_conclusion(metrics, risk_level, anomalies)
        
        # Create measurement record
        measurement = Measurement(
            device_id=data.device_id,
            source=data.source,
            sensor_1=data.sensor_1,
            sensor_2=data.sensor_2,
            sensor_3=data.sensor_3,
            sensor_4=data.sensor_4,
            sensor_5=data.sensor_5,
            sensor_6=data.sensor_6,
            sensor_7=data.sensor_7,
            sensor_8=data.sensor_8,
            avg_left=metrics["avg_left"],
            avg_right=metrics["avg_right"],
            asymmetry=metrics["asymmetry"],
            max_temp=metrics["max_temp"]
        )
        
        self.db.add(measurement)
        await self.db.flush()
        
        # Create analysis result
        analysis = AnalysisResult(
            measurement_id=measurement.id,
            risk_level=risk_level,
            anomaly_zones=anomaly_zones,
            llm_conclusion=conclusion
        )
        
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(measurement)
        
        return {
            "measurement_id": measurement.id,
            "metrics": metrics,
            "risk_level": risk_level,
            "anomalies": anomalies,
            "anomaly_zones": anomaly_zones,
            "conclusion": conclusion,
            "timestamp": measurement.timestamp
        }

    async def get_measurements(self, skip: int = 0, limit: int = 50, days: Optional[int] = None) -> List[Measurement]:
        """
        Get list of measurements with optional filtering.
        """
        query = select(Measurement).order_by(desc(Measurement.timestamp))
        
        if days:
            since = datetime.utcnow() - timedelta(days=days)
            query = query.where(Measurement.timestamp >= since)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_measurement_by_id(self, measurement_id: int) -> Optional[Measurement]:
        """
        Get a specific measurement by ID.
        """
        query = select(Measurement).where(Measurement.id == measurement_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_analysis_by_measurement_id(self, measurement_id: int) -> Optional[AnalysisResult]:
        """
        Get analysis result for a specific measurement.
        """
        query = select(AnalysisResult).where(AnalysisResult.measurement_id == measurement_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
