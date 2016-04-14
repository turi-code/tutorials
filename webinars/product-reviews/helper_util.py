import graphlab as gl
from graphlab.toolkits.text_analytics import trim_rare_words, split_by_sentence, extract_part_of_speech, stopwords, PartOfSpeech
from ipywidgets import widgets
from IPython.display import display, HTML, clear_output

def search(reviews, query='monitor'):
    m = gl._internal.search.create(reviews[['name']].unique().dropna())
    monitors = m.query(query)['name']
    reviews = reviews.filter_by(monitors, 'name')
    return reviews

def get_comparisons(a, b, item_a, item_b, aspects):

    # Compute the number of sentences
    a2 = a.groupby('tag', {item_a: gl.aggregate.COUNT})
    b2 = b.groupby('tag', {item_b: gl.aggregate.COUNT})
    counts = a2.join(b2)

    # Compute the mean sentiment
    a2 = a.groupby('tag', {item_a: gl.aggregate.AVG('sentiment')})
    b2 = b.groupby('tag', {item_b: gl.aggregate.AVG('sentiment')})
    sentiment = a2.join(b2)

    # Get a list of adjectives
    a2 = a.select_columns(['tag', 'adjectives'])\
          .stack('adjectives', 'adjective')\
          .filter_by(aspects, 'adjective', exclude=True)\
          .groupby(['tag'], {item_a: gl.aggregate.CONCAT('adjective')})
    b2 = b.select_columns(['tag', 'adjectives'])\
          .stack('adjectives', 'adjective')\
          .filter_by(aspects, 'adjective', exclude=True)\
          .groupby(['tag'], {item_b: gl.aggregate.CONCAT('adjective')})
    adjectives = a2.join(b2)

    return counts, sentiment, adjectives

def get_dropdown(reviews):
    counts = reviews.groupby('name', gl.aggregate.COUNT).sort('Count', ascending=False)
    counts['display_name'] = counts.apply(lambda x: '{} ({})'.format(x['name'], x['Count']))
    counts = counts.head(500)

    from collections import OrderedDict
    items = OrderedDict(zip(counts['display_name'], counts['name']))
    item_dropdown = widgets.Dropdown()
    item_dropdown.options = items
    item_dropdown.value = items.values()[1]
    return item_dropdown

def get_extreme_sentences(tagged, k=100):

    def highlight(sentence, tags, color):
        for tag in tags:
            html_tag = '<span style="color:{0}">{1}</span>'.format(color, tag)
            sentence = sentence.replace(tag, html_tag)
        return sentence

    good = tagged.topk('sentiment', k=k, reverse=False)
    good['highlighted']  = good.apply(lambda x: highlight(x['sentence'], x['adjectives'], 'red'))
    good['highlighted']  = good.apply(lambda x: highlight(x['highlighted'], [x['tag']], 'green'))

    bad = tagged.topk('sentiment', k=k, reverse=True)
    bad['highlighted']  = bad.apply(lambda x: highlight(x['sentence'], x['adjectives'], 'red'))
    bad['highlighted']  = bad.apply(lambda x: highlight(x['highlighted'], [x['tag']], 'green'))

    return good, bad

def print_sentences(sentences):
    display(HTML('<p/>'.join(sentences)))


