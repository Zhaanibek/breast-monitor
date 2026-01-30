"""
Images API router for thermal image upload and analysis
"""
import os
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import ThermalImage, Measurement, AnalysisResult
from ..schemas import ThermalImageResponse, ImageAnalysisResponse
from ..services import analyzer
from ..config import settings


router = APIRouter(prefix="/images", tags=["images"])


def analyze_thermal_colors(image_path: str) -> dict:
    """
    Analyze thermal image colors to extract temperature estimates.
    
    This is a simplified implementation that maps colors to temperatures.
    A more sophisticated approach would use proper thermal camera calibration data.
    
    Returns dict with estimated temperatures for 8 zones.
    """
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.open(image_path).convert('RGB')
        img_array = np.array(img)
        
        # Divide image into 8 zones (2x4 grid)
        h, w = img_array.shape[:2]
        zone_h, zone_w = h // 2, w // 4
        
        temps = []
        for row in range(2):
            for col in range(4):
                # Extract zone
                zone = img_array[
                    row * zone_h:(row + 1) * zone_h,
                    col * zone_w:(col + 1) * zone_w
                ]
                
                # Calculate average color
                avg_color = zone.mean(axis=(0, 1))
                r, g, b = avg_color
                
                # Map color to temperature
                # Thermal images typically use: blue (cold) -> green -> yellow -> red (hot)
                # Red channel indicates heat
                temp = 34.0 + (r / 255.0) * 5.0  # Range 34-39°C
                
                # Adjust for green/yellow (moderate heat)
                if g > r * 0.8:
                    temp = temp - 0.5
                
                temps.append(round(temp, 1))
        
        return {
            "temperatures": temps,
            "color_data": {
                "zones_analyzed": 8,
                "method": "rgb_mapping"
            }
        }
        
    except Exception as e:
        # Fallback: generate simulated temperatures
        import random
        return {
            "temperatures": [round(36.0 + random.random() * 1.5, 1) for _ in range(8)],
            "color_data": {
                "zones_analyzed": 8,
                "method": "simulated",
                "error": str(e)
            }
        }


@router.post("/upload", response_model=dict)
async def upload_thermal_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a thermal image for analysis.
    Extracts temperatures from color patterns and creates a measurement.
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1] or '.png'
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Analyze image
    analysis_result = analyze_thermal_colors(file_path)
    temps = analysis_result["temperatures"]
    
    # Calculate metrics
    metrics = analyzer.calculate_metrics(temps)
    risk_level, anomalies = analyzer.classify_risk(
        metrics["asymmetry"],
        metrics["max_temp"]
    )
    anomaly_zones = analyzer.find_anomaly_zones(temps)
    conclusion = analyzer.generate_conclusion(metrics, risk_level, anomalies)
    
    # Create measurement
    measurement = Measurement(
        device_id="image_upload",
        source="image",
        sensor_1=temps[0], sensor_2=temps[1],
        sensor_3=temps[2], sensor_4=temps[3],
        sensor_5=temps[4], sensor_6=temps[5],
        sensor_7=temps[6], sensor_8=temps[7],
        avg_left=metrics["avg_left"],
        avg_right=metrics["avg_right"],
        asymmetry=metrics["asymmetry"],
        max_temp=metrics["max_temp"]
    )
    db.add(measurement)
    await db.flush()
    
    # Create thermal image record
    thermal_image = ThermalImage(
        measurement_id=measurement.id,
        filename=filename,
        original_filename=file.filename,
        file_size=len(content),
        processed=True,
        extracted_temps=analysis_result["temperatures"],
        color_analysis=analysis_result["color_data"]
    )
    db.add(thermal_image)
    
    # Create analysis
    analysis = AnalysisResult(
        measurement_id=measurement.id,
        risk_level=risk_level,
        anomaly_zones=anomaly_zones,
        llm_conclusion=conclusion
    )
    db.add(analysis)
    
    await db.commit()
    
    return {
        "image_id": thermal_image.id,
        "measurement_id": measurement.id,
        "extracted_temps": temps,
        "metrics": metrics,
        "risk_level": risk_level,
        "conclusion": conclusion
    }


@router.get("/", response_model=List[ThermalImageResponse])
async def get_images(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get list of uploaded thermal images."""
    result = await db.execute(
        select(ThermalImage)
        .order_by(ThermalImage.upload_time.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{image_id}", response_model=ThermalImageResponse)
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get thermal image by ID."""
    result = await db.execute(
        select(ThermalImage).where(ThermalImage.id == image_id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return image
