"""
Pydantic schemas for API requests/responses
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ===== Measurement Schemas =====

class MeasurementCreate(BaseModel):
    """Schema for creating a measurement"""
    device_id: Optional[str] = "manual"
    source: Optional[str] = "manual"  # manual, sensor, image
    
    sensor_1: float = Field(..., ge=30, le=45, description="Left upper inner zone")
    sensor_2: float = Field(..., ge=30, le=45, description="Left upper outer zone")
    sensor_3: float = Field(..., ge=30, le=45, description="Left lower inner zone")
    sensor_4: float = Field(..., ge=30, le=45, description="Left lower outer zone")
    sensor_5: float = Field(..., ge=30, le=45, description="Right upper inner zone")
    sensor_6: float = Field(..., ge=30, le=45, description="Right upper outer zone")
    sensor_7: float = Field(..., ge=30, le=45, description="Right lower inner zone")
    sensor_8: float = Field(..., ge=30, le=45, description="Right lower outer zone")


class MeasurementResponse(BaseModel):
    """Schema for measurement response"""
    id: int
    device_id: Optional[str]
    timestamp: datetime
    source: str
    
    sensor_1: float
    sensor_2: float
    sensor_3: float
    sensor_4: float
    sensor_5: float
    sensor_6: float
    sensor_7: float
    sensor_8: float
    
    avg_left: Optional[float]
    avg_right: Optional[float]
    asymmetry: Optional[float]
    max_temp: Optional[float]
    
    class Config:
        from_attributes = True


# ===== Analysis Schemas =====

class AnalysisResponse(BaseModel):
    """Schema for analysis result"""
    id: int
    measurement_id: int
    timestamp: datetime
    risk_level: str
    anomaly_zones: Optional[List[str]]
    llm_conclusion: Optional[str]
    
    class Config:
        from_attributes = True


class AnalysisWithMeasurement(BaseModel):
    """Schema for analysis with measurement data"""
    measurement: MeasurementResponse
    analysis: AnalysisResponse


# ===== Metrics Schema =====

class MetricsResponse(BaseModel):
    """Schema for current metrics"""
    avg_left: float
    avg_right: float
    avg_total: float
    asymmetry: float
    max_temp: float
    min_temp: float
    risk_level: str
    last_measurement_time: Optional[datetime]
    total_measurements: int


# ===== Image Schemas =====

class ThermalImageResponse(BaseModel):
    """Schema for thermal image response"""
    id: int
    filename: str
    upload_time: datetime
    processed: bool
    extracted_temps: Optional[dict]
    measurement_id: Optional[int]
    
    class Config:
        from_attributes = True


class ImageAnalysisResponse(BaseModel):
    """Schema for image analysis result"""
    image_id: int
    extracted_temps: dict
    measurement: MeasurementResponse
    analysis: AnalysisResponse


# ===== Sensor Data Schema (for ESP32) =====

class SensorDataCreate(BaseModel):
    """Schema for sensor data from ESP32"""
    device_id: str
    temperatures: List[float] = Field(..., min_length=8, max_length=8)
