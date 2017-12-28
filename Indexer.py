import io
import glob, os
from pprint import pprint
import sys
import Parser

# GLOBAL CONSTANTS 
DOC_TOKEN_COUNT = {}
INVERTED_INDEX = {}
STOP_WORDS = []
           

def unigram_index(stopping):
    """Generates a unigram index from the tokenized output from Parser.
    If 'stopping' is True, does not index stop words."""
    # Read the list of stopwords.
    with open('common_words') as f:
        STOP_WORDS = f.read().splitlines()
    # Invokes Parser to parse the raw html files,
    # and generate tokens
    Parser.main()

    for doc_name in Parser.DOC_TOKENS_MAP:
              
        tokens = Parser.DOC_TOKENS_MAP[doc_name]
        print("Indexing document : " + doc_name)

        # Keep track of number of tokens in each document.
        DOC_TOKEN_COUNT[doc_name] = len(tokens)
        
        for token in tokens:

            if stopping == True:
                if token not in STOP_WORDS:
                    index_token(token,doc_name)
            else:
                index_token(token,doc_name)


def index_token(token,doc_name):

    if token not in INVERTED_INDEX:
        INVERTED_INDEX[token] = {doc_name : 1}
    elif doc_name not in INVERTED_INDEX[token]:
        INVERTED_INDEX[token][doc_name] = 1
    else:
        INVERTED_INDEX[token][doc_name] += 1


def output_index_to_file(filename):
    """Saves the generated inverted index to file."""
    print("Saving index to file . .")

    with io.open(filename + ".txt", "w") as outfile:
        pprint(INVERTED_INDEX, stream=outfile)
        

def main(stopping):

    # Read the list of stopwords.
    with open('common_words') as f:
        STOP_WORDS = f.read().splitlines()

    # Generating unigram index.
    # Pass 'stopping' as true if stopping is to be performed,
    # else pass false.
    unigram_index(stopping)
    
    print("Completed Indexing.")   


#main(False)