import random
from typing import List, Optional
from ..domain.entities.ai_insight import AIInsight, AIInsightResponse, ChatSession, ChatMessage
from ..domain.use_cases.ai_insight import IGenerateAIInsightUseCase, IChatSessionUseCase
from ..domain.interfaces.ai_insight import IAIInsightsRepository, IChatSessionRepository
from ..domain.interfaces.forecasting import IForecastRepository, IMetricsRepository
import google.generativeai as genai
from datetime import datetime

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
                    conversation_history = await self.chat_session_repo.get_conversation_history(session_id, limit=10)
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
                    session_id=session_id,
                    role="user",
                    content=query,
                    timestamp=datetime.utcnow()
                )
                ai_message = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=ai_response,
                    timestamp=datetime.utcnow()
                )
                await self.chat_session_repo.save_message(user_message)
                await self.chat_session_repo.save_message(ai_message)
            except Exception:
                # If session saving fails, continue without error
                pass

        return AIInsightResponse(response=ai_response, suggestions=suggestions)

    async def _generate_ai_response(self, query: str, forecast_data: List, metrics, crop_type: str, region: str, season: str, conversation_history: List = None) -> tuple[str, List[str]]:
        from ...infrastructure.config.settings import settings

        if not settings.gemini_api_key:
            return "Gemini API key not configured. Please set GEMINI_API_KEY in your .env file.", []

        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

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
            # Return error message in chat instead of raising exception
            return f"Failed to generate AI response using Gemini API: {str(e)}", []

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
        return await self.chat_session_repo.create_session(crop_type, region, season)

    async def chat(self, session_id: str, message: str) -> tuple[str, List[str]]:
        # This method is handled by GenerateAIInsightUseCase
        # This is just an interface implementation
        raise NotImplementedError("Use GenerateAIInsightUseCase for chat functionality")

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        session = await self.chat_session_repo.get_session(session_id)
        if not session:
            return []
        return session.messages[-limit:] if session.messages else []