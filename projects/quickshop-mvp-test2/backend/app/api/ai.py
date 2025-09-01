"""
AI API endpoints for intelligent categorization, prioritization, and analysis
Implements OpenAI integration with caching, rate limiting, and fallback mechanisms
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.services.ai_service import AIService, AIServiceError
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI"])

# Initialize AI service
ai_service = AIService()


# Request/Response Models
class CategorizeRequest(BaseModel):
    text: str = Field(..., description="Text to categorize")
    categories: List[str] = Field(..., description="Available categories")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class CategorizeResponse(BaseModel):
    category: str
    confidence: float
    reasoning: str
    fallback: bool = False
    processing_time: float


class PrioritizeRequest(BaseModel):
    tasks: List[Dict[str, Any]] = Field(..., description="Tasks to prioritize")
    criteria: Optional[List[str]] = Field(
        ["urgency", "importance", "effort", "dependencies"],
        description="Prioritization criteria"
    )
    max_results: Optional[int] = Field(None, description="Limit number of results")


class PrioritizeResponse(BaseModel):
    prioritized_tasks: List[Dict[str, Any]]
    rationale: str
    scoring_details: Optional[Dict[str, Any]]
    processing_time: float


class AnalyzeRequest(BaseModel):
    content: str = Field(..., description="Content to analyze")
    analysis_type: str = Field("comprehensive", description="Type of analysis")
    include_entities: bool = Field(True, description="Extract entities")
    include_sentiment: bool = Field(True, description="Analyze sentiment")


class AnalyzeResponse(BaseModel):
    summary: str
    entities: Optional[List[Dict[str, Any]]]
    sentiment: Optional[Dict[str, float]]
    key_points: List[str]
    metadata: Dict[str, Any]
    processing_time: float


class SuggestRequest(BaseModel):
    context: str = Field(..., description="Context for suggestions")
    suggestion_type: str = Field("product", description="Type of suggestions")
    count: int = Field(5, description="Number of suggestions")
    filters: Optional[Dict[str, Any]] = None


class GrammarCheckRequest(BaseModel):
    text: str = Field(..., description="Text to check")
    language: str = Field("en", description="Language code")
    style: Optional[str] = Field("business", description="Writing style")


class BatchProcessRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(..., description="Items to process")
    operation: str = Field(..., description="Operation to perform")
    parallel: bool = Field(True, description="Process in parallel")


# Endpoints
@router.post("/categorize", response_model=CategorizeResponse)
async def categorize_text(
    request: CategorizeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Categorize text into predefined categories using AI
    
    - Uses GPT-3.5-turbo for efficient categorization
    - Implements caching for repeated requests
    - Falls back to keyword matching if AI unavailable
    """
    try:
        start_time = datetime.now()
        
        result = await ai_service.categorize(
            text=request.text,
            categories=request.categories,
            context=request.context,
            user_id=current_user.id
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return CategorizeResponse(
            category=result["category"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            fallback=result.get("fallback", False),
            processing_time=processing_time
        )
        
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in categorize: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/prioritize", response_model=PrioritizeResponse)
async def prioritize_tasks(
    request: PrioritizeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze and prioritize tasks based on multiple criteria
    
    - Uses AI to understand task context and dependencies
    - Applies multi-criteria scoring
    - Returns detailed rationale for prioritization
    """
    try:
        start_time = datetime.now()
        
        result = await ai_service.prioritize(
            tasks=request.tasks,
            criteria=request.criteria,
            max_results=request.max_results,
            user_id=current_user.id
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return PrioritizeResponse(
            prioritized_tasks=result["tasks"],
            rationale=result["rationale"],
            scoring_details=result.get("scoring_details"),
            processing_time=processing_time
        )
        
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in prioritize: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform deep content analysis with entity extraction and sentiment
    
    - Comprehensive text analysis using GPT-4
    - Entity recognition and relationship mapping
    - Sentiment analysis with confidence scores
    """
    try:
        start_time = datetime.now()
        
        result = await ai_service.analyze(
            content=request.content,
            analysis_type=request.analysis_type,
            include_entities=request.include_entities,
            include_sentiment=request.include_sentiment,
            user_id=current_user.id
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AnalyzeResponse(
            summary=result["summary"],
            entities=result.get("entities"),
            sentiment=result.get("sentiment"),
            key_points=result["key_points"],
            metadata=result.get("metadata", {}),
            processing_time=processing_time
        )
        
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in analyze: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/suggest")
async def generate_suggestions(
    request: SuggestRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate intelligent suggestions based on context
    
    - Product recommendations
    - Content suggestions
    - Next best actions
    """
    try:
        result = await ai_service.suggest(
            context=request.context,
            suggestion_type=request.suggestion_type,
            count=request.count,
            filters=request.filters,
            user_id=current_user.id
        )
        
        return {
            "suggestions": result["suggestions"],
            "reasoning": result.get("reasoning"),
            "confidence": result.get("confidence", 0.8)
        }
        
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/grammar-check")
async def check_grammar(
    request: GrammarCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Check and correct grammar with style suggestions
    
    - Grammar and spelling corrections
    - Style improvements
    - Readability analysis
    """
    try:
        result = await ai_service.check_grammar(
            text=request.text,
            language=request.language,
            style=request.style,
            user_id=current_user.id
        )
        
        return {
            "corrected_text": result["corrected_text"],
            "corrections": result["corrections"],
            "style_suggestions": result.get("style_suggestions", []),
            "readability_score": result.get("readability_score")
        }
        
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/batch-process")
async def batch_process(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Process multiple items in batch with AI
    
    - Efficient batch processing
    - Progress tracking
    - Async execution for large batches
    """
    try:
        # For large batches, process in background
        if len(request.items) > 50:
            batch_id = await ai_service.create_batch_job(
                items=request.items,
                operation=request.operation,
                user_id=current_user.id
            )
            
            background_tasks.add_task(
                ai_service.process_batch_async,
                batch_id=batch_id,
                items=request.items,
                operation=request.operation
            )
            
            return {
                "batch_id": batch_id,
                "status": "processing",
                "message": "Batch processing started in background"
            }
        
        # Process small batches immediately
        results = await ai_service.batch_process(
            items=request.items,
            operation=request.operation,
            parallel=request.parallel,
            user_id=current_user.id
        )
        
        return {
            "results": results,
            "processed": len(results),
            "status": "completed"
        }
        
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/batch-status/{batch_id}")
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a batch processing job"""
    try:
        status = await ai_service.get_batch_status(batch_id, current_user.id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/usage-stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get AI usage statistics and costs
    
    - API call counts
    - Token usage
    - Cost breakdown
    - Cache hit rates
    """
    try:
        stats = await ai_service.get_usage_stats(current_user.id)
        return stats
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage stats")


@router.post("/feedback")
async def submit_feedback(
    operation: str,
    result_id: str,
    feedback: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Submit feedback on AI results for improvement"""
    try:
        await ai_service.record_feedback(
            operation=operation,
            result_id=result_id,
            feedback=feedback,
            user_id=current_user.id
        )
        return {"message": "Feedback recorded successfully"}
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/health")
async def health_check():
    """Check AI service health and availability"""
    try:
        health = await ai_service.health_check()
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }