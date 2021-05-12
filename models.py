from pydantic import BaseModel
from typing import Dict, List


class Review(BaseModel):
    reviewerID: str
    asin: str
    reviewText: str


class TokenizedReview(BaseModel):
    frequencyMap: Dict[str, int]
    reviewerID: str
    asin = str
    reviewText: str


class User(BaseModel):
    reviewerID: str
    reviews: List[Review] = None
    word_rank: Dict[str, float] = None


class Product(BaseModel):
    asin: str
    product_link: str = ""
    reviews: List[Review] = None
