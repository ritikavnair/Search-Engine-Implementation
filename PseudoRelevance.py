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
CORPUS_PATH = os.path.join(CURRENT_DIR, "cacm")
RUN_OUTPUTS_DIR = os.path.join(CURRENT_DIR, "RunOutputs")
RUN_OUTPUT_FILE = os.path.join(RUN_OUTPUTS_DIR,"PseudoRelBM25Run.txt")

DOC_TOKEN_COUNT = {}
INVERTED_INDEX = {}
QUERY_ID = 0

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
        with io.open(os.getcwd() + "\\cacm.rel.txt",'r', encoding="utf-8") as relevance_file:
            
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
                DOC_SCORE[doc] +=(relevance_part * k1_part * k2_part)
            else:
                DOC_SCORE[doc] =(relevance_part * k1_part * k2_part)

        
    # return doc scores in descending order.
    return  DOC_SCORE


def pseudo_relevance(query,doc_scores):

    k = 10

    # Step 1 : Generate query vector.
    query_vector = {}
    query_terms = query.split()
    for term in query_terms:
        if term in query_vector:
            query_vector[term] +=1
        else:
            query_vector[term] = 1
    for term in INVERTED_INDEX:
        if term not in query_vector:
            query_vector[term] = 0

    # Step 2 : Generate vector for relevant documents.
    relevance_vector = {}
    doc_scores_asc = [(k, doc_scores[k]) for k in sorted(doc_scores, key=doc_scores.get, reverse = True)]
    #doc_scores_asc = sorted(doc_scores.items(), key=operator.itemgetter(1), reverse=True)
    for i in range(0,k):
        doc_id,doc_score = doc_scores_asc[i]
        doc_content= open(os.path.join(CORPUS_PATH, doc_id+".html")).read()   
        for term in doc_content.split():
            if term in relevance_vector:
                relevance_vector[term] += 1
            else:
                relevance_vector[term] = 1

    for term in INVERTED_INDEX:
        if term not in relevance_vector:
            relevance_vector[term] = 0

    # Calculate magnitude of the relevant document set vector
    rel_vector_magnitude = 0
    for term in relevance_vector:
        rel_vector_magnitude += float(relevance_vector[term]**2)
    rel_vector_magnitude = float(math.sqrt(rel_vector_magnitude))
    

    # Step 3 : Generate vector for non - relevant documents
    non_relevance_vector = {}
    for i in range(k+1,len(doc_scores_asc)):
        doc_id,doc_score = doc_scores_asc[i]
        doc_content= open(os.path.join(CORPUS_PATH, doc_id+".html")).read()
        for term in doc_content.split():
            if term in non_relevance_vector:
                non_relevance_vector[term] += 1
            else:
                non_relevance_vector[term] = 1

    for term in INVERTED_INDEX:
        if term not in non_relevance_vector:
            non_relevance_vector[term] = 0
    
    # Calculate magnitude of the non-relevant document set vector
    non_rel_vector_magnitude = 0
    for term in non_relevance_vector:
        non_rel_vector_magnitude += float(non_relevance_vector[term]**2)
    non_rel_vector_magnitude = float(math.sqrt(non_rel_vector_magnitude))

    # Step 4 : Generate the new query
    query_expansion_terms = {}
    for term in INVERTED_INDEX:
        query_expansion_terms[term] = query_vector[term] + (0.5/rel_vector_magnitude) * relevance_vector[term] - (0.15/non_rel_vector_magnitude) * non_relevance_vector[term]

    #sorted_expansion_query_terms = sorted(query_expansion_terms.items(), key=operator.itemgetter(1), reverse=True)
    sorted_expansion_query_terms = [(k, query_expansion_terms[k]) for k in sorted(query_expansion_terms, key=query_expansion_terms.get, reverse = True)]
        
    expanded_query = query
    for i in range(20):
        term,freq = sorted_expansion_query_terms[i]
        if term not in query:
            expanded_query +=  (" " + term)        
        
    
    
    expanded_query_freq = query_term_freq_map(expanded_query)
    updated_fetched_index = query_matching_index(expanded_query_freq)
    updated_bm25_scores = BM25_score(updated_fetched_index,expanded_query_freq )
    
    return updated_bm25_scores
    


def output_to_file(doc_scores, query_id):
    """Prints the output scores into a textfile."""

    rank = 0
    with io.open(RUN_OUTPUT_FILE ,"a+") as textfile:
        #Counter(doc_scores).most_common(100):
        sorted_scores = [(k, doc_scores[k]) for k in sorted(doc_scores, key=doc_scores.get, reverse = True)]        
        for i in range(min(len(sorted_scores),100)):
            k,v = sorted_scores[i]
            rank += 1
            textfile.write(str(query_id) + " " + "Q0 "+ k + " " + str(rank) + " " + str(v) + " PseudoRelBM25Model\n") 
                
def query_matching_index(query_term_freq):
    """Fetches only those inverted lists from the index, that correspond to the query terms."""

    fetched_index = {}
    for term in query_term_freq:
        if term in INVERTED_INDEX:
            fetched_index[term] = INVERTED_INDEX[term]
        else:
            fetched_index[term] = {}

    return fetched_index

                
def query_term_freq_map(query):
    """Returns a map of query terms and their corresponding frequency in the query."""

    query_terms = query.split()
    query_term_freq = {}
    for term in query_terms:
        if term not in query_term_freq:
            query_term_freq[term] = 1
        else:
            query_term_freq[term] += 1
    return query_term_freq


def extract_queries_from_file():
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

    
    


def main():

    print("--- PSEUDO RELEVANCE RETRIEVER ---")

    # Create a directory to save the results.  
    # and overwrite existing run file, if any 
    os.makedirs(RUN_OUTPUTS_DIR,exist_ok=True)    
    output_file = os.path.join(RUN_OUTPUTS_DIR,"PseudoRelBM25Run.txt")
    if os.path.exists(output_file):
        os.remove(output_file)

    # Generate the unigram index.
    # By default, not performing stopping.
    # So send False
    Indexer.unigram_index(False)    

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
                
        # Compute BM25 score for this query term.
        doc_scores = BM25_score(fetched_index, query_term_freq)

        # Update doc scores using Pseudo-relevance
        doc_scores = pseudo_relevance(query,doc_scores)
        
        # Write results to a textfile.
        output_to_file(doc_scores,QUERY_ID)        

        print("Completed Retrieval for query : " + query)

    print("End of Pseudo Relevance retrieval.")

main()