# modified from: https://erilu.github.io/pubmed-abstract-compiler/#:~:text=Using%20the%20NCBI%20E%2Dutilities%20(Entrez%20Programming%20Utilities%2C%20https,software%E2%80%93its%20completely%20URL%20based.

import csv
import re
import urllib.request
from time import sleep

query = 'genes+gene'

# common settings between esearch and efetch
base_url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
db = 'db=pubmed'

# esearch specific settings
search_eutil = 'esearch.fcgi?'
search_term = '&term=' + query
search_usehistory = '&usehistory=y'
search_rettype = '&rettype=json'

search_url = base_url+search_eutil+db+search_term+search_usehistory+search_rettype
print(search_url)

f = urllib.request.urlopen(search_url)
search_data = f.read().decode('utf-8')


# obtain total abstract count
total_abstract_count = int(re.findall("<Count>(\d+?)</Count>",search_data)[0])
print(f'total abstract count:{total_abstract_count}')

# obtain webenv and querykey settings for efetch command
fetch_webenv = "&WebEnv=" + re.findall ("<WebEnv>(\S+)<\/WebEnv>", search_data)[0]
fetch_querykey = "&query_key=" + re.findall("<QueryKey>(\d+?)</QueryKey>",search_data)[0]


# other efetch settings
fetch_eutil = 'efetch.fcgi?'
retmax = 10
retstart = 0
fetch_retstart = "&retstart=" + str(retstart)
fetch_retmax = "&retmax=" + str(retmax)
fetch_retmode = "&retmode=text"
fetch_rettype = "&rettype=abstract"

# call efetch commands using a loop until all abstracts are obtained
run = True
all_abstracts = list()
loop_counter = 1

while run:
    print("this is efetch run number " + str(loop_counter))
    loop_counter += 1
    fetch_retstart = "&retstart=" + str(retstart)
    fetch_retmax = "&retmax=" + str(retmax)
    # create the efetch url
    fetch_url = base_url+fetch_eutil+db+fetch_querykey+fetch_webenv+fetch_retstart+fetch_retmax+fetch_retmode+fetch_rettype
    print(fetch_url)
    # open the efetch url
    f = urllib.request.urlopen (fetch_url)
    fetch_data = f.read().decode('utf-8')
    # split the data into individual abstracts
    abstracts = fetch_data.split("\n\n\n")
    # append to the list all_abstracts
    all_abstracts = all_abstracts+abstracts
    print("a total of " + str(len(all_abstracts)) + " abstracts have been downloaded.\n")
    # wait 2 seconds so we don't get blocked
    sleep(2)
    # update retstart to download the next chunk of abstracts
    retstart = retstart + retmax
    if retstart > 10:
        run = False

with open("abstracts.txt", "wt", encoding="utf-8") as abstracts_file, open ("partial_abstracts.csv", "wt") as partial_abstracts:
    # csv writer for full abstracts
    abstract_writer = csv.writer(abstracts_file)
    # abstract_writer.writerow(['Journal', 'Title', 'Authors', 'Author_Information', 'Abstract', 'DOI', 'Misc'])
    # csv writer for partial abstracts
    partial_abstract_writer = csv.writer(partial_abstracts)
    #For each abstract, split into categories and write it to the csv file
    for abstract in all_abstracts:
        #To obtain categories, split every double newline.
        split_abstract = abstract.split("\n\n")
        if len(split_abstract) > 5:
            indices = [4]
            split_abstract = [split_abstract[i] for i in indices]
            abstract_writer.writerow(split_abstract)
        else:
            partial_abstract_writer.writerow(split_abstract)