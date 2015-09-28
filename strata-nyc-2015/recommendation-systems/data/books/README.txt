This data is a cleaned version of the BX-Books dataset example.  The
cleaning mostly consists of:

- Aggregating variations of authors into a single author's name
  (E.g. "J.R.R. Tolkien" vs. "J. R. R. Tolkien").

- Aggregating variations of books; e.g. "Blah" vs. "Blah : A Novel" vs. "Blah: A Novel"

Options for regenerating the dataset are given at the top of the
make_book_dataset.py script.

The rating is listed by name and book title.  All the original user
ids and book ids are switched to names and ids; this makes demoing
with this code much easier.  

All the names are unique and chosen so that popular names match to
users with a lot of ratings.

Schema:

book-ratings.csv: (name, book, rating)
book-ratings-implicit.csv: (name, book)  -- all ratings >= 4 above. 
user-data.csv: name, age, city, state, country. 
book-data.csv: book, author, year, publisher. 

Notes:  

A large number of users only have one or two ratings. This tends to
make MF and other methods do weird things. 

