from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime


class ProblemCreate(BaseModel):
	title: str
	description: str
	category: Optional[str] = None


class ProblemRead(BaseModel):
	id: int
	title: str
	description: str
	category: Optional[str] = None

	class Config:
		from_attributes = True


class ProblemSummaryResponse(BaseModel):
	problem_id: int
	problem_statement: str
	detected_issues: List[str]
	affected_components: List[str]
	symptoms: List[str]
	severity: str
	category_confidence: Dict[str, float]
	ai_enhanced: bool = False
	generated_at: str


class RAGCollectionResult(BaseModel):
	status: str
	posts_collected: Optional[int] = 0
	errors: Optional[int] = 0
	timestamp: str
	message: Optional[str] = None
	error: Optional[str] = None


class RAGSummarizationResult(BaseModel):
	status: str
	summaries_created: Optional[int] = 0
	summaries_updated: Optional[int] = 0
	total_problems_processed: Optional[int] = 0
	timestamp: str
	error: Optional[str] = None


class RAGPipelineResponse(BaseModel):
	status: str
	timestamp: str
	reddit_collection: RAGCollectionResult
	x_collection: RAGCollectionResult
	summarization: RAGSummarizationResult
	message: str


class CollectionStatsResponse(BaseModel):
	total_problems: int
	recent_problems_7d: int
	category_distribution: Dict[str, int]
	last_updated: str
	rag_status: str
	error: Optional[str] = None


# Authentication Schemas
class UserCreate(BaseModel):
	username: str
	email: EmailStr
	password: str


class UserLogin(BaseModel):
	username: str
	password: str


class UserResponse(BaseModel):
	id: int
	username: str
	email: str
	created_at: datetime
	is_active: bool

	class Config:
		from_attributes = True


class Token(BaseModel):
	access_token: str
	token_type: str


# Solution Schemas
class SolutionCreate(BaseModel):
	github_repo: Optional[str] = None
	demo_url: Optional[str] = None
	description: Optional[str] = None


class SolutionUpdate(BaseModel):
	github_repo: Optional[str] = None
	demo_url: Optional[str] = None
	description: Optional[str] = None
	status: Optional[str] = None


class SolutionResponse(BaseModel):
	id: int
	problem_id: int
	solver_id: int
	solver_username: str
	github_repo: Optional[str] = None
	demo_url: Optional[str] = None
	description: Optional[str] = None
	status: str
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class ClaimProblemRequest(BaseModel):
	github_repo: Optional[str] = None
	description: Optional[str] = None


# Enhanced Problem Schema
class EnhancedProblemResponse(BaseModel):
	id: int
	title: str
	original_content: str
	processed_content: Optional[str] = None
	category: Optional[str] = None
	clustering_confidence: Optional[float] = None
	source: str
	url: Optional[str] = None
	author: Optional[str] = None
	upvotes: Optional[int] = 0
	created_at: datetime
	is_claimed: bool = False
	claimed_by: Optional[int] = None
	claimed_at: Optional[datetime] = None
	solutions: List[SolutionResponse] = []

	class Config:
		from_attributes = True
