from os import path


from models import Product, Review, User
import re
import json
from typing import Dict, Generator, List, Set
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


def process_words(reviewText: str, english_stop_words: Set[str]) -> Generator[str, None, None]:
    punctuation_regex = re.compile("[^a-zA-Z0-9]")
    num_regex = re.compile("-?[0-9][0-9,.]+")

    stemmer = PorterStemmer()
    for word in word_tokenize(reviewText):
        lower_word = word.lower()
        if lower_word not in english_stop_words:
            stemmed_word = stemmer.stem(lower_word)
            if not punctuation_regex.match(stemmed_word) and not num_regex.match(stemmed_word):
                yield stemmed_word


def prep_data(english_stop_words: Set[str], data_in_path: str = "data/in/Cell_Phones_and_Accessories_5.json", data_out_path: str = "data/out"):
    products: Dict[str, Product] = {}
    # parse json and load in all the products
    with open(data_in_path, "r") as raw_file:
        for line in raw_file:
            try:

                raw_object = json.loads(line)
                review = Review.parse_obj(raw_object)
                if review.asin not in products:
                    products[review.asin] = Product(
                        asin=review.asin, product_link=f"https://www.amazon.com/dp/{review.asin}", reviews=[])
                products[review.asin].reviews.append(review)
            except TypeError as e:

                continue
            except Exception as e:

                continue
    # will only look at a sample of 500 products
    selected_products = list(products.values())[:500]
    users_dict: Dict[str, User] = {}
    reviews: List[Review] = []
    # build user profiles and reviews
    for product in selected_products:
        for review in product.reviews:
            if review.reviewerID not in users_dict:
                users_dict[review.reviewerID] = User(
                    reviewerID=review.reviewerID, reviews=[], word_rank={})
            users_dict[review.reviewerID].reviews.append(review)
            reviews.append(review)
    # build the word_rank for each user profile
    for user in users_dict.values():
        for review in user.reviews:
            for word in process_words(review.reviewText, english_stop_words):
                if word not in user.word_rank:
                    user.word_rank[word] = 0
                user.word_rank[word] += 1
    # now we write out the data
    with open(path.join(data_out_path, "user_data.jsonl"), "w") as user_file:
        for user in users_dict.values():
            json_string = user.json()
            user_file.write(json_string)
            user_file.write("\n")
    with open(path.join(data_out_path, "review_data.jsonl"), "w") as review_file:
        for review in reviews:
            json_string = review.json()
            review_file.write(json_string)
            review_file.write("\n")
    with open(path.join(data_out_path, "product_data.jsonl"), "w") as product_file:
        for product in selected_products:
            json_string = product.json()
            product_file.write(json_string)
            product_file.write("\n")
