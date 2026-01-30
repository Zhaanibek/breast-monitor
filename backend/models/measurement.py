"""
Database models for breast health monitoring
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class Measurement(Base):
    """Temperature measurement model"""
    __tablename__ = "measurements"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=True, default="manual")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(50), default="manual")  # manual, sensor, image
    
    # 8 sensor zones (4 per breast)
    sensor_1 = Column(Float, nullable=False)  # Left upper inner
    sensor_2 = Column(Float, nullable=False)  # Left upper outer
    sensor_3 = Column(Float, nullable=False)  # Left lower inner
    sensor_4 = Column(Float, nullable=False)  # Left lower outer
    sensor_5 = Column(Float, nullable=False)  # Right upper inner
    sensor_6 = Column(Float, nullable=False)  # Right upper outer
    sensor_7 = Column(Float, nullable=False)  # Right lower inner
    sensor_8 = Column(Float, nullable=False)  # Right lower outer
    
    # Calculated metrics
    avg_left = Column(Float, nullable=True)
    avg_right = Column(Float, nullable=True)
    asymmetry = Column(Float, nullable=True)
    max_temp = Column(Float, nullable=True)
    
    # Relationships
    analysis = relationship("AnalysisResult", back_populates="measurement", uselist=False)
    thermal_image = relationship("ThermalImage", back_populates="measurement", uselist=False)


class AnalysisResult(Base):
    """Analysis result model"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"), unique=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Risk classification
    risk_level = Column(String(20), nullable=False)  # NORMAL, ELEVATED, HIGH
    anomaly_zones = Column(JSON, nullable=True)  # List of anomalous zones
    
    # LLM-generated conclusion
    llm_conclusion = Column(Text, nullable=True)
    
    # Relationship
    measurement = relationship("Measurement", back_populates="analysis")


class ThermalImage(Base):
    """Thermal image model"""
    __tablename__ = "thermal_images"
    
    id = Column(Integer, primary_key=True, index=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer, nullable=True)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # Extracted data
    extracted_temps = Column(JSON, nullable=True)  # Temperatures extracted from image
    color_analysis = Column(JSON, nullable=True)  # Color distribution data
    
    # Relationship
    measurement = relationship("Measurement", back_populates="thermal_image")
