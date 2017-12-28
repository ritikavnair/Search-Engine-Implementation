
DOC_TOKENS_MAP = {}

def Tokenizer():
    file = open("cacm_stem.txt", "r+")
    kk=[]
    for line in file:
        line = line.strip("\n")
        line = line.split(" ")
        if line[0] == "#":
            docid=line[1]
            if len(docid) == 1:
                docid = "CACM-000" + docid
            if len(docid) == 2:
                docid = "CACM-00" + docid
            if len(docid) == 3:
                docid = "CACM-0" + docid
            if len(docid) == 4:
                docid = "CACM-" + docid

            str=[]
        else:
            kk=words_in_doc(line,str)
            DOC_TOKENS_MAP[docid]=kk
            kk=[]
    #print(DOC_TOKENS_MAP)


def words_in_doc(line,str):
    flag=True
    for word in line:
        if not (word.isdigit() or word == ""):
            flag= False
    if (flag==True):
        return str
    while line != []:
        word = line.pop(0)
        if (word=="am" or word=="pm"):
            str.append(word)
        if not (word=="am" or word=="pm"):
            str.append(word)
        else:
            return str

def main():
    Tokenizer()

#main()