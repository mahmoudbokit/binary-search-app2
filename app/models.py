from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class HealthStatus(str, Enum):
    """Status values for health check"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"

class SearchRequest(BaseModel):
    """Request model for search endpoint"""
    value: int = Field(
        ...,
        ge=1,
        le=1000,
        description="Value to search in the array (1-1000)",
        example=42
    )

class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    found: bool = Field(
        ...,
        description="Whether the value was found in the array"
    )
    index: int = Field(
        ...,
        ge=-1,
        description="Index of the value in array, -1 if not found"
    )
    value: int = Field(
        ...,
        description="The value that was searched for"
    )
    array_size: int = Field(
        ...,
        ge=0,
        description="Size of the array"
    )
    array_min: Optional[int] = Field(
        None,
        description="Minimum value in the array"
    )
    array_max: Optional[int] = Field(
        None,
        description="Maximum value in the array"
    )
    search_time_ms: Optional[float] = Field(
        None,
        description="Time taken for search in milliseconds"
    )

    class Config:
        schema_extra = {
            "example": {
                "found": True,
                "index": 25,
                "value": 42,
                "array_size": 100,
                "array_min": 1,
                "array_max": 1000,
                "search_time_ms": 0.5
            }
        }

class ArrayResponse(BaseModel):
    """Response model for array endpoint"""
    array: List[int] = Field(
        ...,
        description="The sorted array of numbers"
    )
    size: int = Field(
        ...,
        ge=0,
        description="Size of the array"
    )
    min_value: Optional[int] = Field(
        None,
        description="Minimum value in the array"
    )
    max_value: Optional[int] = Field(
        None,
        description="Maximum value in the array"
    )
    is_sorted: Optional[bool] = Field(
        None,
        description="Whether the array is sorted"
    )
    source: Optional[str] = Field(
        None,
        description="Source of the array (redis or generated)"
    )

    class Config:
        schema_extra = {
            "example": {
                "array": [1, 2, 3, 4, 5],
                "size": 5,
                "min_value": 1,
                "max_value": 5,
                "is_sorted": True,
                "source": "redis"
            }
        }

class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: HealthStatus = Field(
        ...,
        description="Overall health status"
    )
    redis_connected: bool = Field(
        ...,
        description="Redis connection status"
    )
    service: str = Field(
        default="binary-search-api",
        description="Service name"
    )
    version: str = Field(
        default="1.0.0",
        description="API version"
    )
    uptime_seconds: Optional[float] = Field(
        None,
        description="Service uptime in seconds"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "redis_connected": True,
                "service": "binary-search-api",
                "version": "1.0.0",
                "uptime_seconds": 3600.5
            }
        }

class ErrorResponse(BaseModel):
    """Response model for errors"""
    detail: str = Field(
        ...,
        description="Error description"
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code for debugging"
    )
    timestamp: Optional[str] = Field(
        None,
        description="Timestamp when error occurred"
    )

    class Config:
        schema_extra = {
            "example": {
                "detail": "Value must be between 1 and 1000",
                "error_code": "VALIDATION_ERROR",
                "timestamp": "2023-12-01T10:30:00Z"
            }
        }

class StatsResponse(BaseModel):
    """Response model for statistics endpoint"""
    total_searches: int = Field(
        ...,
        ge=0,
        description="Total number of searches performed"
    )
    successful_searches: int = Field(
        ...,
        ge=0,
        description="Number of successful searches (value found)"
    )
    failed_searches: int = Field(
        ...,
        ge=0,
        description="Number of failed searches (value not found)"
    )
    average_search_time_ms: Optional[float] = Field(
        None,
        description="Average search time in milliseconds"
    )
    most_searched_value: Optional[int] = Field(
        None,
        description="Most frequently searched value"
    )
    searches_today: Optional[int] = Field(
        None,
        description="Number of searches performed today"
    )

    class Config:
        schema_extra = {
            "example": {
                "total_searches": 150,
                "successful_searches": 75,
                "failed_searches": 75,
                "average_search_time_ms": 0.8,
                "most_searched_value": 42,
                "searches_today": 10
            }
        }

class ResetRequest(BaseModel):
    """Request model for reset endpoint"""
    new_size: Optional[int] = Field(
        None,
        ge=10,
        le=1000,
        description="New size for the array (10-1000)"
    )
    min_value: Optional[int] = Field(
        None,
        ge=0,
        le=10000,
        description="Minimum value for array generation"
    )
    max_value: Optional[int] = Field(
        None,
        ge=1,
        le=10000,
        description="Maximum value for array generation"
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducible array generation"
    )

    class Config:
        schema_extra = {
            "example": {
                "new_size": 200,
                "min_value": 0,
                "max_value": 5000,
                "seed": 12345
            }
        }