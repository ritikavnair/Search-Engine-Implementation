def evaluation():
    relevance_judgementsdocs={}
    typesofruns = []
    ranking=[]
    querydoc={}
    queries=[]
    reldoc={}
    #Reads values from Runs1.txt
    runs = open("Runs1.txt", "r")
    for line in runs:
        line = line.split()
        typesofruns.append(line)
    runs.close()
    cacmrelevance = open("cacm.rel.txt", "r")
# Creates a relevancejudgementsdocs dictionary that maps the query to the total number of relevant documents
    for line in cacmrelevance:
        lines = line.split()
        if (lines[0]) in relevance_judgementsdocs:
            relevance_judgementsdocs[lines[0]] = relevance_judgementsdocs[lines[0]] + 1
        else:
            relevance_judgementsdocs[lines[0]]=1
# Creates a dictionary reldoc that maps the doc and query to the relevance judgement for that query for that term.
        reldoc[lines[0]+lines[2]]=lines[3]
    cacmrelevance.close()

    for run in typesofruns:
            run=str(run).replace('[',"").replace(']',"").replace('\'',"")
            #Creates a file with the output retrieval model name+"result.txt"
            output = open(run[:-4]+"result.txt", "w")
            #The format in which the outputs are required.
            output.write("Query \t Document \t Ranking \t R/N \t Precision \t\t\t Recall"+"\n")
            file = open(run, "r")
            #Computes all the queries and stores it in queries.
            for line in file:
                temp = line.split()
                if not (temp[0] in queries):
                    queries.append(temp[0])
                # A dictionary consisting of query to doc mapping is generated only if relevance judgements for that query is present, other quries are just skipped.
                if  (temp[0]) in relevance_judgementsdocs:
                    if (temp[0]) in querydoc:
                        querydoc[temp[0]].append(temp[2])
                    else:
                        querydoc[temp[0]] = [temp[2]]
            retreived = {}
            relevant = {}
            precision = {}
            recall = {}
            avgprecision={}
            totalrel={}
            precisionat5={}
            precisionat20 = {}
            filenotevaluated={}
            rr={}
            map=0
            mrr=0

            flag={}
            # Initializing the dictionaries for all docs in querydoc dictionary
            for i, tokens in querydoc.items():
                retreived[i] = 0
                precision[i] = 0
                recall[i] = 0
                relevant[i] = 0
                avgprecision[i] = 0
                flag[i] = 0
                rr[i] = 0
                precisionat5[i]=0
                precisionat20[i]=0
                filenotevaluated[i]=False

            if i not in relevance_judgementsdocs:
                filenotevaluated[i]=True
# Calculating the total number for relevant documents for all queries.
            for i, tokens in relevance_judgementsdocs.items():
                totalrel[i]=tokens
# Computing precision, recall, precision at 5, precision at 20, reciprocal ranking and average precision for all the queries.
            for i, tokens in querydoc.items():
                for token2 in tokens:
                    retreived[i]=retreived[i]+1
                    rn="N"
                    #If document for a query is relevant and is the first relevant document, compute reciprocal rank.
                    if (i + token2) in reldoc:
                        if flag[i]==0:
                            rr[i]=1/retreived[i]
                            flag[i]=1
                        relevant[i] = relevant[i] + 1
                        rn = "R"

                        avgprecision[i]=avgprecision[i]+float(relevant[i]) /float(retreived[i])
                    precision[i] = float(relevant[i]) /float(retreived[i])
                    recall[i] = float(relevant[i])/float(totalrel[i])
                    if retreived[i]==5:
                        precisionat5[i]=precision[i]
                    if retreived[i]==20:
                        precisionat20[i]=precision[i]
                    #Prints the output to a file
                    output.write(str(i)+"\t 	 "+str(token2)+"\t  "+str(retreived[i])+"\t 	      "+ str(rn) +"\t	   "+ str(precision[i])+"\t"+str(recall[i])+"\n")
                output.write("P@5 for query "+str(i)+" is: "+str(precisionat5[i])+"\n")
                output.write("P@20 for query " + str(i) + " is: " + str(precisionat20[i])+"\n")
            output.close()
# Computes map and mrr for all the queries
            for query in queries:
                if query in relevance_judgementsdocs:
                    map=map+(float(avgprecision[query])/float (totalrel[query]))
                    mrr=mrr+rr[query]

            outputfile = open(run[:-4] + "MAPMRRresult.txt", "w")
            map = float(map) / 64
            mrr = float(mrr) / 64
#Prints the output in a seperate file
            outputfile.write("MAP for "+ str(run)[:-4]+" is: "+str(map)+"\n")
            outputfile.write("MRR for " + str(run)[:-4] + " is: " + str(mrr)+"\n")

            outputfile.close()





evaluation()
