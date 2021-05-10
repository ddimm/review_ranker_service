from pydantic import BaseModel
from typing import Dict


class Review(BaseModel):
    reviewerID: str
    asin: str
    reviewText: str


class TokenizedReview(BaseModel):
    frequencyMap: Dict[str, int]
    reviewerID: str
    asin = str
    reviewText: str
