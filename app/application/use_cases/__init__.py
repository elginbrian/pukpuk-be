import random
from typing import List, Optional
from ..domain.entities import ForecastData, Metrics, AIInsight, AIInsightResponse, ChatSession, ChatMessage
from ..domain.use_cases import IGetForecastUseCase, IGetMetricsUseCase, ISimulateScenarioUseCase, IGenerateAIInsightUseCase, IChatSessionUseCase
from ..domain.interfaces import IForecastRepository, IMetricsRepository, IAIInsightsRepository, IChatSessionRepository
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
    def __init__(self, ai_insights_repo: IAIInsightsRepository, forecast_repo: IForecastRepository, metrics_repo: IMetricsRepository, chat_session_repo: IChatSessionRepository):
        self.ai_insights_repo = ai_insights_repo
        self.forecast_repo = forecast_repo
        self.metrics_repo = metrics_repo
        self.chat_session_repo = chat_session_repo

    async def execute(self, query: str, crop_type: str, region: str, season: str, session_id: Optional[str] = None) -> AIInsightResponse:
        # Get current forecast data and metrics for context
        forecast_data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        metrics = await self.metrics_repo.get_latest_metrics(crop_type, region, season)

        # Load conversation history if session_id provided
        conversation_history = []
        if session_id:
            try:
                session = await self.chat_session_repo.get_session(session_id)
                if session:
                    conversation_history = session.messages[-10:]  # Last 10 messages for context
            except Exception:
                # If session loading fails, continue without history
                pass

        # Generate AI response using Gemini
        ai_response, suggestions = await self._generate_ai_response(query, forecast_data, metrics, crop_type, region, season, conversation_history)

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

        # Save message to session if session_id provided
        if session_id:
            try:
                from ..domain.entities import ChatMessage
                user_message = ChatMessage(
                    role="user",
                    content=query,
                    timestamp=datetime.utcnow()
                )
                ai_message = ChatMessage(
                    role="assistant",
                    content=ai_response,
                    timestamp=datetime.utcnow()
                )
                await self.chat_session_repo.add_message(session_id, user_message)
                await self.chat_session_repo.add_message(session_id, ai_message)
            except Exception:
                # If session saving fails, continue without error
                pass

        return AIInsightResponse(response=ai_response, suggestions=suggestions)

    async def _generate_ai_response(self, query: str, forecast_data: List[ForecastData], metrics: Metrics, crop_type: str, region: str, season: str, conversation_history: List = None) -> tuple[str, List[str]]:
        from ...infrastructure.config.settings import settings

        if not settings.gemini_api_key:
            # Fallback to mock responses if API key not configured
            return self._generate_mock_response(query), self._generate_suggestions(query)

        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Get comprehensive data from database
            context = await self._build_comprehensive_context(crop_type, region, season)

            # Build conversation history context
            history_context = ""
            if conversation_history:
                history_lines = []
                for msg in conversation_history[-6:]:  # Last 6 messages for context
                    role = "User" if msg.role == "user" else "Assistant"
                    history_lines.append(f"{role}: {msg.content}")
                history_context = f"\n\nConversation History:\n" + "\n".join(history_lines) + "\n"

            prompt = f"""You are an intelligent supply chain assistant for agricultural demand forecasting. You have access to comprehensive data about the supply chain operations.

{context}{history_context}

Current User query: {query}

As a supply chain expert, provide helpful, analytical responses based on the available data. Focus on:
- Demand forecasting and trends analysis
- Inventory optimization and stock management
- Route optimization and logistics
- Risk identification and mitigation strategies
- Performance metrics interpretation
- Data-driven recommendations

Be conversational but professional. Provide specific, actionable insights when possible. If you don't have enough data to answer definitively, acknowledge the limitations and suggest what additional information would help.

Keep responses concise but informative."""

            response = model.generate_content(prompt)
            ai_response = response.text.strip()

            # Generate suggestions based on the query and response
            suggestions = self._generate_suggestions(query)

            return ai_response, suggestions

        except Exception as e:
            # Fallback to mock response on error
            return self._generate_mock_response(query), self._generate_suggestions(query)

    async def _build_comprehensive_context(self, crop_type: str, region: str, season: str) -> str:
        """Build comprehensive context from all available data"""
        context_parts = []

        # Current metrics
        metrics = await self.metrics_repo.get_latest_metrics(crop_type, region, season)
        if metrics:
            context_parts.append(f"""
Current Performance Metrics:
- Mean Absolute Error (MAE): {metrics.mae:.2f}
- Root Mean Square Error (RMSE): {metrics.rmse:.2f}
- Demand Trend: {metrics.demand_trend:.2f}%
- Volatility Score: {metrics.volatility_score:.3f}""")

        # Forecast data
        forecast_data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        if forecast_data:
            context_parts.append(f"""
Recent Forecast Data ({crop_type}, {region}, {season}):
{chr(10).join([f"- {item.month}: Predicted={item.predicted:.1f} tons" + (f", Actual={item.actual:.1f} tons" if item.actual else "") for item in forecast_data[:6]])}""")

        # AI insights history
        recent_insights = await self.ai_insights_repo.get_recent_insights(crop_type, region, season, limit=5)
        if recent_insights:
            context_parts.append(f"""
Recent AI Insights:
{chr(10).join([f"- {insight.user_query[:50]}...: {insight.ai_response[:100]}..." for insight in recent_insights])}""")

        # Combine all context
        full_context = f"""
Supply Chain Context:
Crop: {crop_type}
Region: {region}
Season: {season}

{"".join(context_parts)}

General Supply Chain Knowledge:
- Rice is the primary crop with seasonal demand patterns
- Key regions include Java Barat, Yogyakarta, and surrounding areas
- Supply chain challenges include weather dependency, transportation logistics, and inventory management
- Performance metrics help track forecasting accuracy and operational efficiency"""

        return full_context

    def _generate_mock_response(self, query: str) -> str:
        if query.lower().includes("high demand") or query.lower().includes("kecamatan"):
            return "Based on the CatBoost multivariate forecasting model, Kecamatan X shows elevated demand due to three key factors:\n\n1. **Seasonal patterns**: Rice planting season begins in 3 weeks\n2. **Weather forecast**: 15% above-average rainfall predicted\n3. **Historical trends**: Last year showed 18% demand spike in this period\n\nRecommended action: Increase stock allocation by 12% (approx. 2.1 tons) to meet projected demand of 19.4 tons."
        elif query.lower().includes("warehouse b") or query.lower().includes("dead-stock"):
            return "Warehouse B dead-stock analysis:\n\n**Issue**: 680 tons with no movement for 18 days indicates dead-stock risk.\n\n**Root cause**: Overstocking during low-demand period, regional demand shift to neighboring areas.\n\n**Recommended actions**:\n1. Transfer 250 tons to Warehouse A (cost: Rp 2.1M via Route B)\n2. Redistribute 150 tons to Kios network in high-demand areas\n3. Reduce next month's allocation by 40%\n\n**Cost savings**: Estimated Rp 8.5M in storage and opportunity costs."
        else:
            return "I've analyzed your query using the latest supply chain data. Could you provide more specific details about what aspect you'd like me to focus on? I can help with demand forecasting, route optimization, inventory analysis, or risk detection."

    def _generate_suggestions(self, query: str) -> List[str]:
        base_suggestions = [
            "What's the current demand trend?",
            "Show me inventory optimization suggestions",
            "Analyze route efficiency",
            "Check forecasting accuracy"
        ]

        query_lower = query.lower()

        if any(word in query_lower for word in ["demand", "forecast", "trend"]):
            return ["Compare demand vs actual sales", "Show seasonal demand patterns", "Predict next month demand", "Identify demand drivers"]
        elif any(word in query_lower for word in ["inventory", "stock", "warehouse"]):
            return ["Optimize inventory levels", "Find dead-stock locations", "Plan redistribution", "Check stock turnover"]
        elif any(word in query_lower for word in ["route", "distribution", "logistics"]):
            return ["Calculate optimal routes", "Estimate transportation costs", "Find delivery bottlenecks", "Optimize delivery schedules"]
        elif any(word in query_lower for word in ["performance", "metrics", "accuracy"]):
            return ["Analyze forecasting accuracy", "Check model performance", "Identify improvement areas", "Compare metrics over time"]
        else:
            return base_suggestions


class ChatSessionUseCase(IChatSessionUseCase):
    def __init__(self, chat_session_repo: IChatSessionRepository):
        self.chat_session_repo = chat_session_repo

    async def create_session(self, crop_type: str, region: str, season: str) -> ChatSession:
        from ..domain.entities import ChatSession
        import uuid
        from datetime import datetime

        session = ChatSession(
            session_id=str(uuid.uuid4()),
            crop_type=crop_type,
            region=region,
            season=season,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await self.chat_session_repo.save_session(session)
        return session

    async def chat(self, session_id: str, message: str) -> tuple[str, List[str]]:
        # This method is handled by GenerateAIInsightUseCase
        # This is just an interface implementation
        raise NotImplementedError("Use GenerateAIInsightUseCase for chat functionality")

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        session = await self.chat_session_repo.get_session(session_id)
        if not session:
            return []
        return session.messages[-limit:] if session.messages else []