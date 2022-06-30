from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from mainapp.helpers import genre_wise, tfidf_recommendations, get_book_dict, get_rated_bookids, combine_ids, get_top_n, popular_among_users, get_book_title
from mainapp.models import UserRating, SaveForLater
from django.contrib import messages
from django.core.paginator import Paginator
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
import os
import pandas as pd
import BookRecSystem.settings as settings
book_path_rating = os.path.join(settings.STATICFILES_DIRS[0] + '/mainapp/dataset/ratings.csv')

ratings_df = pd.read_csv(book_path_rating)


import random
import operator

train, test = train_test_split(ratings_df,test_size=0.2)

train = pd.DataFrame(train, columns= ratings_df.columns)
test = pd.DataFrame(test, columns= ratings_df.columns)

books_matrix = ratings_df.pivot_table(index='book_id',columns='user_id',values='rating').fillna(0)

movies_matrixT=books_matrix.T

model_knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
model_knn.fit(books_matrix)


@ensure_csrf_cookie
def index(request):
    books = popular_among_users()
    return render(request, 'mainapp/index.html', {'books': books})

@ensure_csrf_cookie
def aboutPage(request):
  
    return render(request, 'mainapp/about.html')

@ensure_csrf_cookie
def contactPage(request):

    return render(request, 'mainapp/contact.html')

@ensure_csrf_cookie
def genre_books(request, genre):

    genre_topbooks = genre_wise(genre)
    genre_topbooks = genre_topbooks.to_dict('records')
    context = {
        'genre': genre.capitalize(),
        'genre_topbook': genre_topbooks,
    }
    return render(request, 'mainapp/genre.html', context)


@ensure_csrf_cookie
def explore_books(request):

    N = 152
    sample = get_top_n().sample(N).to_dict('records')
    return render(request, 'mainapp/explore.html', {'book': sample})


@login_required
@ensure_csrf_cookie
def book_recommendations(request):
    user_ratings = list(UserRating.objects.filter(user=request.user).order_by('-bookrating'))
    random.shuffle(user_ratings)
    best_user_ratings = sorted(user_ratings, key=operator.attrgetter('bookrating'), reverse=True)

    if len(best_user_ratings) < 4:
        messages.info(request, 'Please rate atleast 5 books')
        return redirect('index')
    if best_user_ratings:
        bookid = best_user_ratings[0].bookid
        already_rated_books = set(get_rated_bookids(user_ratings))

        tfidf_bookids = set(tfidf_recommendations(bookid))

        recommended_list=[]
        book_name = get_book_title(bookid)
        try:
            distances, indices = model_knn.kneighbors(books_matrix[books_matrix.index==bookid].values.reshape(1, -1), n_neighbors=11)
            for i in range(0, len(distances.flatten())):
                recommended_list.append(books_matrix.index[indices.flatten()[i]])
        except:
            recommended_list=[]
        if book_name in recommended_list:
            recommended_list.remove(book_name)
        best_bookids = combine_ids(tfidf_bookids, already_rated_books, recommended_list)
        all_books_dict = get_book_dict(best_bookids)
    else:
        return redirect('index')
    return render(request, 'mainapp/recommendation.html', {'books': all_books_dict})


@login_required
@ensure_csrf_cookie
def read_books(request):

    user_ratings = list(UserRating.objects.filter(user=request.user).order_by('-bookrating'))
    if len(user_ratings) == 0:
        messages.info(request, 'Please rate some books')
        return redirect('index')
    if user_ratings:
        rated_books = set(get_rated_bookids(user_ratings))
        books = get_book_dict(rated_books)
        num = len(books)
        # Add pagination to the page showing 10 books
        paginator = Paginator(books, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        return redirect('index')
    return render(request, 'mainapp/read.html', {'page_obj': page_obj, 'num': num})


def handler404(request, *args, **argv):
    response = render(request, 'mainapp/error_handler.html')
    response.status_code = 404
    return response


def handler500(request, *args, **argv):
    response = render(request, 'mainapp/error_handler.html')
    response.status_code = 500
    return response


def SaveList(request):

    book = set(SaveForLater.objects.filter(user=request.user).values_list('bookid', flat=True))
    book_id = list(book)
    if len(book_id) == 0:
        messages.info(request, 'Please Add Some Books')
        return redirect('index')
    books = get_book_dict(book_id)
    total_books = len(books)
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'mainapp/saved_book.html', {'page_obj': page_obj, 'num': total_books})