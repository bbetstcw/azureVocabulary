import nltk

lemmatizer = nltk.WordNetLemmatizer()
grammar = r"""
    NBAR:
        {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
        
    NP:
        {<NBAR>}
        {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
"""
chunker = nltk.RegexpParser(grammar)
stopwords = nltk.corpus.stopwords.words('english')

def run(text):
    toks = nltk.word_tokenize(text)
    postoks = nltk.tag.pos_tag(toks)
    tree = chunker.parse(postoks)
    terms = get_terms(tree)
    result = {}
    for term in terms:
        keyword = " ".join(term)
        try:
            result[keyword] += 1
        except KeyError:
            result[keyword] = 1
    return result

def leaves(tree):
    """Finds NP (nounphrase) leaf nodes of a chunk tree."""
    for subtree in tree.subtrees(filter = lambda t: t.label()=='NP'):
        yield subtree.leaves()

myException = ["media"]

def normalise(word):
    """Normalises words to lowercase and stems and lemmatizes it."""
    word = word.lower()
    if word not in myException:
        word = lemmatizer.lemmatize(word)
    word = myLemmatize(word)
    return word

myLem = {"apps":"app", "runbooks":"runbook"}

def myLemmatize(word):
    try:
        return myLem[word]
    except KeyError:
        return word

def acceptable_word(word):
    """Checks conditions for acceptable word: length, stopword."""
    accepted = bool(2 <= len(word) <= 40
        and word.lower() not in stopwords)
    return accepted


def get_terms(tree):
    for leaf in leaves(tree):
        term = [ normalise(w) for w,t in leaf if acceptable_word(w) ]
        yield term
