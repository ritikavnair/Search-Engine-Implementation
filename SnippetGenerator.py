import io
import os
import Parser
import re
import operator

CORPUS_PATH = os.path.join(os.getcwd() ,"cacm")
INVERTED_INDEX ={}


def snippet_selector(doc,query_terms):


    filename = os.path.join(CORPUS_PATH ,doc+".html")
    with io.open(filename,"r", encoding="utf-8") as raw_file:
        
        lines = raw_file.read() 
    
    # Parse
    body_content = Parser.parse_html_doc(lines)

    # Identify sentences
    sentences = re.split(r"\.[\s\n]+", body_content)

    # Populating significant word list
    significant_words = find_sig_words(sentences,doc,query_terms)

    # Generate scores for each sentence.
    sentence_scores = {}
    for line in sentences:
        sentence_scores[line] = significance_factor(line,significant_words)
    sorted_sentence_scores = sorted(sentence_scores.items(), key=operator.itemgetter(1), reverse = True)
    #sorted_sentence_scores = sorted(sentence_scores, key=sentence_scores.get, reverse = True)
    snippet = []
    
    
    if sorted_sentence_scores[0][1] == 0:
        return snippet

    #if sorted_sentence_scores.values()[0] == 0:
    #    return snippet

    count = 0
    for sentence,score in sorted_sentence_scores:
        # Selecting top 2 snippets
        if(count<4):
            snippet.append(sentence)
            count+=1

    return snippet


def significance_factor(line,significant_words):
    '''Calculates the significance factor for a line of text.'''
    
    # Case - folded comparision
    words = line.split()  
    words = [x.casefold() for x in words]
    significant_words = [x.casefold() for x in significant_words]
    
    # Find the start of span
    start = 0
    for word in words:
        
        if word in significant_words: #   word_in_query(word,query_terms):
            start = words.index(word)
            break

    # find the end of span
    end = 0
    for i in range(len(words)-1, 0, -1):
        if word in significant_words: #word_in_query(words[i],query_terms):
            end = i
            break

    # count the number of signifcance words in this span
    count = 0
    for x in words[start:end]:
        if word in significant_words: #word_in_query(x,query_terms):
            count += 1 

    if count == 0:
        return 0
    else:
        span = (end - start + 1)
        return (count * count)/span

def find_sig_words(sentences,doc, query_terms):
    
    sig_words = []
    # sd = number of sentences in the document
    sd = len(sentences)

    with open('common_words') as f:
        stopwords = f.read().splitlines()

    for sentence in sentences:
        words = sentence.split()
        for word in words:
            if word not in stopwords:
                processed_word = process_word(word)
                if processed_word == '':
                    continue
                fdw = INVERTED_INDEX[processed_word][doc]
                if (check_threshold(sd,fdw)) and word not in sig_words:
                    sig_words.append(word)
    
    for term in query_terms:        
        if not word_in_query(term, sig_words):
            sig_words.append(term)
    
    return sig_words

def process_word(word):
    word = word.casefold()
    word = Parser.remove_punctuation(word)
    return word


def check_threshold(sd,fdw):
    threshold = 0
    if sd < 25:
        threshold = 7 - float(0.1) * float(25-sd)
    elif (sd <= 40 and sd >= 25):
        threshold = 7
    else:
        threshold = 7 + float(0.1) * float(sd-40)

    # if frequency of word greater than threshold, it is significant.
    if fdw >= threshold:
        return True
    else:
        return False

def word_in_query(word,query_terms):
    '''Returns true if the given word is present in the query'''
    #query_terms = query.split()
    # Case fold
    query_terms = [x.casefold() for x in query_terms]
   
    if word.casefold() in query_terms:
        return True
    else:
        return False



def snippet_generator(doc_list,query,inverted_index):

    global INVERTED_INDEX
    INVERTED_INDEX = inverted_index
     # Query stopping
    with open('common_words') as f:
        stopwords = f.read().splitlines()
    query_terms = query.split()
    ''' for term in query_terms:
        if term in stopwords:
            query_terms.remove(term) '''

    query_terms = [x for x in query_terms if not x in stopwords]

    for doc in doc_list:
        snippet_lines = snippet_selector(doc,query_terms)

        if len(snippet_lines) == 0:
            continue
        result = ""
        print("------ "+ doc+ " -------")
        for line in snippet_lines:
            
            result += ".."
            for word in line.split():
                if word_in_query(word,query_terms):
                    result += ('\033[1m' + '\033[91m' + word + '\033[0m' + " ")
                else:
                    result += (word + " ")
            
            result += "..\n"
        print(result)
        print("--------")

       