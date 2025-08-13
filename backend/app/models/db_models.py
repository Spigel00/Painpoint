from sqlalchemy import Column, Integer, String, Text, BigInteger, UniqueConstraint, DateTime, Float, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100))
    github_username = Column(String(50))
    linkedin_profile = Column(String(200))
    skills = Column(JSON)  # List of technical skills
    bio = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    claimed_problems = relationship("ProblemClaim", back_populates="user")
    solutions = relationship("Solution", back_populates="contributor")

class ProblemCluster(Base):
    __tablename__ = "problem_clusters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category_type = Column(String(50))  # Software Needs, Hardware Needs, Tech Support, etc.
    cluster_centroid = Column(JSON)  # Embedding centroid for clustering
    keywords = Column(JSON)  # Top keywords for this cluster
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    problems = relationship("FetchedProblem", back_populates="cluster")

class ProblemClaim(Base):
    __tablename__ = "problem_claims"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("fetched_problems.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="claimed")  # claimed, in_progress, completed, abandoned
    github_repo = Column(String(200))
    project_url = Column(String(200))
    notes = Column(Text)
    claimed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="claimed_problems")
    problem = relationship("FetchedProblem", back_populates="claims")

class Solution(Base):
    __tablename__ = "solutions"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("fetched_problems.id"), nullable=False)
    contributor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    github_repo = Column(String(200))
    demo_url = Column(String(200))
    tech_stack = Column(JSON)  # List of technologies used
    implementation_notes = Column(Text)
    status = Column(String(20), default="in_development")  # in_development, completed, published
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contributor = relationship("User", back_populates="solutions")
    problem = relationship("FetchedProblem", back_populates="solutions")

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100))
    embedding = Column(Text)  # store as JSON string if needed


class ProblemSummary(Base):
    __tablename__ = "problem_summaries"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, nullable=False, index=True)
    problem_statement = Column(String(500), nullable=False)
    detected_issues = Column(JSON)  # List of detected issues
    affected_components = Column(JSON)  # List of affected components
    symptoms = Column(JSON)  # List of symptoms
    severity = Column(String(20))  # low, medium, high
    category_confidence = Column(JSON)  # Confidence scores for categories
    ai_enhanced = Column(String(10), default="false")
    refined_statement = Column(String(500))
    root_cause_hypothesis = Column(Text)
    ai_urgency = Column(String(20))
    solution_category = Column(String(100))
    generated_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class FetchedProblem(Base):
    __tablename__ = "fetched_problems"
    __table_args__ = (
    UniqueConstraint("url", name="uq_fetched_problem_url"),
    UniqueConstraint("reddit_id", name="uq_fetched_problem_reddit_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    subreddit = Column(String(120), nullable=False)
    category = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)
    reddit_id = Column(String(30), nullable=False)
    created_utc = Column(BigInteger, nullable=False)
    
    # Enhanced fields for clustering and AI processing
    source_platform = Column(String(20), default="reddit")  # reddit, twitter, x
    embedding_vector = Column(JSON)  # MiniLM-L6-v2 embedding
    cluster_id = Column(Integer, ForeignKey("problem_clusters.id"), nullable=True)
    ai_problem_statement = Column(Text)  # Generated by MiniLM-L6-v2
    confidence_score = Column(Float, default=0.0)  # AI confidence in categorization
    is_claimed = Column(Boolean, default=False)
    claim_count = Column(Integer, default=0)
    solution_count = Column(Integer, default=0)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cluster = relationship("ProblemCluster", back_populates="problems")
    claims = relationship("ProblemClaim", back_populates="problem")
    solutions = relationship("Solution", back_populates="problem")
