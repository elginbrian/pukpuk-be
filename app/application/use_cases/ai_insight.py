import random
from typing import List, Optional
from ..domain.entities.ai_insight import AIInsight, AIInsightResponse, ChatSession, ChatMessage
from ..domain.use_cases.ai_insight import IGenerateAIInsightUseCase, IChatSessionUseCase
from ..domain.interfaces.ai_insight import IAIInsightsRepository, IChatSessionRepository
from ..domain.interfaces.forecasting import IForecastRepository, IMetricsRepository
from ..domain.interfaces.route_optimization import IRouteOptimizationRepository
from ..domain.use_cases.forecasting import IGetForecastUseCase
import google.generativeai as genai
from datetime import datetime

class GenerateAIInsightUseCase(IGenerateAIInsightUseCase):
    def __init__(self, ai_insights_repo: IAIInsightsRepository, forecast_repo: IForecastRepository, metrics_repo: IMetricsRepository, chat_session_repo: IChatSessionRepository, route_repo: IRouteOptimizationRepository, forecast_use_case: IGetForecastUseCase):
        self.ai_insights_repo = ai_insights_repo
        self.forecast_repo = forecast_repo
        self.metrics_repo = metrics_repo
        self.chat_session_repo = chat_session_repo
        self.route_repo = route_repo
        self.forecast_use_case = forecast_use_case
        self._model_configured = False

    async def execute(self, query: str, crop_type: str, region: str, season: str, session_id: Optional[str] = None) -> AIInsightResponse:
        # Parse query for dynamic forecasting parameters
        forecast_params = self._parse_forecast_parameters(query)
        
        # Use parsed parameters or fall back to defaults
        forecast_crop = forecast_params.get('crop_type', crop_type)
        forecast_region = forecast_params.get('region', region)
        forecast_season = forecast_params.get('season', season)

        # Get current forecast data and metrics for context
        forecast_data = await self.forecast_repo.get_forecast_data(forecast_crop, forecast_region, forecast_season)
        metrics = await self.metrics_repo.get_latest_metrics(forecast_crop, forecast_region, forecast_season)

        # If no forecast data exists and user is asking for forecast, run a new forecast
        if not forecast_data and self._is_forecast_request(query):
            try:
                forecast_data = await self.forecast_use_case.execute(forecast_crop, forecast_region, forecast_season)
            except Exception as e:
                print(f"Failed to run forecast: {e}")

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
        ai_response, suggestions = await self._generate_ai_response(query, forecast_data, metrics, forecast_crop, forecast_region, forecast_season, conversation_history)

        # Save the insight to database if available
        insight = AIInsight(
            user_query=query,
            ai_response=ai_response,
            suggestions=suggestions,
            crop_type=forecast_crop,
            region=forecast_region,
            season=forecast_season,
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

    async def get_recent_insights(self, limit: int = 10) -> List[AIInsight]:
        return await self.ai_insights_repo.get_all_recent_insights(limit)

    async def get_recent_insights(self, limit: int = 10) -> List[AIInsight]:
        return await self.ai_insights_repo.get_all_recent_insights(limit)

    def _parse_forecast_parameters(self, query: str) -> dict:
        """Parse query to extract forecasting parameters like crop_type, region, season"""
        query_lower = query.lower()
        params = {}
        
        # Define known crop types, regions, and seasons from seeding data
        crop_types = ['rice', 'corn', 'sugarcane', 'soybean']
        regions = ['malang regency', 'blitar regency', 'kediri regency', 'madiun regency', 'jember regency']
        seasons = ['wet-season', 'dry-season']
        
        # Extract crop type
        for crop in crop_types:
            if crop in query_lower:
                params['crop_type'] = crop
                break
        
        # Extract region
        for region in regions:
            if region in query_lower or region.replace(' regency', '') in query_lower:
                params['region'] = region
                break
        
        # Extract season
        for season in seasons:
            if season in query_lower or season.replace('-', ' ') in query_lower:
                params['season'] = season
                break
        
        return params

    async def _run_forecast_for_request(self, params: dict) -> str:
        """Run forecast for specific parameters and return formatted results"""
        try:
            crop_type = params.get('crop_type', 'rice')
            region = params.get('region', 'malang regency')
            season = params.get('season', 'wet-season')

            # Get forecast data
            forecast_data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
            metrics = await self.metrics_repo.get_latest_metrics(crop_type, region, season)

            result = f"Forecast Results for {crop_type.title()} in {region.title()} ({season}):\n"

            if metrics:
                result += f"Performance Metrics: MAE={metrics.mae:.1f}, RMSE={metrics.rmse:.1f}, Trend={metrics.demand_trend:.1f}%\n"

            if forecast_data:
                result += "Monthly Forecast:\n"
                for item in forecast_data[:6]:  # Show first 6 months
                    actual_str = f", Actual={item.actual:.0f}" if item.actual else ""
                    result += f"- {item.month}: Predicted={item.predicted:.0f} tons{actual_str}\n"

            return result
        except Exception as e:
            return f"Unable to run forecast: {str(e)}"

    def _is_forecast_request(self, query: str) -> bool:
        """Check if the query is requesting a forecast"""
        forecast_keywords = ['forecast', 'predict', 'prediction', 'ramal', 'perkiraan', 'prediksi', 'future', 'next month', 'next season']
        query_lower = query.lower()
        
        return any(keyword in query_lower for keyword in forecast_keywords)

    def _get_gemini_model(self):
        """Get cached Gemini model instance to prevent resource leaks."""
        from ...infrastructure.config.settings import settings
        
        if not settings.gemini_api_key:
            return None
        
        if not self._model_configured:
            genai.configure(api_key=settings.gemini_api_key)
            self._model_configured = True
        
        if self._model is None:
            self._model = genai.GenerativeModel('gemini-2.5-flash')
        
        return self._model
    
    async def _generate_ai_response(self, query: str, forecast_data: List, metrics, crop_type: str, region: str, season: str, conversation_history: List = None) -> tuple[str, List[str]]:
        from ...infrastructure.config.settings import settings

        if not settings.gemini_api_key:
            return "Gemini API key not configured. Please set GEMINI_API_KEY in your .env file.", []

        try:
            model = self._get_gemini_model()
            if model is None:
                return "Gemini API key not configured. Please set GEMINI_API_KEY in your .env file.", []

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

         
            forecast_params = self._parse_forecast_parameters(query)
            forecast_context = ""
            
            if forecast_params and self._is_forecast_request(query):
                forecast_result = await self._run_forecast_for_request(forecast_params)
                if forecast_result:
                    forecast_context = f"\n\nRequested Forecast Analysis:\n{forecast_result}"

            prompt = f"""You are an intelligent supply chain assistant for agricultural demand forecasting and logistics optimization. You have access to comprehensive data about the supply chain operations including forecasting, inventory, and route optimization.

Available forecasting options:
- Crops: rice, corn, sugarcane, soybean
- Regions: malang regency, blitar regency, kediri regency, madiun regency, jember regency
- Seasons: wet-season, dry-season

I can dynamically run forecasts for different crop types, regions, and seasons based on your requests. If you ask about forecasting for specific parameters, I'll automatically run the appropriate forecast analysis.

{context}{forecast_context}{history_context}

Current User query: {query}

As a supply chain expert, provide helpful, analytical responses based on the available data. Focus on:
- Demand forecasting and trends analysis
- Inventory optimization and stock management
- Route optimization and logistics efficiency
- Transportation cost analysis and CO2 emissions
- Fleet utilization and capacity planning
- Network optimization across plants, warehouses, and retail locations
- Risk identification and mitigation strategies
- Performance metrics interpretation
- Data-driven recommendations for operational improvements

Be conversational but professional. Provide specific, actionable insights when possible. If you don't have enough data to answer definitively, acknowledge the limitations and suggest what additional information would help.

Keep responses concise but informative."""

            response = model.generate_content(prompt)
            ai_response = response.text.strip()

            # Generate dynamic suggestions using AI
            suggestions = await self._generate_ai_suggestions(query, ai_response, context, crop_type, region, season)

            return ai_response, suggestions

        except Exception as e:
            # Return error message in chat instead of raising exception
            return f"Failed to generate AI response using Gemini API: {str(e)}", []

    async def _generate_ai_suggestions(self, query: str, ai_response: str, context: str, crop_type: str, region: str, season: str) -> List[str]:
        """Generate contextual suggestions using AI based on the conversation"""
        from ...infrastructure.config.settings import settings

        if not settings.gemini_api_key:
            return ["What's the current demand trend?", "Analyze route efficiency", "Check forecasting accuracy"]

        try:
            model = self._get_gemini_model()
            if model is None:
                return ["What's the current demand trend?", "Analyze route efficiency", "Check forecasting accuracy"]

            # Available options for forecasting
            available_crops = ["rice", "corn", "sugarcane", "soybean"]
            available_regions = ["malang regency", "blitar regency", "kediri regency", "madiun regency", "jember regency"]
            available_seasons = ["wet-season", "dry-season"]

            suggestions_prompt = f"""Based on the following context and AI response, generate 4-6 relevant follow-up questions that a user might ask next. These should be specific, actionable questions that build on the current conversation.

Available forecasting options:
- Crops: {', '.join(available_crops)}
- Regions: {', '.join(available_regions)}
- Seasons: {', '.join(available_seasons)}

Context: {context[:1000]}...  # Truncated for brevity

User's original query: {query}

AI's response: {ai_response[:500]}...  # Truncated for brevity

Generate 3 SHORT follow-up questions (under 6 words each) that would be natural next steps in this supply chain analysis conversation. Include questions that:
- Request forecasts for different crops, regions, or seasons
- Compare data across different parameters
- Ask for deeper analysis of current topics
- Request optimization suggestions
- Ask about performance metrics
- Inquire about logistics and routing

Make questions concise and direct. Return only the questions as a numbered list, one per line."""

            suggestions_response = model.generate_content(suggestions_prompt)
            suggestions_text = suggestions_response.text.strip()

            # Parse the suggestions from the AI response
            suggestions = []
            for line in suggestions_text.split('\n'):
                line = line.strip()
                # Remove numbering (1., 2., etc.) and clean up
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove leading numbers, dashes, and extra spaces
                    cleaned = line.lstrip('123456789-. ').strip()
                    if cleaned and len(cleaned) > 5 and len(cleaned) < 100:  # Reasonable length for questions
                        suggestions.append(cleaned)

            # Ensure we have at least 3 suggestions, fallback to basic ones if needed
            if len(suggestions) < 3:
                suggestions.extend([
                    "What's the demand trend?",
                    "Analyze route efficiency",
                    "Check forecast accuracy"
                ])

            return suggestions[:6]  # Return up to 6 suggestions

        except Exception as e:
            # Fallback to basic suggestions if AI generation fails
            return [
                "What's the demand trend?",
                "Show inventory suggestions",
                "Analyze routes",
                "Check accuracy"
            ]

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

        try:
            locations = await self.route_repo.get_locations()
            vehicles = await self.route_repo.get_vehicles()
            route_configs = await self.route_repo.get_route_configurations()

            if locations:
                context_parts.append(f"""
Logistics Network:
- Total Locations: {len(locations)}
- Location Types: {', '.join(set([loc.type for loc in locations]))}
- Key Locations: {', '.join([f"{loc.name} ({loc.type})" for loc in locations[:5]])}""")

            if vehicles:
                context_parts.append(f"""
Fleet Information:
- Available Vehicles: {len(vehicles)}
- Vehicle Types: {', '.join([f"{v.name} ({v.min_capacity}-{v.max_capacity} tons)" for v in vehicles])}""")

            if route_configs:
                context_parts.append(f"""
Route Configurations:
- Total Routes: {len(route_configs)}
- Route Examples: {', '.join([f"{config.origin}→{config.destination}" for config in route_configs[:3]])}""")

        except Exception as e:
            context_parts.append(f"""
Logistics Data: Currently unavailable ({str(e)})""")

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
- I can run forecasts dynamically for any crop type, region, and season combination
- Supply chain challenges include weather dependency, transportation logistics, and inventory management
- Performance metrics help track forecasting accuracy and operational efficiency
- Route optimization considers distance, fuel costs, tolls, CO2 emissions, and delivery time
- Fleet includes various truck sizes optimized for different load capacities
- Network spans plants, warehouses, and retail kiosks across multiple regions"""

        return full_context


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