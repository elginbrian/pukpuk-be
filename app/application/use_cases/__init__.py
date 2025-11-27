import random
from typing import List
from ..domain.entities import ForecastData, Metrics, AIInsight, AIInsightResponse
from ..domain.use_cases import IGetForecastUseCase, IGetMetricsUseCase, ISimulateScenarioUseCase, IGenerateAIInsightUseCase
from ..domain.interfaces import IForecastRepository, IMetricsRepository, IAIInsightsRepository
from ...infrastructure.utils.export_service import ExportService
import google.generativeai as genai
from datetime import datetime

class GetForecastUseCase(IGetForecastUseCase):
    def __init__(self, forecast_repo: IForecastRepository, metrics_repo: IMetricsRepository):
        self.forecast_repo = forecast_repo
        self.metrics_repo = metrics_repo

    async def execute(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        # Get data from repository (will return empty list if database not available)
        data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        if data:
            return data

        # Generate and save data only if database is available
        from ...infrastructure.database.database import is_database_available
        if is_database_available():
            data = self._generate_forecast_data(crop_type, region, season)
            await self.forecast_repo.save_forecast_data(data)
        return data

    def _generate_forecast_data(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
        data = []
        base_demand = 4000 + random.randint(-500, 500)

        for i, month in enumerate(months):
            actual = base_demand + random.randint(-300, 300) if i < 6 else None
            predicted = base_demand + random.randint(-200, 400)
            data.append(ForecastData(
                month=month,
                actual=actual,
                predicted=predicted,
                crop_type=crop_type,
                region=region,
                season=season
            ))

        return data

class GetMetricsUseCase(IGetMetricsUseCase):
    def __init__(self, metrics_repo: IMetricsRepository):
        self.metrics_repo = metrics_repo

    async def execute(self, crop_type: str, region: str, season: str) -> Metrics:
        # Get metrics from repository (handles database availability)
        return await self.metrics_repo.get_latest_metrics(crop_type, region, season)

    def _generate_metrics(self, crop_type: str, region: str, season: str) -> Metrics:
        return Metrics(
            mae=142 + random.uniform(-20, 20),
            rmse=218 + random.uniform(-30, 30),
            demand_trend=15.3 + random.uniform(-5, 5),
            volatility_score=0.68 + random.uniform(-0.1, 0.1),
            crop_type=crop_type,
            region=region,
            season=season
        )

class SimulateScenarioUseCase(ISimulateScenarioUseCase):
    def __init__(self, forecast_repo: IForecastRepository):
        self.forecast_repo = forecast_repo

    async def execute(self, rainfall_change: float, crop_type: str = "rice", region: str = "jawa-barat", season: str = "wet-season") -> List[ForecastData]:
        # Get base forecast data
        data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        
        # If no data and database is available, generate base data
        from ...infrastructure.database.database import is_database_available
        if not data and is_database_available():
            # Generate base data
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
            data = []
            base_demand = 4000 + random.randint(-500, 500)
            for i, month in enumerate(months):
                actual = base_demand + random.randint(-300, 300) if i < 6 else None
                predicted = base_demand + random.randint(-200, 400)
                data.append(ForecastData(
                    month=month,
                    actual=actual,
                    predicted=predicted,
                    crop_type=crop_type,
                    region=region,
                    season=season
                ))
            await self.forecast_repo.save_forecast_data(data)

        # Apply rainfall change to predictions if we have data
        if data:
            for item in data:
                if item.predicted:
                    item.predicted *= (1 + rainfall_change / 100)

        return data

class GenerateAIInsightUseCase(IGenerateAIInsightUseCase):
    def __init__(self, ai_insights_repo: IAIInsightsRepository, forecast_repo: IForecastRepository, metrics_repo: IMetricsRepository):
        self.ai_insights_repo = ai_insights_repo
        self.forecast_repo = forecast_repo
        self.metrics_repo = metrics_repo

    async def execute(self, query: str, crop_type: str, region: str, season: str) -> AIInsightResponse:
        # Get current forecast data and metrics for context
        forecast_data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        metrics = await self.metrics_repo.get_latest_metrics(crop_type, region, season)

        # Generate AI response using Gemini
        ai_response, suggestions = await self._generate_ai_response(query, forecast_data, metrics, crop_type, region, season)

        # Save the insight to database if available
        insight = AIInsight(
            user_query=query,
            ai_response=ai_response,
            suggestions=suggestions,
            crop_type=crop_type,
            region=region,
            season=season,
            created_at=datetime.utcnow()
        )
        await self.ai_insights_repo.save_insight(insight)

        return AIInsightResponse(response=ai_response, suggestions=suggestions)

    async def _generate_ai_response(self, query: str, forecast_data: List[ForecastData], metrics: Metrics, crop_type: str, region: str, season: str) -> tuple[str, List[str]]:
        from ...infrastructure.config.settings import settings

        if not settings.gemini_api_key:
            # Fallback to mock responses if API key not configured
            return self._generate_mock_response(query), self._generate_suggestions(query)

        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Prepare context data
            context = self._prepare_context_data(forecast_data, metrics, crop_type, region, season)

            prompt = f"""
You are an AI supply chain assistant for agricultural demand forecasting. You have access to the following data:

{context}

User query: {query}

Please provide a helpful, analytical response based on the available data. Focus on:
- Demand forecasting insights
- Inventory optimization recommendations
- Risk identification and mitigation
- Supply chain efficiency improvements

Keep your response concise but informative, and provide actionable insights.
"""

            response = model.generate_content(prompt)
            ai_response = response.text.strip()

            # Generate suggestions based on the query and response
            suggestions = self._generate_suggestions(query)

            return ai_response, suggestions

        except Exception as e:
            # Fallback to mock response on error
            return self._generate_mock_response(query), self._generate_suggestions(query)

    def _prepare_context_data(self, forecast_data: List[ForecastData], metrics: Metrics, crop_type: str, region: str, season: str) -> str:
        context = f"""
Crop Type: {crop_type}
Region: {region}
Season: {season}

Current Metrics:
- MAE (Mean Absolute Error): {metrics.mae:.2f}
- RMSE (Root Mean Square Error): {metrics.rmse:.2f}
- Demand Trend: {metrics.demand_trend:.2f}%
- Volatility Score: {metrics.volatility_score:.3f}

Forecast Data:
"""

        if forecast_data:
            for item in forecast_data[:5]:  # Show first 5 months
                context += f"- {item.month}: Actual={item.actual or 'N/A'}, Predicted={item.predicted:.1f}\n"
        else:
            context += "No forecast data available\n"

        return context

    def _generate_mock_response(self, query: str) -> str:
        if query.lower().includes("high demand") or query.lower().includes("kecamatan"):
            return "Based on the CatBoost multivariate forecasting model, Kecamatan X shows elevated demand due to three key factors:\n\n1. **Seasonal patterns**: Rice planting season begins in 3 weeks\n2. **Weather forecast**: 15% above-average rainfall predicted\n3. **Historical trends**: Last year showed 18% demand spike in this period\n\nRecommended action: Increase stock allocation by 12% (approx. 2.1 tons) to meet projected demand of 19.4 tons."
        elif query.lower().includes("warehouse b") or query.lower().includes("dead-stock"):
            return "Warehouse B dead-stock analysis:\n\n**Issue**: 680 tons with no movement for 18 days indicates dead-stock risk.\n\n**Root cause**: Overstocking during low-demand period, regional demand shift to neighboring areas.\n\n**Recommended actions**:\n1. Transfer 250 tons to Warehouse A (cost: Rp 2.1M via Route B)\n2. Redistribute 150 tons to Kios network in high-demand areas\n3. Reduce next month's allocation by 40%\n\n**Cost savings**: Estimated Rp 8.5M in storage and opportunity costs."
        else:
            return "I've analyzed your query using the latest supply chain data. Could you provide more specific details about what aspect you'd like me to focus on? I can help with demand forecasting, route optimization, inventory analysis, or risk detection."

    def _generate_suggestions(self, query: str) -> List[str]:
        base_suggestions = [
            "Why is Kecamatan X showing high demand next month?",
            "Recommend redistribution from Warehouse B",
            "Explain the dead-stock alert for Warehouse B",
            "What's driving demand in Yogyakarta region?"
        ]

        if "demand" in query.lower():
            return ["Show me demand trends for next quarter", "Which regions need more inventory?", "Compare demand vs actual sales"]
        elif "warehouse" in query.lower() or "inventory" in query.lower():
            return ["Optimize inventory levels across warehouses", "Identify dead-stock locations", "Plan redistribution routes"]
        elif "route" in query.lower() or "distribution" in query.lower():
            return ["Calculate optimal delivery routes", "Estimate transportation costs", "Plan emergency redistribution"]
        else:
            return base_suggestions