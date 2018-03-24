# Canadian GRIN Database Scraper
# By: Delvin So

# Given a .csv of variety names, the program will query each variety against the GRIN database and return the accession number and URL to the console
# Additionally, a .csv will be created with the first column being the variety name and subsequent columns corresponding to the accession number and URL

# How to use : python .py  -f test_list.csv -o test_out.csv
#
## Sample output :
# --------------------------------------------------
# Current variety is: CM96097
#
# Querying GRIN...
# Finished querying GRIN... 7 seconds elapsed
# One accession found for CM96097
#
# CN 106375: http://pgrc3.agr.gc.ca/cgi-bin/npgs/html/acc_search.pl?accid=CM96097
#
# --------------------------------------------------
# Current variety is: CM99058
#
# Querying GRIN...
# Finished querying GRIN... 1 seconds elapsed
# Zero accessions found for CM99058
#
# --------------------------------------------------
# Current variety is: Columbus
#
# Querying GRIN...
# Finished querying GRIN... 1 seconds elapsed
# Multiple Accessions found for Columbus
#
# Wheat:
# CN 9687: http://pgrc3.agr.ca/cgi-bin/npgs/html/acchtml.pl?9194
# CN 37156: http://pgrc3.agr.ca/cgi-bin/npgs/html/acchtml.pl?39544
# CN 38925: http://pgrc3.agr.ca/cgi-bin/npgs/html/acchtml.pl?41540
# CN 43983: http://pgrc3.agr.ca/cgi-bin/npgs/html/acchtml.pl?47145
#
#
# Other:
#
#
# End List of Multiple Accessions found for Columbus
#
# --------------------------------------------------
# Current variety is: CRGB-0-623.4
#
# Querying GRIN...
# Finished querying GRIN... 1 seconds elapsed
# Zero accessions found for CRGB-0-623.4


import requests  # for querying
import pandas as pd
from bs4 import BeautifulSoup

import time  # for calculating time spent querying
import csv  # for writing dictionary to csv
import argparse  # for parsing in command line arguments

# initializing parser
parser = argparse.ArgumentParser()
# creating argument
parser.add_argument( "-f","--file", type=str, required=True)
parser.add_argument("-o","--output",dest='outfile')
args = parser.parse_args()

# import os
#
# os.getcwd()
# os.chdir("/Users/delvin/Dropbox/python")
# read in csv of variety names

## Processing the user input list of variety names ##
# Reading in the csv
varDF = pd.read_csv(args.file, header=0)

# varDF = pd.read_csv("delvins_list.csv",header=0)

# extract column of varieties as a list to iterate through
varListRaw = varDF[varDF.columns[0]].values

# a test list to iterate through to make sure everything is working smoothly
testList = ['AC Sampson', 'Selkirk', 'AC Mackinnon']  # none, multiple, single


def grinDBscraper(list):
    # for storing variety and corresponding accession and link
    varDict = {}

    # count statistics
    noHit = 0
    singleHit = 0
    multiHit = 0

    for variety in list:

        # account for :, - and white space when inserting into links
        formattedVariety = variety.replace(" ", "+").replace(":", "%")

        # formatting
        print("-" * 75)
        # indicates to user the current variety
        print("Current variety is: %s\n" %variety)

        # generating link to be queried
        baseLink ="http://pgrc3.agr.gc.ca/cgi-bin/npgs/html/acc_search.pl?accid="
        link = baseLink + formattedVariety

        # Printing some output to the console indicating GRIN is being queried and the time it took to do so

        # print("Querying:  %s" % (item))
        print("Querying GRIN...")
        start = time.time()
        # querying the URL
        r = requests.get(link)
        end = time.time()
        elapsed = end - start
        # print("Finished querying %s, %i seconds elapsed" % (item,elapsed))
        print("Finished querying GRIN... %i seconds elapsed" %elapsed)

        # BSing for navigating the HTML
        soup = BeautifulSoup(r.text, "html.parser")

        # Lists for use if multiple results returned, reinitialized at the beginning of each iteration
        goodHits = []
        badHits = []

        if "No accessions found" in r.text:
            print("Zero accessions found for %s\n" % (variety))
            noHit += 1

        elif "Accessions returned" in r.text:  # account for single and multiple accession numbers
            print("Multiple Accessions found for %s\n" % (variety))

            # pattern identification: the accession and links are embedded within OL( ordered lists), knowing this we can extract the information we need as follows

            tag = soup.find_all("ol")  # find all ordered lists, the last one is (usually?) the one of interest containing the ID and links - has not failed so far.
            # print(tag)
            # given how the GRIN DB works with single queries, they will return all species. since we are only interested in wheat varieties we will have to filter the 'bad' hits out.

            for anchor in tag[-1].find_all("a"):  # find all anchors within the last ordered list which contains the accession ID's and URL's of hits

                if "Triticum aestivum" in anchor.text.strip():
                    id = " ".join(
                        anchor.text.strip().split()[:2])  # splitting by " " and rejoining the accession identifier,
                    # the original cleaned anchor looks like this for reference :
                    # http://pgrc3.agr.ca/cgi-bin/npgs/html/acchtml.pl?3229 CN    2740   Triticum aestivum subsp. aestivum Selkirk
                    # print(id, anchor['href'])

                    both = id + ": " + anchor['href']  # storing the accession ID and link in a clean format
                    goodHits.append(both)  # appending the accession ID and link to a list

                else:  # not wheat...
                    id = " ".join(anchor.text.strip().split()[:2])
                    # print(id, anchor['href'])

                    both = id + ": " + anchor['href']
                    badHits.append(both)
                    # print("NOT WHEAT: %s"%(anchor))

            print("Wheat: ")

            for good in goodHits:
                print(good)
                varDict.setdefault(variety, []).append(
                    good)  # appending the variety name and its corresponding ID and URL to  our dictionary

            print("\n")

            print("Other: ")
            for bad in badHits:
                print(bad)
            print("\n")

            multiHit += 1
            print("End List of Multiple Accessions found for %s\n" % (variety))
        else:  # working with the assumption that if not a 'no' result or 'multiple' result,
            # it will be a single result and be processed accordingly.
            # hasn't failed so far and I can always go back and go through the links manually to troubleshoot if anything.

            # if single accession - print stored link and accession ID, else
            # strong = soup.find_all("strong")
            # strong  # first result has what we're looking for
            # simplify to

            # pattern identification: the accession ID is stored within the first!! <strong></strong> tags and the URL for single hits the queried link
            strong = soup.find("strong")
            id = strong.text.strip()  # our accession number
            both = id + ": " + link
            varDict.setdefault(variety, []).append(both)
            print("One accession found for %s\n" % (variety))
            print("%s: %s\n" % (id, link))

            singleHit += 1

    print("-" * 75)

    # for debugging the dictionary
    # for variety,idLink in varDict.items():
    #     print("Variety: %s\n ID/Link: %s"%(variety,idLink))

    ##writing to a file

    unique = []


    if args.outfile:
        print("Output file saved as: %s\n"%args.outfile)
    else:
        args.outfile = "varieties_list.csv"
        print("Output file was not specified , by default output is saved as: %s\n\n" %args.outfile)



    # with open(args.outfile, "w") as handle:
    with open("test_out.csv", "w") as handle:
        writer = csv.writer(handle)
        for var, idLink in varDict.items():
            #print("Variety: %s\n ID/Link: %s" % (var, idLink))
            for item in idLink:  #can be multiple idLinks, iterate through each one and place on a new row with corresponding variety name
                unique = item.split(":",1) #splits on first : which seperates the accession ID and the URL
                #print(unique)
                writer.writerow([var, unique[0],unique[1]])
                # print(unique)
            # writer.writerow([var,idLink])

    print("Single Results: %i\nMultiple Results: %i\nNo Results: %i\n\n" % (singleHit, multiHit, noHit))

    #args.output default


# Running the scraper on the user defined list
grinDBscraper(varListRaw)


# grinDBscraper(testList)
# grinDBscraper(varListRaw)
# grinDBscraper(testList)

# Debugging
# # One accession
# link = "http://pgrc3.agr.gc.ca/cgi-bin/npgs/html/acc_search.pl?accid=AC+Mackinnon"
# r = requests.get(link)
# soup = BeautifulSoup(r.text, "html.parser")
# print(soup)
# if "GRIN/NPGS ACCESSION INFORMATION" in r.text:
#     print("yep")
# # for single result accessions, the accession number is embedded in a <strong></strong> tag
# strong = soup.find_all("strong")
# strong  # first result has what we're looking for
# # simplify to
# strong = soup.find("strong")
# strong.text.strip()  # our accession number
#
#
#
#
# # if single, we want to strip the identifier name and store it - what are the surrounding tags for this?
# # none
# link = "http://pgrc3.agr.gc.ca/cgi-bin/npgs/html/acc_search.pl?accid=AC+Sampson"
# # multiple
# link = "http://pgrc3.agr.gc.ca/cgi-bin/npgs/html/acc_search.pl?accid=Selkirk"
# # ??
# r = requests.get(link)
# #print(r.text)
# soup = BeautifulSoup(r.text, "html.parser")
# #print(soup)

#
#
# if "No accessions found" in r.text:
#     print("None\n")
# elif "Accessions returned" in r.text:  # account for single and multiple accession numbers
#     # if single accession - print stored link and accession ID, else
#     # the accession and links are embedded within OL( ordered lists), knowing this we can extract the information we need as follows
#     tag = soup.find_all("ol") #find all ordered lists, the last one is (usually?) the one of interest containing the ID and links
#     for anchor in tag[-1].find_all("a"): #individual anchors
#         if "Triticum aestivum" in anchor.text.strip():
#             id = " ".join(anchor.text.strip().split()[:2])   # splitting by " " and rejoining the accession identifier,
#                                                              # the original cleaned anchor looks like this for reference :
#                                                              # http://pgrc3.agr.ca/cgi-bin/npgs/html/acchtml.pl?3229 CN    2740   Triticum aestivum subsp. aestivum Selkirk
#             print(id,anchor['href'])
#
#     print("Multiple Accessions found\n")
# else:
#     # if single accession - print stored link and accession ID, else
#     print("One accession found")
#
#
# if "Triticum aestivum" in tag[-1].find_all("a"):
#     print("yes")
# else:
#     print("no")
