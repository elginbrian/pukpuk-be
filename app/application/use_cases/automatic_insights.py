from typing import List
from ..domain.use_cases.ai_insight import IAutomaticInsightsUseCase
from ..domain.interfaces.ai_insight import IAIInsightsRepository
from ..domain.interfaces.forecasting import IForecastRepository, IMetricsRepository
from ..domain.interfaces.route_optimization import IRouteOptimizationRepository
from ..domain.entities.ai_insight import AIInsight
import google.generativeai as genai
from datetime import datetime, timedelta

class AutomaticInsightsUseCase(IAutomaticInsightsUseCase):
    def __init__(self, ai_insights_repo: IAIInsightsRepository, forecast_repo: IForecastRepository, metrics_repo: IMetricsRepository, route_repo: IRouteOptimizationRepository):
        self.ai_insights_repo = ai_insights_repo
        self.forecast_repo = forecast_repo
        self.metrics_repo = metrics_repo
        self.route_repo = route_repo

    async def generate_insights(self, crop_type: str, region: str, season: str, limit: int = 3) -> List[dict]:
        """Generate automatic insights based on current data conditions"""
        from ...infrastructure.config.settings import settings
        
        # Check for recent insights in database (less than 3 hours old)
        three_hours_ago = datetime.utcnow() - timedelta(hours=3)
        
        # Get existing automatic insights (we need to distinguish them from chat insights)
        recent_insights = await self.ai_insights_repo.get_all_recent_insights(10)
        
        valid_recent_insights = []
        for insight in recent_insights:
            if insight.created_at > three_hours_ago:
                if any(keyword in insight.user_query.lower() for keyword in [
                    "automatic", "system", "generated", "insight", "analysis"
                ]) or len(insight.user_query.split()) <= 3:
                    valid_recent_insights.append({
                        "title": self._extract_title_from_insight(insight),
                        "description": insight.ai_response[:100],  # Truncate for display
                        "type": self._determine_insight_type(insight.user_query),
                        "priority": "medium"  # Default priority
                    })
        
        if len(valid_recent_insights) >= limit:
            return valid_recent_insights[:limit]
        
        if not settings.gemini_api_key:
            return await self._get_fallback_insights(limit)

        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            context = await self._build_comprehensive_context(crop_type, region, season)

            prompt = f"""Based on the following current supply chain data, generate {limit} key insights that would be valuable for a supply chain manager. Each insight should be actionable and focus on critical areas like demand forecasting, inventory management, route optimization, or operational efficiency.

{context}

Generate exactly {limit} insights in the following JSON format:
[
  {{
    "title": "Brief, descriptive title (max 5 words)",
    "description": "Detailed insight description (max 50 words)",
    "type": "One of: demand, inventory, route, general",
    "priority": "high, medium, or low"
  }}
]

Focus on:
- Current demand trends and forecasts
- Inventory levels and stock optimization
- Route efficiency and cost savings
- Operational bottlenecks or opportunities
- Performance metrics analysis

Make insights specific, actionable, and based on the actual data provided. Return only valid JSON."""

            response = model.generate_content(prompt)
            ai_response = response.text.strip()

            import json
            import re
            
            new_insights = []
            try:
                json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    new_insights = json.loads(json_str)
                else:
                    new_insights = json.loads(ai_response)
                
                if not isinstance(new_insights, list):
                    new_insights = []
                    
                validated_insights = []
                for insight in new_insights:
                    if isinstance(insight, dict) and 'title' in insight and 'description' in insight:
                        validated_insights.append({
                            'title': insight.get('title', 'Insight'),
                            'description': insight.get('description', 'Generated insight'),
                            'type': insight.get('type', 'general'),
                            'priority': insight.get('priority', 'medium')
                        })
                new_insights = validated_insights
                
            except (json.JSONDecodeError, Exception) as e:
                print(f"Failed to parse AI response as JSON: {str(e)}")
                print(f"AI Response: {ai_response[:500]}...")
                new_insights = []

            # If we got valid insights from Gemini, save and return them
            if new_insights and len(new_insights) > 0:
                # Save new insights to database
                for insight_data in new_insights[:limit]:
                    insight = AIInsight(
                        user_query=f"Automatic {insight_data.get('type', 'general')} insight",
                        ai_response=insight_data.get('description', ''),
                        suggestions=[insight_data.get('title', '')],
                        crop_type=crop_type,
                        region=region,
                        season=season,
                        created_at=datetime.utcnow()
                    )
                    await self.ai_insights_repo.save_insight(insight)

                return new_insights[:limit]

        except Exception as e:
            print(f"Failed to generate automatic insights: {str(e)}")

        # Return fallback insights if anything fails
        return await self._get_fallback_insights(limit)

    async def _get_fallback_insights(self, limit: int) -> List[dict]:
        """Return fallback insights when AI generation fails"""
        fallback_insights = [
            {
                "title": "Demand Monitoring",
                "description": "Regular monitoring of demand patterns shows seasonal variations. Consider adjusting inventory levels based on historical trends.",
                "type": "demand",
                "priority": "medium"
            },
            {
                "title": "Route Optimization",
                "description": "Optimizing delivery routes can reduce transportation costs by up to 15%. Review current routing algorithms for efficiency improvements.",
                "type": "route",
                "priority": "high"
            },
            {
                "title": "Inventory Management",
                "description": "Maintaining optimal inventory levels prevents stockouts and reduces holding costs. Consider implementing automated reorder points.",
                "type": "inventory",
                "priority": "medium"
            },
            {
                "title": "Performance Tracking",
                "description": "Track key performance indicators regularly to identify bottlenecks and improvement opportunities in your supply chain operations.",
                "type": "general",
                "priority": "low"
            }
        ]
        
        # Save fallback insights to database as well
        for insight_data in fallback_insights[:limit]:
            insight = AIInsight(
                user_query=f"Automatic {insight_data.get('type', 'general')} insight",
                ai_response=insight_data.get('description', ''),
                suggestions=[insight_data.get('title', '')],
                crop_type="rice",  # Default values
                region="malang regency",
                season="wet-season",
                created_at=datetime.utcnow()
            )
            try:
                await self.ai_insights_repo.save_insight(insight)
            except Exception:
                pass  # Ignore save errors for fallback
        
        return fallback_insights[:limit]

    def _extract_title_from_insight(self, insight: AIInsight) -> str:
        """Extract a title from an existing insight"""
        # Try to create a meaningful title from the response
        response_start = insight.ai_response[:30].strip()
        if len(response_start) > 20:
            return response_start[:20] + "..."
        return response_start or "Recent Insight"

    def _determine_insight_type(self, query: str) -> str:
        """Determine the type of insight based on the query"""
        query_lower = query.lower()
        if any(word in query_lower for word in ["demand", "forecast", "predict"]):
            return "demand"
        elif any(word in query_lower for word in ["inventory", "stock", "warehouse"]):
            return "inventory"
        elif any(word in query_lower for word in ["route", "transport", "delivery"]):
            return "route"
        else:
            return "general"

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

        # Combine all context
        full_context = f"""
Supply Chain Context:
Crop: {crop_type}
Region: {region}
Season: {season}

{"".join(context_parts)}

General Supply Chain Knowledge:
- Rice is the primary crop with seasonal demand patterns
- Supply chain challenges include weather dependency, transportation logistics, and inventory management
- Performance metrics help track forecasting accuracy and operational efficiency
- Route optimization considers distance, fuel costs, tolls, CO2 emissions, and delivery time
- Fleet includes various truck sizes optimized for different load capacities
- Network spans plants, warehouses, and retail kiosks across multiple regions"""

        return full_context