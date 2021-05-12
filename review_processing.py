

from models import Product, Review, User
import re
import json
import gzip
from typing import Dict, Generator, List, Set
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import string
import random


def process_words(reviewText: str, english_stop_words: Set[str]) -> Generator[str, None, None]:
    punctuation_regex = re.compile("[^a-zA-Z0-9]")
    num_regex = re.compile("-?\d+.?\d*")

    stemmer = PorterStemmer()
    for word in word_tokenize(reviewText):
        lower_word = word.lower()
        if lower_word not in english_stop_words:
            stemmed_word = stemmer.stem(lower_word)
            if not punctuation_regex.match(stemmed_word) and not num_regex.match(stemmed_word):
                yield stemmed_word


def parse_products() -> List[Product]:
    products: List[Product] = []
    with gzip.open("meta_Cell_Phones_and_Accessories.json.gz", "rb") as raw_file:
        for line in raw_file:

            raw_object = json.loads(line)

            products.append(Product.parse_obj(raw_object))
    return products


def parse_reviews() -> Generator[Review, None, None]:
    with gzip.open("Cell_Phones_and_Accessories.json.gz", "rb") as raw_file:
        for line in raw_file:
            raw_object = json.loads(line)
            yield Review.parse_obj(raw_object)


def prep_data(english_stop_words: Set[str]):
    # deterministic??
    random.seed(42)
    products = parse_products()

    # will only look at a sample of 500 products
    selected_products_sample = random.sample(products, 1_000)
    selected_products = {
        product.asin: product for product in selected_products_sample}
    users_dict: Dict[str, User] = {}
    reviews: List[Review] = []
    # build user profiles and reviews
    for review in parse_reviews():
        if review.asin in selected_products:
            selected_products[review.asin].reviews.append(review)
            reviews.append(review)
            if review.reviewerID not in users_dict:
                users_dict[review.reviewerID] = User(
                    reviewerID=review.reviewerID)
            users_dict[review.reviewerID].reviews.append(review)

    # build the word_rank for each user profile
    for user in users_dict.values():
        for review in user.reviews:
            for word in process_words(review.reviewText, english_stop_words):
                if word not in user.word_rank:
                    user.word_rank[word] = 0
                user.word_rank[word] += 1
    # now we write out the data
    with open("user_data.jsonl", "w") as user_file:
        for user in users_dict.values():
            json_string = user.json()
            user_file.write(json_string)
            user_file.write("\n")
    with open("review_data.jsonl", "w") as review_file:
        for review in reviews:
            json_string = review.json()
            review_file.write(json_string)
            review_file.write("\n")
    with open("product_data.jsonl", "w") as product_file:
        for product in selected_products:
            json_string = product.json()
            product_file.write(json_string)
            product_file.write("\n")
