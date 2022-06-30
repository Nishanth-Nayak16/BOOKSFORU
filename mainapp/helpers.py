import pandas as pd
import numpy as np
import os
import math
import pickle
import operator
import random
from collections import Counter
import BookRecSystem.settings as settings
import mainapp.models

book_path = os.path.join(settings.STATICFILES_DIRS[0] + '/mainapp/dataset/books.csv')

cosine_sim_path = os.path.join(settings.STATICFILES_DIRS[0] + '/mainapp/model_files/tf-idf/cosine_rating_sim.npz')
book_indices_path = os.path.join(settings.STATICFILES_DIRS[0] + '/mainapp/model_files/tf-idf/indices.pkl')

book_id_map_path = os.path.join(settings.STATICFILES_DIRS[0] + '/mainapp/model_files/surprise/book_raw_to_inner_id.pickle')
book_raw_map_path = os.path.join(settings.STATICFILES_DIRS[0] + '/mainapp/model_files/surprise/book_inner_id_to_raw.pickle')
book_embed_path = os.path.join(settings.STATICFILES_DIRS[0] + '/mainapp/model_files/surprise/book_embedding.npy')
sim_books_path = os.path.join(settings.STATICFILES_DIRS[0] + '/mainapp/model_files/surprise/sim_books.pickle')

with open(book_id_map_path, 'rb') as handle:
    book_raw_to_inner_id = pickle.load(handle)

with open(book_raw_map_path, 'rb') as handle:
    book_inner_id_to_raw = pickle.load(handle)
book_embedding = np.load(book_embed_path)

with open(sim_books_path, 'rb') as handle:
    sim_books_dict = pickle.load(handle)

cols = ['original_title', 'authors', 'average_rating', 'image_url', 'book_id']

df_book = pd.read_csv(book_path)
total_books = df_book.shape[0]


def is_rating_invalid(rating):
    if not rating or not rating.isdigit():
        return True
    if int(rating) > 5:
        return True
    return False


def is_bookid_invalid(bookid):
    if not bookid or not bookid.isdigit():
        return True
    elif sum(df_book['book_id'] == int(bookid)) == 0:
        # If bookid does not exist
        return True
    return False


def get_book_title(bookid):
    return df_book[df_book['book_id'] == bookid]['original_title'].values[0]


def get_book_ids(index_list):
    bookid_list = list(df_book.loc[index_list].book_id.values)
    return bookid_list


def get_rated_bookids(user_ratings):
    already_rated = []
    for rating in user_ratings:
        book_id = rating.bookid
        already_rated.append(book_id)
    return already_rated


def get_raw_id(book_id):
    raw_id = df_book[df_book.book_id == book_id]['r_index'].values[0]
    return raw_id


def get_bookid(raw_id_list):
    bookid_list = list(df_book[df_book.r_index.isin(raw_id_list)]['book_id'].values)
    return bookid_list


def genre_wise(genre, percentile=0.85):
    n_books = 16
    min_genre_book_count = 48

    qualified = df_book[df_book.genre.str.contains(genre.lower())]
    # Imdb Formula
    v = qualified['ratings_count']
    m = qualified['ratings_count'].quantile(percentile)
    R = qualified['average_rating']
    C = qualified['average_rating'].mean()
    W = (R*v + C*m) / (v + m)
    qualified = qualified.assign(weighted_rating=W)
    qualified.sort_values('weighted_rating', ascending=False, inplace=True)

    return qualified[cols].head(min_genre_book_count).sample(n_books)


def tfidf_recommendations(bookid):
    indices = pd.read_pickle(book_indices_path)
    cosine_sim = np.load(cosine_sim_path)['array1']
    book_title = get_book_title(bookid)
    book_title = book_title.replace(' ', '').lower()
    idx = indices[book_title]

    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:10]

    book_indices = [i[0] for i in sim_scores]
    bookid_list = get_book_ids(book_indices)
    return bookid_list



def get_book_dict(bookid_list):
    rec_books_dict = df_book[df_book['book_id'].isin(bookid_list)][cols].to_dict('records')
    return rec_books_dict


def combine_ids(tfidf_bookids, already_rated, knn_reco, recommendations=10):
    tfidf_bookids = list(tfidf_bookids.difference(knn_reco))
    top_5_tfidf = set(tfidf_bookids[:5])
    already_rated = already_rated.difference(knn_reco)
    already_rated = list(already_rated.difference(top_5_tfidf))
    top_5_tfidf = list(top_5_tfidf)
    top_5_tfidf.sort()
    top_5_rate = list(already_rated[:5])
    best_bookid = top_5_tfidf + knn_reco
    if(len(best_bookid) == 10):
        best_bookids = best_bookid[:10]
    else:
        best_bookids = top_5_tfidf + top_5_rate + knn_reco
        best_bookids = best_bookid[:10]

    if len(best_bookids) < recommendations:
        two_n = (recommendations - len(best_bookids))
        n1, n2 = math.ceil(two_n/2), math.floor(two_n/2)

        best_bookids_tfidf = tfidf_bookids[3: (3*2)+n1]
        best_bookids_tfidf = list(set(best_bookids_tfidf).difference(set(best_bookids)))[:n1]

        genre_recomm_bookids = most_common_genre_recommendations(best_bookids + best_bookids_tfidf, n2)

        best_bookids = best_bookids + best_bookids_tfidf + genre_recomm_bookids
    return best_bookids


def most_common_genre_recommendations(books, n):

    genre_frequency = []
    for book in books:
        genre_frequency.append(df_book[df_book['book_id'] == book]['genre'].values[0].split(", ")[0])

    most_common_genre = sorted(Counter(genre_frequency).most_common())[0][0]

    genre_recommendations = genre_wise(most_common_genre).book_id.to_list()[:2*n]

    genre_recommendations = list(set(genre_recommendations).difference(books))[:n]

    return genre_recommendations


def get_top_n(top_n=400):

    df_books_copy = df_book.copy()
    v = df_books_copy['ratings_count']
    m = df_books_copy['ratings_count'].quantile(0.95)
    R = df_books_copy['average_rating']
    C = df_books_copy['average_rating'].mean()
    W = (R*v + C*m) / (v + m)
    df_books_copy = df_books_copy.assign(weighted_rating=W)
    qualified = df_books_copy.sort_values('weighted_rating', ascending=False)[cols].head(top_n)
    return qualified.sample(top_n)


def popular_among_users(N=15):
    all_ratings = list(mainapp.models.UserRating.objects.all().order_by('-bookrating'))
    random.shuffle(all_ratings)
    best_user_ratings = sorted(all_ratings, key=operator.attrgetter('bookrating'), reverse=True)

    filtered_books = set()
    for i, rating in enumerate(best_user_ratings):
        if rating.bookrating >= 4:
            filtered_books.add((rating.bookid))
        elif rating.bookrating < 4 or len(filtered_books) == N:
            break

    remaining_books_nos = N - len(filtered_books)
    if remaining_books_nos >= 0:
        rem_books = get_top_n(2*N)['book_id'].tolist()
        filtered_books = list(filtered_books) + list((set(rem_books) - filtered_books))[:remaining_books_nos]

    return get_book_dict(filtered_books)