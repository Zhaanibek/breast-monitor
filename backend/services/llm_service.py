"""
LLM Service for generating intelligent analysis conclusions
"""
import os
from typing import Dict, Optional


class LLMService:
    """Service for generating AI-powered analysis conclusions"""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self._openai_client = None
        self._gemini_model = None
    
    def _get_openai_client(self):
        """Lazy initialization of OpenAI client"""
        if self._openai_client is None and self.openai_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.openai_key)
            except ImportError:
                pass
        return self._openai_client
    
    def _get_gemini_model(self):
        """Lazy initialization of Gemini model"""
        if self._gemini_model is None and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self._gemini_model = genai.GenerativeModel('gemini-pro')
            except ImportError:
                pass
        return self._gemini_model
    
    def _build_prompt(self, metrics: Dict, risk_level: str, anomalies: list) -> str:
        """Build prompt for LLM"""
        return f"""Ты медицинский ассистент системы мониторинга температуры молочных желез. 
Сгенерируй краткое заключение по результатам термографического анализа.

Данные измерения:
- Средняя температура левой груди: {metrics['avg_left']}°C
- Средняя температура правой груди: {metrics['avg_right']}°C
- Температурная асимметрия: {metrics['asymmetry']}°C
- Максимальная температура: {metrics['max_temp']}°C
- Уровень риска: {risk_level}
- Выявленные отклонения: {', '.join(anomalies) if anomalies else 'нет'}

Требования к заключению:
1. Объясни результаты простым языком
2. Укажи возможные причины отклонений (если есть)
3. Дай рекомендации по дальнейшим действиям
4. ОБЯЗАТЕЛЬНО укажи, что система не заменяет врачебную консультацию
5. Не ставь диагнозы, говори только о температурных показателях

Формат: 2-3 абзаца, без заголовков. Пиши на русском языке."""
    
    async def generate_conclusion_openai(self, metrics: Dict, risk_level: str, anomalies: list) -> Optional[str]:
        """Generate conclusion using OpenAI API"""
        client = self._get_openai_client()
        if not client:
            return None
        
        try:
            prompt = self._build_prompt(metrics, risk_level, anomalies)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты медицинский ассистент для анализа термографических данных."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI error: {e}")
            return None
    
    async def generate_conclusion_gemini(self, metrics: Dict, risk_level: str, anomalies: list) -> Optional[str]:
        """Generate conclusion using Google Gemini API"""
        model = self._get_gemini_model()
        if not model:
            return None
        
        try:
            prompt = self._build_prompt(metrics, risk_level, anomalies)
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return None
    
    async def generate_conclusion(self, metrics: Dict, risk_level: str, anomalies: list) -> str:
        """
        Generate conclusion using available LLM provider.
        Falls back to rule-based generation if no LLM is available.
        """
        # Try OpenAI first
        if self.openai_key:
            result = await self.generate_conclusion_openai(metrics, risk_level, anomalies)
            if result:
                return result
        
        # Try Gemini
        if self.gemini_key:
            result = await self.generate_conclusion_gemini(metrics, risk_level, anomalies)
            if result:
                return result
        
        # Fallback to rule-based generation
        return self._generate_rule_based(metrics, risk_level, anomalies)
    
    def _generate_rule_based(self, metrics: Dict, risk_level: str, anomalies: list) -> str:
        """Rule-based conclusion generation (fallback)"""
        if risk_level == "NORMAL":
            return (
                f"✅ Результаты термографического анализа в пределах нормы.\n\n"
                f"Средняя температура левой молочной железы составляет {metrics['avg_left']}°C, "
                f"правой — {metrics['avg_right']}°C. Температурная асимметрия ({metrics['asymmetry']}°C) "
                f"находится в допустимых пределах, что свидетельствует о нормальном распределении тепла.\n\n"
                f"Рекомендуется продолжать регулярный мониторинг. Данная система является "
                f"вспомогательным инструментом и не заменяет консультацию врача-маммолога."
            )
        elif risk_level == "ELEVATED":
            anomaly_text = ", ".join(anomalies) if anomalies else "незначительная асимметрия"
            return (
                f"⚠️ Обнаружены незначительные отклонения от нормы.\n\n"
                f"Выявлено: {anomaly_text}. Средняя температура левой молочной железы — "
                f"{metrics['avg_left']}°C, правой — {metrics['avg_right']}°C. "
                f"Подобные отклонения могут быть связаны с естественными колебаниями температуры тела, "
                f"физической активностью, фазой менструального цикла или внешними факторами.\n\n"
                f"Рекомендуется повторить измерение через 24-48 часов для подтверждения результатов. "
                f"При сохранении асимметрии рекомендуется консультация специалиста. "
                f"Данная система не является медицинским диагностическим устройством."
            )
        else:  # HIGH
            anomaly_text = ", ".join(anomalies) if anomalies else "значительная температурная асимметрия"
            return (
                f"🔴 Обнаружены значимые отклонения от нормы.\n\n"
                f"Выявлено: {anomaly_text}. Температурная асимметрия составляет {metrics['asymmetry']}°C, "
                f"что превышает пороговое значение. Максимальная зафиксированная температура: "
                f"{metrics['max_temp']}°C. Подобные изменения могут указывать на различные состояния, "
                f"требующие внимания специалиста.\n\n"
                f"⚠️ ВАЖНО: Рекомендуется обратиться к врачу-маммологу для дополнительного обследования. "
                f"Данная система является вспомогательным скрининговым инструментом и НЕ заменяет "
                f"профессиональную медицинскую диагностику. Не откладывайте визит к специалисту."
            )


# Singleton instance
llm_service = LLMService()
