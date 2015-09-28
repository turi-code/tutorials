book_rating_count_minimum = 2
user_rating_count_mimimum = 1  
impute_implicit = False
ignore_implicit = True 

# Install this manually from http://py-editdist.googlecode.com/files/py-editdist-0.3.tar.gz
import editdist

# pip install titlecase
import titlecase

import graphlab as gl
from collections import defaultdict
import re
import unicodedata
import sys
import graphlab as gl
import random

rating_data = gl.SFrame.read_csv("./raw_data/BX-Book-Ratings.csv", delimiter=";", column_type_hints={'Book-Rating' : int})
book_data = gl.SFrame.read_csv("./raw_data/BX-Books.csv", delimiter=";")
user_data = gl.SFrame.read_csv("./raw_data/BX-Users.csv", delimiter=";")

print "Cleaning; this takes a while."

################################################################################
# Clean and filter out bad book titles

book_filter = []

def clean_book(title):
    try: 
        n = unicodedata.normalize('NFKD', unicode(title.strip())).encode('ascii','ignore')
    except UnicodeDecodeError:
        return ''

    n = re.sub(r'\(.+\)', '', n).replace('&amp;', '&').strip()

    if n.upper() == n:
        n = titlecase.titlecase(n)

    n = re.sub(': A[\w\s]* Novel', '', n).strip()

    n = n.replace(' : ', ': ').replace(' : ', ': ').replace(' : ', ': ').strip()

    if n.count('"') == 1:
        n = n.replace('"', ' ').strip()

    if len(n) == 0:
        return n

    if n[0] == '"' and n[-1] == '"':
        n = n[1:-1].strip()

    if n.endswith(','):
        n = n[:-1].strip()

    n = re.sub(r'(\s*\.){3}', '...', n)

    # Now, a few specifc rules for some annoying cases that come up in the examples
    if n.startswith("J.R.R. Tolkien's"):
        n = titlecase.titlecase(n.replace("J.R.R. Tolkien's", "")).strip()
    
    book_filter.append(title)

    return n

book_list = sorted(set(clean_book(t) for t in set(book_data['Book-Title'])),
                   key = lambda k: k.lower())

def clean_list(L, sub_dict):

    i = 0
    while i + 1 < len(L):
        s1 = L[i]
        s2 = L[i + 1]

        if s1 == s2[:len(s1)]:

            suffix = s2[len(s1):]
            if suffix.strip().startswith(':'):
                sub_dict[L[i + 1].strip().lower()] = L[i]
                del L[i + 1]
                continue

            elif suffix.startswith(' '):
                sub_dict[L[i].strip().lower()] = L[i + 1]
                del L[i]
                continue

        d = editdist.distance(s1.lower(), s2.lower())
        
        if (s1.lower() == s2.lower() 
            or d <= 2
            or s1.lower().replace(' ', '') == s2.lower().replace(' ', '')):
            
            if len(s1) > len(s2):
                sub_dict[L[i + 1].strip().lower()] = L[i]
                del L[i + 1]
            else: 
                sub_dict[L[i].strip().lower()] = L[i + 1]
                del L[i]

            continue

        try:
            if re.match(s1.replace('.', '[A-Za-z]+'), s2) is not None:
                sub_dict[L[i].strip().lower()] = L[i + 1]
                del L[i]
                continue
        except:
            pass
            
        i += 1

known_book_substitutions = {}
clean_list(book_list, known_book_substitutions)
        
# open('all-books.txt', 'w').write('\n'.join(book_list))

book_data = book_data.filter_by(book_list, 'Book-Title')

################################################################################
# Clean and aggregate authors

author_filter = []

def clean_author(author):
    try: 
        a = unicodedata.normalize('NFKD', unicode(author.strip())).encode('ascii','ignore')
    except UnicodeDecodeError:
        return ''

    a = re.sub(r'\.\s*', '. ', a).replace('"', '').strip()

    a = re.sub(r'\(.+\)', '', a).replace('&amp;', '&').strip()
    
    a = titlecase.titlecase(a)

    if 'tolkien' in a.lower():
        a = 'J. R. R. Tolkien'

    a = a.replace(' ,', ',')

    a = re.sub(r'(^|\s)([A-Za-z])(?=\s|$)', r' \2. ', a).strip()

    a = re.sub(r'\s+', ' ', a).strip()
    
    author_filter.append(author)
    
    return a

author_list = sorted(set(clean_author(t) for t in set(book_data['Book-Author'])),
                     key = lambda k: k.lower())

known_author_substitutions = {}

clean_list(author_list, known_author_substitutions)

# Book data is being used as the master list of what we will keep
book_data = book_data.filter_by(author_list, 'Book-Author')

# open('all-authors.txt', 'w').write('\n'.join(author_list))

################################################################################
# Now we have to map all the books and authors to their best match.
# This can be tricky.

ref_authors = dict((n.strip().lower(), n.strip()) for n in author_list)
ref_books   = dict((n.strip().lower(), n.strip()) for n in book_list)

def get_from_ref_dict(L, v_in):

    assert False
    
    best_edit_dist = 1000000000000
    best_name = None
    
    for v_key, tv in L.iteritems():
        if v_key == v_in:
            return tv

        d = editdist.distance(v_in, v_key)

        min_l = min(len(v_in), len(v_key))
        
        if v_in[:min_l] == v_key[:min_l]:
            d = 0

        if d < best_edit_dist:
            best_edit_dist = d
            best_name = tv

        if d == 0:
            break

    print "%s >>>>>> %s" % (v_in, best_name)
    
    return best_name

author_map = ref_authors.copy()
author_map.update(known_author_substitutions)
book_map = ref_books.copy()
book_map.update(known_book_substitutions)

def get_author(a):
    try:
        return author_map[a.lower().strip()]
    except KeyError:
        pass

    clean_a = clean_author(a)
    
    try:
        return author_map[clean_a]
    except KeyError:
        pass
    
    ta = get_from_ref_dict(ref_authors, clean_a)
    author_map[a.lower().strip()] = ta
    author_map[clean_a] = ta
    return ta

def get_book(t):
    
    try:
        return book_map[t.lower().strip()]
    except KeyError:
        pass

    cleaned_t = clean_book(t)
        
    try:
        return book_map[cleaned_t]
    except KeyError:
        pass

    tb = get_from_ref_dict(ref_books, cleaned_t)
    book_map[t.lower().strip()] = tb
    book_map[cleaned_t] = tb
    
    return tb
    
new_authors = [None]*len(book_data)
new_books   = [None]*len(book_data)

for i, (author, book) in enumerate(zip(book_data['Book-Author'], book_data['Book-Title'])):
    if author is None:
        new_authors[i] = 'NONE'
    else:
        a = get_author(author)
        assert a is not None
        new_authors[i] = a

    if book is None:
        new_books[i] = ''
    else:
        b = get_book(book)
        assert b is not None
        new_books[i] = b

book_data['Book-Title'] = new_books
book_data['Book-Author'] = new_authors
        
book_data = book_data.filter_by(book_data['Book-Title'][book_data['Book-Title'] != ''], 'Book-Title')

################################################################################

rating_data = rating_data.join(book_data[['ISBN', 'Book-Title']])[['User-ID', 'Book-Title', 'Book-Rating']]

################################################################################
# Replace all the implicit ratings with reasonable, but slightly
# negative, other ratings.

if impute_implicit: 

    rating_data_nz = rating_data[rating_data['Book-Rating'] != 0]

    m_nz = gl.recommender.create(rating_data_nz, 'Book-Title', 'User-ID', 'Book-Rating', 
                                 regularization = 10, n_factors = 32)

    m_ot = gl.recommender.create(rating_data, 'Book-Title', 'User-ID', 'Book-Rating', 
                                 regularization = 10, n_factors = 32)

    alt_pred = 0.5 * (m_nz.score(rating_data) + m_ot.score(rating_data))

    new_pred = [None] * len(rating_data)

    for i, (true_y, alt_y) in enumerate(zip(rating_data['Book-Rating'], alt_pred)):
        new_pred[i] = true_y if true_y != 0 else alt_y

    rating_data['Book-Rating'] = new_pred
elif ignore_implicit: 
    rating_data = rating_data[rating_data['Book-Rating'] != 0]

################################################################################
# Eliminate books that don't have a diversity of ratings or who don't
# have more than book_rating_count_minimum ratings

rating_count_by_book = rating_data.groupby('Book-Title', {'count' : gl.aggregate.COUNT()})
rating_mean_by_book  = rating_data.groupby('Book-Title', {'mean' : gl.aggregate.MEAN('Book-Rating')})

okay_book = []

for book, count, mean in zip(rating_count_by_book['Book-Title'], 
                             rating_count_by_book['count'],
                             rating_mean_by_book['mean']):

    if count >= book_rating_count_minimum:
        okay_book.append(book)

book_data = book_data.filter_by(okay_book, 'Book-Title')

rating_data = rating_data.filter_by(book_data['Book-Title'], 'Book-Title')

################################################################################
# Eliminate users who haven't rated more than 3 books

rating_count_by_user = rating_data.groupby('User-ID', {'count' : gl.aggregate.COUNT()})

rating_count_by_user = rating_count_by_user[rating_count_by_user['count'] >= user_rating_count_mimimum]
user_data = user_data.filter_by(rating_count_by_user['User-ID'], 'User-ID')

################################################################################
# Put in fake names for all the users; makes demoing easier.  Make it
# so the common names refer to users with a lot of ratings. 

user_id_count_lookup = dict( zip(rating_count_by_user['User-ID'], rating_count_by_user['count']))

names = [n.strip() for n in open("./raw_data/name_list.txt").readlines()]

while len(names) < user_data.num_rows():
    names += names

# The names are sorted by how common they are
nl1 = ((idx, uid, user_id_count_lookup[uid]) for idx, uid in enumerate(user_data['User-ID']))
nl2 = zip(sorted(nl1, key = lambda k: -k[2]), names)
nl3 = sorted( (idx, uid, name) for (idx, uid, c), name in nl2)
names = [name for idx, uid, name in nl3] 
    
user_data['name'] = names[:len(user_data)]

################################################################################
# Final rating for the user; transform to 1-5 stars

def true_rating(r):
    r = int(r / 2)
    return max(1, min(r, 5))

rating_data['rating'] = rating_data['Book-Rating'].apply(true_rating)
                                                         
rating_data = rating_data.join(user_data, 'User-ID')
rating_data.rename({'Book-Title' : 'book'})

# Final cleaning for the user data 

def get_location_info(s, idx):
    try:
        return s.split(',')[idx].strip().lower()
    except IndexError:
        return ""

user_data['city'] = user_data['Location'].apply(lambda s: get_location_info(s, 0))
user_data['state'] = user_data['Location'].apply(lambda s: get_location_info(s, 1))
user_data['country'] = user_data['Location'].apply(lambda s: get_location_info(s, 2))

user_data.rename( {"Age" : "age"} )
user_data = user_data[["name", "age", "city", "state", "country"]]


rating_data = rating_data[["name", "book", "rating"]]
book_data.rename({'Book-Title' : 'book', 
                  'Book-Author' : 'author', 
                  'Year-Of-Publication' : 'year',
                  'Publisher' : 'publisher'
                  })
book_data = book_data[['book', 'author', 'year', 'publisher']]

rating_data_implicit = rating_data[rating_data["rating"] >= 4] [["name", "book"]]

rating_data.save('book-ratings.csv')
rating_data_implicit.save('book-ratings-implicit.csv')
user_data.save('user-data.csv')
book_data.save('book-data.csv')

# Now, we need to shuffle them.  If you don't shuffle them, the first
# ones in rating_data are bdsm books rated by Zola.

def shuffle_csv(filename):
    all_lines = open(filename).readlines()

    L = all_lines[1:]
    random.shuffle(L)
    all_lines[1:] = L

    open(filename, 'w').writelines(all_lines)


shuffle_csv('book-ratings.csv')
shuffle_csv('book-ratings-implicit.csv')
shuffle_csv('user-data.csv')
shuffle_csv('book-data.csv')

# And we are done!
