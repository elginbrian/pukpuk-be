from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.application.container import container
from app.application.use_cases import GenerateAIInsightUseCase, ChatSessionUseCase, AutomaticInsightsUseCase
from app.application.domain.entities import AIInsight

router = APIRouter(prefix="/ai-insight", tags=["ai-insight"])

# Pydantic models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = None  # Optional session ID for conversation continuity
    crop_type: str = "rice"
    region: str = "jawa-barat"
    season: str = "wet-season"

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str]

class CreateSessionRequest(BaseModel):
    crop_type: str = "rice"
    region: str = "jawa-barat"
    season: str = "wet-season"

class CreateSessionResponse(BaseModel):
    session_id: str
    crop_type: str
    region: str
    season: str
    created_at: str

class AIInsightModel(BaseModel):
    user_query: str
    ai_response: str
    suggestions: List[str]
    crop_type: str
    region: str
    season: str
    created_at: str

class AutomaticInsightModel(BaseModel):
    title: str
    description: str
    type: str
    priority: str

# Dependency injection
def get_generate_ai_insight_use_case() -> GenerateAIInsightUseCase:
    return container.generate_ai_insight_use_case()

def get_chat_session_use_case() -> ChatSessionUseCase:
    return container.chat_session_use_case()

def get_automatic_insights_use_case() -> AutomaticInsightsUseCase:
    return container.automatic_insights_use_case()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    use_case: GenerateAIInsightUseCase = Depends(get_generate_ai_insight_use_case)
):
    """Chat with AI assistant about supply chain data"""
    try:
        # Use the existing AI insight use case with session support
        result = await use_case.execute(
            query=request.message,
            crop_type=request.crop_type,
            region=request.region,
            season=request.season,
            session_id=request.session_id
        )

        return ChatResponse(
            response=result.response,
            suggestions=result.suggestions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@router.post("/session", response_model=CreateSessionResponse)
async def create_chat_session(
    request: CreateSessionRequest,
    use_case: ChatSessionUseCase = Depends(get_chat_session_use_case)
):
    """Create a new chat session for conversation continuity"""
    try:
        session = await use_case.create_session(
            crop_type=request.crop_type,
            region=request.region,
            season=request.season
        )

        return CreateSessionResponse(
            session_id=session.session_id,
            crop_type=session.crop_type,
            region=session.region,
            season=session.season,
            created_at=session.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session creation error: {str(e)}")

@router.get("/session/{session_id}/history", response_model=List[ChatMessage])
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    use_case: ChatSessionUseCase = Depends(get_chat_session_use_case)
):
    """Get conversation history for a session"""
    try:
        history = await use_case.get_conversation_history(session_id, limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval error: {str(e)}")

@router.get("/recent-insights", response_model=List[AIInsightModel])
async def get_recent_insights(
    limit: int = 10,
    use_case: GenerateAIInsightUseCase = Depends(get_generate_ai_insight_use_case)
):
    """Get recent AI insights from the database"""
    try:
        insights = await use_case.get_recent_insights(limit)
        return [
            AIInsightModel(
                user_query=insight.user_query,
                ai_response=insight.ai_response,
                suggestions=insight.suggestions,
                crop_type=insight.crop_type,
                region=insight.region,
                season=insight.season,
                created_at=insight.created_at.isoformat()
            )
            for insight in insights
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve insights: {str(e)}")

@router.get("/automatic-insights", response_model=List[AutomaticInsightModel])
async def get_automatic_insights(
    crop_type: str = "rice",
    region: str = "malang regency",
    season: str = "wet-season",
    limit: int = 3,
    use_case: AutomaticInsightsUseCase = Depends(get_automatic_insights_use_case)
):
    """Generate automatic insights based on current data conditions"""
    try:
        insights = await use_case.generate_insights(crop_type, region, season, limit)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.get("/history")
async def get_chat_history():
    """Get chat history (placeholder for future implementation)"""
    # This would return chat history from database
    return {"history": []}