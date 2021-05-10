
import re
from typing import Any, Generator, Set

import aiohttp

from aiohttp.web import HTTPException
import nltk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from starlette.requests import Request
from starlette.responses import Response
from models import Review, TokenizedReview

english_stop_words: Set = set()
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


@app.on_event("startup")
async def startup_event():
    nltk.download("punkt")
    nltk.download("stopwords")
    english_stop_words.union(set(stopwords.words("english")))
    async with aiohttp.ClientSession(trust_env=True) as session:

        schema_url = "http://solr:8983/solr/reviews/schema"

        while True:
            try:

                await session.post(schema_url,  json={
                    "add-field": {"name": "reviewText", "type": "text_general", "stored": "true"}})
                await session.post(schema_url,  json={
                    "add-field": {"name": "asin", "type": "string", "stored": "true"}})
                await session.post(schema_url,  json={
                    "add-field": {"name": "reviewID", "type": "string", "stored": "true"}})
            except HTTPException:
                continue
            finally:

                break
        print("startup complete")


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


@app.get("/solr/{rest_of_path:path}")
async def fetch_solr(rest_of_path: str, request: Request, response: Response):
    async with aiohttp.ClientSession() as session:

        solr_url = f"http://solr:8983/solr/{rest_of_path}"
        proxy = await session.get(solr_url, params=request.query_params)
        response.body = await proxy.read()
        response.status_code = proxy.status

        response.media_type = proxy.content_type
        response.charset = proxy.charset
        response.headers.update(proxy.headers)
        return response


@app.post("/solr/{rest_of_path:path}")
async def post_solr(rest_of_path: str, data: Any, request: Request, response: Response):
    async with aiohttp.ClientSession() as session:
        solr_url = f"http://solr:8983/solr/{rest_of_path}"
        proxy = await session.post(solr_url, json=data, params=request.query_params)
        response.body = await proxy.read()
        response.status_code = proxy.status
        response.charset = proxy.charset
        response.headers.update(proxy.headers)
        return response


@app.post("/", response_model=TokenizedReview)
async def tokenize(review: Review) -> TokenizedReview:
    freq_table = {}
    for processed_word in process_words(review.reviewText):
        if processed_word not in freq_table:
            freq_table[processed_word] = 0
        freq_table[processed_word] += 1
    return TokenizedReview(reviewerID=review.reviewerID, reviewText=review.reviewText, asin=review.asin, frequencyMap=freq_table)
