from pydantic import BaseModel
from typing import Dict, List, Optional, Union

from pydantic.fields import Field


class Review(BaseModel):
    reviewerID: str
    asin: str
    reviewText: str = ""
    reviewerName: Optional[str]
    vote: Optional[Union[str, int]]
    style: Optional[Union[Dict[str, str], str]]
    overall: Optional[Union[str, float]]
    summary: Optional[str]
    unixReviewTime: Optional[int]
    reviewTime: Optional[str]
    image: Optional[Union[str, List[str]]]


class TokenizedReview(Review):
    frequencyMap: Dict[str, int]


class User(BaseModel):
    reviewerID: str
    reviews: List[Review] = Field(default_factory=list)
    word_rank: Dict[str, float] = Field(default_factory=dict)


class Product(BaseModel):
    asin: str
    title: Optional[str]
    feature: Optional[List[str]]
    description: Optional[Union[str, List[str]]]
    price: Union[str, float]
    image: Optional[List[str]]
    salesRank: Optional[Dict[str, int]]
    brand: Optional[str]
    categories: Optional[Union[List[str], str]]
    reviews: List[Review] = Field(default_factory=list)
