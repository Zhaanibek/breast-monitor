"""
Temperature analysis service
"""
from typing import List, Dict, Tuple
from ..config import settings


class AnalyzerService:
    """Service for analyzing temperature measurements"""
    
    @staticmethod
    def calculate_metrics(temps: List[float]) -> Dict:
        """
        Calculate metrics from 8 temperature readings.
        
        Args:
            temps: List of 8 temperatures [s1, s2, s3, s4, s5, s6, s7, s8]
                   where s1-s4 are left breast, s5-s8 are right breast
        
        Returns:
            Dictionary with calculated metrics
        """
        left_temps = temps[:4]
        right_temps = temps[4:8]
        
        avg_left = sum(left_temps) / len(left_temps)
        avg_right = sum(right_temps) / len(right_temps)
        asymmetry = abs(avg_left - avg_right)
        avg_total = (avg_left + avg_right) / 2
        max_temp = max(temps)
        min_temp = min(temps)
        
        return {
            "avg_left": round(avg_left, 2),
            "avg_right": round(avg_right, 2),
            "avg_total": round(avg_total, 2),
            "asymmetry": round(asymmetry, 2),
            "max_temp": round(max_temp, 2),
            "min_temp": round(min_temp, 2)
        }
    
    @staticmethod
    def classify_risk(asymmetry: float, max_temp: float) -> Tuple[str, List[str]]:
        """
        Classify risk level based on asymmetry and max temperature.
        
        Returns:
            Tuple of (risk_level, list of anomaly descriptions)
        """
        anomalies = []
        
        # Check asymmetry
        if asymmetry >= settings.ASYMMETRY_ELEVATED:
            anomalies.append(f"Значительная асимметрия: {asymmetry:.2f}°C")
        elif asymmetry >= settings.ASYMMETRY_NORMAL:
            anomalies.append(f"Умеренная асимметрия: {asymmetry:.2f}°C")
        
        # Check max temperature
        if max_temp >= settings.TEMP_ELEVATED_MAX:
            anomalies.append(f"Повышенная температура: {max_temp:.1f}°C")
        elif max_temp >= settings.TEMP_NORMAL_MAX:
            anomalies.append(f"Температура выше нормы: {max_temp:.1f}°C")
        
        # Determine risk level
        if asymmetry >= settings.ASYMMETRY_ELEVATED or max_temp >= settings.TEMP_ELEVATED_MAX:
            risk_level = "HIGH"
        elif asymmetry >= settings.ASYMMETRY_NORMAL or max_temp >= settings.TEMP_NORMAL_MAX:
            risk_level = "ELEVATED"
        else:
            risk_level = "NORMAL"
        
        return risk_level, anomalies
    
    @staticmethod
    def find_anomaly_zones(temps: List[float]) -> List[str]:
        """
        Identify specific zones with anomalous temperatures.
        
        Returns:
            List of zone names with anomalies
        """
        zone_names = [
            "Левая верхняя внутренняя",
            "Левая верхняя внешняя",
            "Левая нижняя внутренняя",
            "Левая нижняя внешняя",
            "Правая верхняя внутренняя",
            "Правая верхняя внешняя",
            "Правая нижняя внутренняя",
            "Правая нижняя внешняя"
        ]
        
        anomalies = []
        avg_temp = sum(temps) / len(temps)
        
        for i, temp in enumerate(temps):
            deviation = temp - avg_temp
            if deviation > 0.8:  # Zone is significantly warmer than average
                anomalies.append(f"{zone_names[i]}: +{deviation:.1f}°C")
        
        return anomalies
    
    @staticmethod
    def generate_conclusion(metrics: Dict, risk_level: str, anomalies: List[str]) -> str:
        """
        Generate a text conclusion based on analysis results.
        
        This is a rule-based generator. LLM integration can be added later.
        """
        if risk_level == "NORMAL":
            conclusion = (
                f"✅ Все показатели в пределах нормы.\n\n"
                f"Средняя температура левой груди: {metrics['avg_left']}°C\n"
                f"Средняя температура правой груди: {metrics['avg_right']}°C\n"
                f"Асимметрия: {metrics['asymmetry']}°C\n\n"
                f"Температурное распределение симметричное, признаков аномалий не обнаружено."
            )
        elif risk_level == "ELEVATED":
            conclusion = (
                f"⚠️ Обнаружены незначительные отклонения.\n\n"
                f"Средняя температура левой груди: {metrics['avg_left']}°C\n"
                f"Средняя температура правой груди: {metrics['avg_right']}°C\n"
                f"Асимметрия: {metrics['asymmetry']}°C\n\n"
                f"Выявленные отклонения:\n"
            )
            for anomaly in anomalies:
                conclusion += f"• {anomaly}\n"
            conclusion += (
                f"\nРекомендации: Повторите измерение через 24-48 часов. "
                f"При сохранении асимметрии рекомендуется консультация специалиста."
            )
        else:  # HIGH
            conclusion = (
                f"🔴 Обнаружены значимые отклонения от нормы.\n\n"
                f"Средняя температура левой груди: {metrics['avg_left']}°C\n"
                f"Средняя температура правой груди: {metrics['avg_right']}°C\n"
                f"Асимметрия: {metrics['asymmetry']}°C\n\n"
                f"Выявленные отклонения:\n"
            )
            for anomaly in anomalies:
                conclusion += f"• {anomaly}\n"
            conclusion += (
                f"\n⚠️ ВАЖНО: Рекомендуется обратиться к врачу-маммологу "
                f"для дополнительного обследования.\n\n"
                f"Данная система не является медицинским диагностическим устройством "
                f"и не заменяет консультацию специалиста."
            )
        
        return conclusion


analyzer = AnalyzerService()
