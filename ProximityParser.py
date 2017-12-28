from bs4 import BeautifulSoup
import io
import requests
import re
import glob, os
import string

CURRENT_DIR = os.getcwd()
CORPUS_PATH =  os.path.join(CURRENT_DIR, "cacm") 
DOC_TOKENS_MAP = {}
TOKENIZED_CORPUS_PATH =  os.path.join(CORPUS_PATH,r"TokenizedFile")

def Tokenizer(filename):
    file_title = os.path.basename(filename)
    print("Tokenizing file : " + file_title+"\n")
    with io.open(filename,"r", encoding="utf-8") as textfile:
        
        lines = textfile.read() 
    
    # Parse
    body_content = parse_html_doc(lines)

    #Tokenize
    tokens = tokenize(body_content)

    # Case Fold
    tokens = case_fold(tokens)

    # Remove unnecessary punctuation
    tokens = puncuation_handler(tokens)

    # Save tokens to file
    save_tokens_to_file(tokens,filename)

def parse_html_doc(raw_html):
    '''Extracts main body content text from the raw html''' 
    soup = BeautifulSoup(raw_html, 'html.parser')
    body = soup.find("pre").get_text()   

    match = re.search(r'\sAM|\sPM',body)
    if match:
        body = body[:match.end()]
    
    return body

def tokenize(text_content):
    '''Converts text into a list of tokens without spaces.'''
    raw_tokens = text_content.split()
    regex = re.compile('\w')
    
    return list(filter(regex.search, raw_tokens))

def case_fold(tokens):
    '''Returns case-folded list of tokens.'''    
    return [x.casefold() for x in tokens]

def puncuation_handler(tokens):
    punct_removed = []
    for token in tokens:
               
        punct_removed.append(remove_punctuation(token))
    
    # Remove white-space tokens
    regex = re.compile('\S')
    return list(filter(regex.search, punct_removed))

def remove_punctuation(s):
    
    # Remove unnecessary punctuation.
    s = re.sub(r'[^a-zA-Z0-9\-,\.–:]', '', str(s))
    # Remove trailing punctuation.    
    s = s.strip(string.punctuation)     
   
    number_matcher =  re.compile(r'[0-9]+([\d[,.:]?]?\d)*[-\.%–]?([\d[,.:]?]?\d)*$')
    
    if number_matcher.match(s):
        return s
    else:
        str_form = re.sub(r'[^a-zA-Z0-9\-–]', '', s)
        str_form = str_form.strip(string.punctuation)
        return str_form

    

''' while(word[:1] == "-" or word[:1] == "," or word[:1] == "."):
        # Handle numbers
        if re.match(r'^[\-]?[0-9]*\.?[0-9]+$', word):
            return word
        if word[:1] == "-" or word[:1] == "." or word[:1] == ",":
            word = word[1:]
        else:
            return word
    return word '''

def save_tokens_to_file(tokens,file):
    filename = os.path.basename(file)
    doc_id = filename[:-5]
    output_file = os.path.join(TOKENIZED_CORPUS_PATH,doc_id+".txt")
     
    global DOC_TOKENS_MAP   
    DOC_TOKENS_MAP[doc_id] = tokens
    with io.open(output_file, "w", encoding="utf-8") as tokenized_html:        
        for token in tokens:
            tokenized_html.write(token+"\n")


def main():

    # Read input CACM raw documents corpus
    input_path = os.path.join(CORPUS_PATH, r"*.html")
    files = glob.glob(input_path)
    
    # Create output directory for tokenized files
    os.makedirs(TOKENIZED_CORPUS_PATH,exist_ok=True)

    for filename in files:
        Tokenizer(filename)

    print("Completed parsing documents.")


#main()