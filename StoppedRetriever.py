import Indexer
import io
import glob, os
from pprint import pprint
from collections import Counter
import sys
import math
import string
import re
import traceback


# GLOBAL CONSTANTS 
CURRENT_DIR = os.getcwd()

RUN_OUTPUTS_DIR = os.path.join(CURRENT_DIR, "RunOutputs")
RETRIEVAL_MODEL = ""
DOC_TOKEN_COUNT = {}
INVERTED_INDEX = {}
QUERY_ID = 0
STOP_WORDS = []

def average_doc_length():
    """Returns the average document length for the documents in this input corpus."""

    total_length = 0
    for doc in DOC_TOKEN_COUNT:
        total_length += DOC_TOKEN_COUNT[doc]

    return float(total_length)/float(len(DOC_TOKEN_COUNT))

def read_relevance_info():
    try:
        relevant_docs = []
        rel_docs_in_corpus = []
        with io.open("cacm.rel.txt",'r', encoding="utf-8") as relevance_file:
            
            for line in relevance_file.readlines():
                values = line.split()
                if values and (values[0] == str(QUERY_ID)):
                    relevant_docs.append(values[2])
            for doc_id in DOC_TOKEN_COUNT:
                if doc_id in relevant_docs:
                    rel_docs_in_corpus.append(doc_id)
            
        return rel_docs_in_corpus
    except Exception as e:
        print(traceback.format_exc())

def relevant_doc_count(docs_with_term,relevant_docs):

    count = 0
    for doc_id in docs_with_term:
        if doc_id in relevant_docs:
            count+=1
    return count
    

def BM25_score(fetched_index, query_term_freq):
    """Computes BM25 scores for all documents in the given index.
    Returns a map of the document ids with thier BM25 score."""
    
    DOC_SCORE = {}

    # Initialize all docs with score = 0
    #for doc in DOC_TOKEN_COUNT:
    #    DOC_SCORE[doc] = 0

    relevant_docs = read_relevance_info()
    R = len(relevant_docs)
    

    avdl = average_doc_length()
    N = len(DOC_TOKEN_COUNT)
    k1 = 1.2
    k2 = 100
    b = 0.75

    for query_term in query_term_freq:

        qf = query_term_freq[query_term]
        n = len(fetched_index[query_term])
        if query_term in INVERTED_INDEX:
            r = relevant_doc_count(INVERTED_INDEX[query_term],relevant_docs)
        else:
            r = 0
        dl = 0
        for doc in fetched_index[query_term]:           
            
            f = fetched_index[query_term][doc]
            if doc in DOC_TOKEN_COUNT:
                dl = DOC_TOKEN_COUNT[doc]
            K = k1 * ((1-b) + ( b*(float(dl)/float(avdl))))
            relevance_part = math.log(((r + 0.5) / (R - r + 0.5)) / ((n - r + 0.5) / (N - n - R + r + 0.5)))
            k1_part = ((k1 + 1) * f) / (K + f)
            k2_part =  ((k2 + 1) * qf) / (k2 + qf)
            if doc in DOC_SCORE:
                DOC_SCORE[doc] +=( relevance_part * k1_part * k2_part)
            else:
                DOC_SCORE[doc] =( relevance_part * k1_part * k2_part)

        
    # return doc scores in descending order.
    return  DOC_SCORE

def output_to_file(doc_scores, query_id):
    """Prints the output scores into a textfile."""

    output_file = os.path.join(RUN_OUTPUTS_DIR,"Stopped"+RETRIEVAL_MODEL+"Run.txt")
    rank = 0
    
    with io.open(output_file ,"a+") as textfile:
        
        sorted_scores = [(k, doc_scores[k]) for k in sorted(doc_scores, key=doc_scores.get, reverse = True)]        
        for i in range(min(len(sorted_scores),100)):
            k,v = sorted_scores[i]
            rank += 1
            textfile.write(str(query_id) + " " + "Q0 "+ k + " " + str(rank) + " " + str(v) +" Stopped"+RETRIEVAL_MODEL+"Model\n") 
                
def query_matching_index(query_term_freq):
    """Fetches only those inverted lists from the index, that correspond to the query terms."""

    fetched_index = {}
    for term in query_term_freq:
        if term in INVERTED_INDEX:
            fetched_index[term] = INVERTED_INDEX[term]
        else:
            fetched_index[term] = {}

    return fetched_index

                
''' def query_term_freq_map(query):
    """Returns a map of query terms and their corresponding frequency in the query."""

    query_terms = query.split()
    query_term_freq = {}
    for term in query_terms:
        if term not in query_term_freq:
            query_term_freq[term] = 1
        else:
            query_term_freq[term] += 1
    return query_term_freq '''

def query_term_freq_map(query):
    """Returns a map of query terms and their corresponding frequency in the query."""

    query_terms = query.split()
    query_term_freq = {}
    
    for term in query_terms:
        if term not in STOP_WORDS:
            if term not in query_term_freq:
                query_term_freq[term] = 1
            else:
                query_term_freq[term] += 1
    return query_term_freq


def extract_queries_from_file():
    '''Read all queries from given file.'''
    extracted_queries = []
    raw_queries = open("cacm.query.txt",'r').read()
    while raw_queries.find('<DOC>')!=-1:
        query, raw_queries = extract_first_query(raw_queries)
        extracted_queries.append(query.lower())
    return extracted_queries

def extract_first_query(raw_queries):
    transformed_query = []
    query = raw_queries[raw_queries.find('</DOCNO>') + 8:raw_queries.find('</DOC>')]
    query = str(query).strip()

    query_terms = query.split()

    for term in query_terms:
        transformed_term = term.strip(string.punctuation)
        transformed_term = re.sub(r'[^a-zA-Z0-9\-,\.–]', '', str(transformed_term))
        if transformed_term != '':
            transformed_query.append(transformed_term)
    
    query = " ".join(transformed_query)
    raw_queries = raw_queries[raw_queries.find('</DOC>')+6:]
    return query, raw_queries

def QLM_score(fetched_index, query_term_freq):
    """Computes QLM scores for all documents in the given index.
    Returns a map of the document ids with thier QLM score."""
    
    DOC_SCORE_QLM = {}
    C = 0
    lambda_value = 0.35 

    # Initialize all docs with score = 0
    for doc in DOC_TOKEN_COUNT:
        #DOC_SCORE_QLM[doc] = 0
        C = C + DOC_TOKEN_COUNT[doc] #total number of words in collection
        

    for query_term in query_term_freq:
        cq = 0
        for doc in fetched_index[query_term]:
            cq = cq +  fetched_index[query_term][doc]#total occurance of query term in collection

        for doc in fetched_index[query_term]:   
            D = DOC_TOKEN_COUNT[doc] #total number of words in doc
            fq = fetched_index[query_term][doc] #total occurance of query term in doc
            first_part = float(1-lambda_value) * (fq / D)
            second_part = float(lambda_value) * (cq / C)
            if doc in DOC_SCORE_QLM:
                DOC_SCORE_QLM[doc] += math.log(first_part + second_part)
            else:
                DOC_SCORE_QLM[doc] = math.log(first_part + second_part)

        
    # return doc scores in descending order.
    return  DOC_SCORE_QLM
    
def tfidf_score(fetched_index, query_term_freq):
    """Computes tf-idf scores for all documents in the given index.
    Returns a map of the document ids with thier tfidf score."""
    
    DOC_SCORE_TFIDF = {}
    tf_idf_dict = {}

    for term in fetched_index:
        idf = 1.0 + math.log(float(len(DOC_TOKEN_COUNT)) / float(len(fetched_index[term].keys()) + 1)) 
        for doc_id in fetched_index[term]:
            tf = float(fetched_index[term][doc_id])/float(DOC_TOKEN_COUNT[doc_id])
            if term not in tf_idf_dict:
                tf_idf_dict[term] = {}
            tf_idf_dict[term][doc_id] = tf * idf  

    for term in fetched_index:
        for doc in fetched_index[term]:
            doc_weight = 0
            doc_weight = doc_weight + tf_idf_dict[term][doc]#get_doc_weight(doc,fetched_index,tf_idf_dict) 
            if doc in DOC_SCORE_TFIDF:
                doc_weight = doc_weight + DOC_SCORE_TFIDF[doc]
            DOC_SCORE_TFIDF.update({doc:doc_weight})

    # return doc scores in descending order.
    return  DOC_SCORE_TFIDF

def get_doc_weight(doc,fetched_index,tf_idf_dict):
    doc_weight = 0
    for term in tf_idf_dict:
        if doc in tf_idf_dict[term]:
            doc_weight += tf_idf_dict[term][doc]
    return doc_weight

def compute_doc_scores(fetched_index, query_term_freq):
    '''Decides scoring algorithm based on user desired retrieval model.'''
    global RETRIEVAL_MODEL

    if RETRIEVAL_MODEL == "BM25Relevance":                         
        return BM25_score(fetched_index, query_term_freq)
                
    elif RETRIEVAL_MODEL == "TFIDF":
        return tfidf_score(fetched_index, query_term_freq)
           
    # else it is "QL" model
    else:
        return QLM_score(fetched_index, query_term_freq)

def set_retrieval_model(user_choice):
    '''Sets vale of RETRIEVAL_MODEL algorithm based on user input.'''
    global RETRIEVAL_MODEL

    if user_choice == "1":     
        RETRIEVAL_MODEL = "BM25Relevance"       
                
    elif user_choice == "2":
        RETRIEVAL_MODEL = "TFIDF"
                   
    # else it is "3"
    else:
        RETRIEVAL_MODEL = "QL"
        

def main():

    print("--- RETRIEVER ---")
    print("Select")
    print("1 for BM25")
    print("2 for tf-idf")
    print("3 for Query Likelihood Model")
    user_choice = input("Enter your choice: ")
    if user_choice not in ["1", "2", "3"]:
        print("\nInvalid input. Aborting . .")
        sys.exit()

    global STOP_WORDS
    with open('common_words') as f:
        STOP_WORDS = f.read().splitlines()

    # sets "RETRIEVAL_MODEL" to the user chosen model.
    set_retrieval_model(user_choice)
    
    # Create a directory to save the results.  
    # and overwrite existing run file, if any 
    os.makedirs(RUN_OUTPUTS_DIR,exist_ok=True)
    global RETRIEVAL_MODEL
    output_file = os.path.join(RUN_OUTPUTS_DIR,"Stopped"+RETRIEVAL_MODEL+"Run.txt")
    if os.path.exists(output_file):
        os.remove(output_file)
     
    # Generate the unigram index.
    # By performing stopping.
    # So send True
    Indexer.unigram_index(True)    

    # Fetch the index generated.
    global INVERTED_INDEX
    INVERTED_INDEX = Indexer.INVERTED_INDEX
    global DOC_TOKEN_COUNT
    DOC_TOKEN_COUNT = Indexer.DOC_TOKEN_COUNT
      

    # Read all queries. 
    queries = extract_queries_from_file()   
    
    global QUERY_ID
    for query in queries:
        QUERY_ID +=1       
        
        # Dictionary of query term frequency
        query_term_freq = query_term_freq_map(query)
        
        # Fetch the inverted indexes corresponding to the terms
        # in the query.
        fetched_index = query_matching_index(query_term_freq)
                
        # Compute ranking scores of all docs for this query.
        doc_scores = compute_doc_scores(fetched_index, query_term_freq)
        
        # Write results to a textfile.
        output_to_file(doc_scores,QUERY_ID)        

        print("Completed Retrieval for query : " + query)

    print("End of Retrieval.")

main()