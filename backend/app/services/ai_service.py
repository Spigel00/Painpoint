import re
from typing import List
import numpy as np
from ..utils.embeddings import generate_embedding

# Required categories
LABELS = ["Software", "Hardware", "Other"]
_label_embeddings: List[List[float]] | None = None


def _heuristic_classify(text: str) -> str:
	t = text.lower()
	scores = {l: 0 for l in LABELS}

	sw = [
		"bug",
		"software",
		"app",
		"application",
		"code",
		"deploy",
		"crash",
		"error",
		"feature",
		"update",
		"api",
		"database",
	]
	hw = [
		"device",
		"hardware",
		"battery",
		"screen",
		"keyboard",
		"printer",
		"server",
		"cpu",
		"gpu",
		"disk",
		"router",
		"sensor",
	]
	other = [
		"question",
		"how to",
		"anyone",
		"recommend",
		"idea",
		"need",
	]

	def count(words):
		return sum(len(re.findall(rf"\b{re.escape(w)}\b", t)) for w in words)

	scores["Software"] = count(sw)
	scores["Hardware"] = count(hw)
	scores["Other"] = count(other)

	label = max(scores.items(), key=lambda kv: kv[1])[0]
	if scores[label] == 0:
		return "Other"
	return label


def _ensure_label_embeddings() -> List[List[float]]:
	global _label_embeddings
	if _label_embeddings is None:
		# Provide short descriptors with labels for better separation
		phrases = [
			"software issue bug application code error",
			"hardware device printer battery screen",
			"general question need recommendation other",
		]
		_label_embeddings = [generate_embedding(p) for p in phrases]
	return _label_embeddings


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
	if a.size == 0 or b.size == 0:
		return -1.0
	na = np.linalg.norm(a)
	nb = np.linalg.norm(b)
	if na == 0 or nb == 0:
		return -1.0
	return float(np.dot(a, b) / (na * nb))


def classify_category_from_embedding(vec: List[float]) -> str:
	try:
		label_vecs = _ensure_label_embeddings()
		v = np.asarray(vec, dtype=np.float32)
		sims = [
			_cosine(v, np.asarray(lv, dtype=np.float32)) for lv in label_vecs
		]
		if sims and max(sims) > -0.5:
			return LABELS[int(np.argmax(sims))]
	except Exception:
		pass
	# Fallback when embeddings unavailable
	return "Other"


def classify_category(text: str) -> str:
	vec = generate_embedding(text)
	if vec:
		return classify_category_from_embedding(vec)
	# last resort
	return _heuristic_classify(text)
