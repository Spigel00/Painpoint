from sqlalchemy.orm import Session
from ..models.schemas import ProblemCreate
from ..repositories.problem_repository import (
	create_problem,
	list_problems,
	get_problem,
	delete_problem,
)
from typing import List, Optional
from ..models.db_models import Problem
from .ai_service import classify_category_from_embedding, classify_category
from ..utils.embeddings import generate_embedding
import json


def create(db: Session, data: ProblemCreate) -> Problem:
	# Compute category using AI (ignore any client-provided category)
	text_for_ai = f"{data.title}\n\n{data.description}"
	# Generate embedding from title + description (Hugging Face model)
	emb_vec = generate_embedding(text_for_ai)
	# Prefer classifying from embedding to avoid double work
	ai_category = (
		classify_category_from_embedding(emb_vec) if emb_vec else classify_category(text_for_ai)
	)
	emb_json = json.dumps(emb_vec)

	# Overwrite category with AI-chosen label
	data.category = ai_category

	return create_problem(db, data, embedding=emb_json)


def list_all(db: Session, skip: int = 0, limit: int = 50) -> List[Problem]:
	return list_problems(db, skip, limit)


def get(db: Session, problem_id: int) -> Optional[Problem]:
	return get_problem(db, problem_id)


def delete(db: Session, problem_id: int) -> bool:
	return delete_problem(db, problem_id)
