"""
Arduino Service
Handles communication with Arduino hardware or simulates it.
"""
import random
from abc import ABC, abstractmethod
from typing import List

class BaseArduinoService(ABC):
    """Abstract base class for Arduino services"""
    
    @abstractmethod
    def read_data(self) -> List[float]:
        """Read temperature data from 8 sensors"""
        pass

class MockArduinoService(BaseArduinoService):
    """Mock service for testing without hardware"""
    
    def read_data(self) -> List[float]:
        """
        Generate random temperature data.
        Simulates realistic body temperatures (36.0 - 37.5).
        """
        temps = []
        
        # Base temperature for this reading
        base_temp = 36.6 + (random.random() * 0.4 - 0.2)
        
        for _ in range(8):
            # Add small random variation per sensor
            variance = random.random() * 0.3 - 0.15
            temp = round(base_temp + variance, 1)
            temps.append(temp)
            
        return temps

class RealArduinoService(BaseArduinoService):
    """
    Real service implementation for Arduino communication.
    To be implemented/connected later.
    """
    
    def read_data(self) -> List[float]:
        # Placeholder for serial communication logic
        # For now, behaves like mock or raises NotImplementedError
        raise NotImplementedError("Hardware communication not yet implemented")

# Factory or singleton storage
# By default export the Mock service for now, or allow switching
current_arduino_service = MockArduinoService()

def get_arduino_service() -> BaseArduinoService:
    return current_arduino_service
