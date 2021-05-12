

import os
from os import path

from typing import Set

import aiohttp
import dotenv
import nltk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nltk.corpus import stopwords
from starlette.requests import Request
from starlette.responses import FileResponse, Response

from models import Review, TokenizedReview
from review_processing import process_words, prep_data

# load env variables
dotenv.load_dotenv()
SOLR_URL = os.getenv('SOLR_URL', "http://localhost:8983")
# for stop words later
english_stop_words: Set = set()
app = FastAPI()
# cors list
origins = [

    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://review-ranker.netlify.app",
    "https://review-ranker.netlify.app"
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
    # download data nltk
    nltk.download("punkt")
    nltk.download("stopwords")
    english_stop_words.union(set(stopwords.words("english")))
    prep_data(english_stop_words)
    async with aiohttp.ClientSession(trust_env=True) as session:
        # setup solr schema
        schema_url = f"{SOLR_URL}/solr/reviews/schema"

        await session.post(schema_url,  json={
            "add-field": {"name": "reviewText", "type": "text_general", "stored": "true"}})
        await session.post(schema_url,  json={
            "add-field": {"name": "asin", "type": "string", "stored": "true"}})
        await session.post(schema_url,  json={
            "add-field": {"name": "reviewerID", "type": "string", "stored": "true"}})

        with open("review_data.jsonl", "r") as g:
            await session.post(f"{SOLR_URL}/solr/reviews/update/json/docs", data=g)

            await session.post(f"{SOLR_URL}/solr/reviews/update", json={"commit": {}})


@app.get("/solr/{rest_of_path:path}")
async def fetch_solr(rest_of_path: str, request: Request, response: Response):
    async with aiohttp.ClientSession() as session:

        solr_url = f"{SOLR_URL}/solr/{rest_of_path}"
        proxy = await session.get(solr_url, params=request.query_params)
        response.body = await proxy.read()
        response.status_code = proxy.status

        response.media_type = proxy.content_type
        response.charset = proxy.charset
        response.headers.update(proxy.headers)
        return response


@app.post("/solr/{rest_of_path:path}")
async def post_solr(rest_of_path: str, request: Request, response: Response):

    async with aiohttp.ClientSession() as session:
        solr_url = f"{SOLR_URL}/solr/{rest_of_path}"
        proxy = await session.post(solr_url, json=await request.json(),  params=request.query_params)
        response.body = await proxy.read()
        response.status_code = proxy.status
        response.charset = proxy.charset
        response.headers.update(proxy.headers)
        return response


@app.post("/tokenize", response_model=TokenizedReview)
async def tokenize(review: Review) -> TokenizedReview:
    freq_table = {}
    for processed_word in process_words(review.reviewText, english_stop_words):
        if processed_word not in freq_table:
            freq_table[processed_word] = 0
        freq_table[processed_word] += 1
    return TokenizedReview(reviewerID=review.reviewerID, reviewText=review.reviewText, asin=review.asin, frequencyMap=freq_table)


@app.get("/product_data")
async def get_product_data():
    return FileResponse("product_data.jsonl")


@app.get("/user_data")
async def get_user_data():
    return FileResponse("user_data.jsonl")


@app.get("/review_data")
async def get_review_data():
    return FileResponse("review_data.jsonl")
