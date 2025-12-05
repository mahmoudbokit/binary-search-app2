import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
from app.database import RedisDatabase
from app.services import BinarySearchService
from app.models import (
    SearchRequest,
    SearchResponse,
    ArrayResponse,
    HealthResponse,
    HealthStatus,
    ErrorResponse,
    StatsResponse,
    ResetRequest
)

app = FastAPI(
    title="Binary Search API",
    version="1.0.0",
    description="REST API for binary search operations with Redis persistence",
    contact={
        "name": "API Support",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
redis_db = RedisDatabase(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379))
)
search_service = BinarySearchService(redis_db)

# Track startup time
startup_time = time.time()

@app.on_event("startup")
async def startup_event():
    """Initialize array on startup"""
    await search_service.initialize_array()
    print(f"API started at {datetime.now()}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await redis_db.disconnect()
    print(f"API shutting down at {datetime.now()}")

@app.get("/health", 
         response_model=HealthResponse,
         summary="Health check",
         description="Check the health status of the API and Redis connection",
         responses={
             200: {"description": "Service is healthy"},
             503: {"description": "Service is unhealthy", "model": ErrorResponse}
         })
async def health_check():
    """Health check endpoint"""
    try:
        redis_status = await redis_db.is_connected()
        current_status = HealthStatus.HEALTHY if redis_status else HealthStatus.UNHEALTHY
        
        response = HealthResponse(
            status=current_status,
            redis_connected=redis_status,
            uptime_seconds=time.time() - startup_time
        )
        
        if current_status == HealthStatus.UNHEALTHY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection failed"
            )
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@app.post("/search", 
          response_model=SearchResponse,
          summary="Search value in array",
          description="Perform binary search for a value in the sorted array",
          responses={
              200: {"description": "Search completed successfully"},
              400: {"description": "Invalid input value", "model": ErrorResponse},
              500: {"description": "Internal server error", "model": ErrorResponse}
          })
async def search_value(request: SearchRequest):
    """Search for a value in the array"""
    try:
        start_time = time.time()
        result = await search_service.search(request.value)
        search_time = (time.time() - start_time) * 1000  # Convert to ms
        
        response = SearchResponse(
            found=result["found"],
            index=result["index"],
            value=request.value,
            array_size=result["array_size"],
            array_min=result.get("array_min"),
            array_max=result.get("array_max"),
            search_time_ms=search_time
        )
        
        # Track statistics (in a real app, you'd save this to Redis)
        search_service.track_search(request.value, result["found"], search_time)
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@app.get("/array", 
         response_model=ArrayResponse,
         summary="Get current array",
         description="Retrieve the current sorted array stored in Redis",
         responses={
             200: {"description": "Array retrieved successfully"},
             500: {"description": "Failed to retrieve array", "model": ErrorResponse}
         })
async def get_array():
    """Get the current array"""
    try:
        array = await search_service.get_array()
        source = await search_service.get_array_source()
        
        return ArrayResponse(
            array=array,
            size=len(array),
            min_value=min(array) if array else None,
            max_value=max(array) if array else None,
            is_sorted=all(array[i] <= array[i+1] for i in range(len(array)-1)) if array else None,
            source=source
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get array: {str(e)}"
        )

@app.post("/reset",
          summary="Reset array",
          description="Generate a new array with custom parameters",
          responses={
              200: {"description": "Array reset successfully"},
              400: {"description": "Invalid parameters", "model": ErrorResponse},
              500: {"description": "Failed to reset array", "model": ErrorResponse}
          })
async def reset_array(request: ResetRequest = None):
    """Reset the array with new parameters"""
    try:
        if request:
            await search_service.reset_array(
                size=request.new_size,
                min_value=request.min_value,
                max_value=request.max_value,
                seed=request.seed
            )
        else:
            await search_service.reset_array()
        
        return {"message": "Array reset successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset array: {str(e)}"
        )

@app.get("/stats",
         response_model=StatsResponse,
         summary="Get search statistics",
         description="Retrieve statistics about searches performed",
         responses={
             200: {"description": "Statistics retrieved successfully"},
             500: {"description": "Failed to get statistics", "model": ErrorResponse}
         })
async def get_statistics():
    """Get search statistics"""
    try:
        stats = search_service.get_statistics()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)