
import re
from typing import Dict, Generator, List, Set

import aiohttp
import nltk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from pydantic import BaseModel

nltk.download("punkt")
nltk.download("stopwords")
english_stop_words: Set = set(stopwords.words("english"))
app = FastAPI()

origins = [

    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Review(BaseModel):
    reviewerID: str
    asin: str
    reviewText: str


class TokenizedReview(BaseModel):
    frequencyMap: Dict[str, int]
    reviewerID: str
    asin = str
    reviewText: str


def process_words(reviewText: str) -> Generator[str, None, None]:
    punctuation_regex = re.compile("[^a-zA-Z0-9]")
    num_regex = re.compile("-?[0-9][0-9,.]+")

    stemmer = PorterStemmer()
    for word in word_tokenize(reviewText):
        lower_word = word.lower()
        if lower_word not in english_stop_words:
            stemmed_word = stemmer.stem(lower_word)
            if not punctuation_regex.match(stemmed_word) and not num_regex.match(stemmed_word):
                yield stemmed_word


@app.get("/solr")
async def fetch_solr(q: str = "", fq: str = ""):
    async with aiohttp.ClientSession() as session:
        solr_url = "http://localhost:8983/solr/reviews/select"
        async with session.get(solr_url, params={"fq": fq, "q": q}) as resp:
            resp_json = await resp.json()
            return resp_json


@app.post("/", response_model=TokenizedReview)
async def tokenize(review: Review) -> TokenizedReview:
    freq_table = {}
    for processed_word in process_words(review.reviewText):
        if processed_word not in freq_table:
            freq_table[processed_word] = 0
        freq_table[processed_word] += 1
    return TokenizedReview(reviewerID=review.reviewerID, reviewText=review.reviewText, asin=review.asin, frequencyMap=freq_table)
