#!/usr/bin/python
import urllib.request
import json
import re
import os
import sys
from xml.dom import minidom
from xml.etree import ElementTree as etree

ttyLen = int(os.popen('stty size', 'r').read().split()[1]) 

# progress bar functions
def _reporthook(numblocks, blocksize, filesize, url=None):
    try:
        percent = min((numblocks*blocksize*100)/filesize, 100)
    except:
        percent = 100
    if numblocks != 0:
        bar = '#' * int(percent/5) + '-' * int(20-percent/5)
        print('\r[%s] %s%s   ' % (bar, percent, '%')),
        sys.stdout.flush()

def geturl(url, dst):
    if(os.path.isfile(dst)):
        if(raw_input("A file already exists with that name. Continue? (y/n)").lower() == 'n'):
            print("Move the file and try again")
            sys.exit(0)
    try:
        urllib.request.urlretrieve(url, dst.encode("ascii", "ignore"),
                       lambda nb, bs, fs, url=url: _reporthook(nb,bs,fs,url))
    except IOError:
        print("There was an error retrieving the data. Check your internet connection and try again.")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nYou have interrupted an active download.\n Cleaning up fines now.")
        os.remove(dst)
        sys.exit(1)


def main():

    # correctly get the user's podcast
    while True:

        podcastSearch = input("Podcast you want to download: ")
        podcastSearch = re.sub(r" ", "+", podcastSearch)

        # grab podcast info
        url = "https://itunes.apple.com/search?term=" + podcastSearch + "&entity=podcast"
        try:
            with urllib.request.urlopen(url) as url2:
                response = url2.read().decode(url2.headers.get_content_charset())
        except IOError:
            print("There was an error retrieving the data. Check your internet connection and try again.")
            sys.exit(0)

        data = json.loads(response)
        resultCount = data["resultCount"] 
        print(str(resultCount) + " results were found. Displaying results:")

        #can display top ten by changing to:
        #for i in range(min(10,resultCount))
        for i in range(resultCount):
            print (str(i+1)+ ": " + data["results"][i]["trackName"])
            print("  artist: "+ data["results"][i]["artistName"])


        try:
            userSelection = int(input("Enter a number (0 if none): "))
        except ValueError:
            userSelection = -1

        if userSelection > 0 and userSelection < int(resultCount):
            podcastName = data["results"][userSelection-1]["trackName"]
            podcastId = data["results"][userSelection-1]["collectionId"]
            print("You have selected " + podcastName)
            break
        else:
            print("Please search again.")

    # grab podcast feed
    url = "https://itunes.apple.com/lookup?id=" + str(podcastId) + "&entity=podcast"
    try:
        with urllib.request.urlopen(url) as url2:
            response = url2.read().decode(url2.headers.get_content_charset())
    except IOError:
        print("There was an error retrieving the data. Check your internet connection and try again.")
        sys.exit(0)

    data = json.loads(response)

    rss = data["results"][0]["feedUrl"]

    # grab all podcast .mp3 files
    url_str = rss
    try:
        xml_str = urllib.request.urlopen(url_str).read()
    except IOError:
        print("There was an error retrieving the data. Check your internet connection and try again.")
    xmldoc = minidom.parseString(xml_str)

    values = xmldoc.getElementsByTagName('enclosure')
    titles = xmldoc.getElementsByTagName('title')

    # append the title list such that the correct title is corresponding to the
    # equivlanet .mp3 link
    nameChecker = True
    counter = 0
    while nameChecker:
        if podcastName == titles[counter].firstChild.nodeValue:
            counter = counter + 1
        else:
            nameChecker = False

    titles = titles[counter:]

    # insert mp3 list into mp3list array
    mp3list = []
    for val in values:
        mp3list.append(val.attributes['url'].value)

    numTitles = len(titles)

    print("The newest titles are:")
    for i in range(min(10, len(titles))):
        print (titles[i].firstChild.nodeValue.strip('\n'))

    # get how the user wants to download the files

    downloadAll = False
    downloadOne = -1
    downloadNew = False;
    downloadRangeStart = -1
    downloadRangeFinish = -1
    badInput = True

    while badInput: 
        badInput = False
        userDownload = input('Which file(s) to download? ')
        if userDownload == "All" or userDownload == "all":
            downloadAll = True
        elif userDownload.isdigit():
            downloadOne = len(mp3list) - int(userDownload) + 1
        elif 'to' in userDownload or '-' in userDownload:
            if('to' in userDownload ):
                rangeList = re.split('to', userDownload)
            else:
                rangeList = re.split('-', userDownload)
                #print(rangeList)
                if(rangeList.count('')):
                    print ("Error: bad input")
                    badInput = True
            if not badInput:        
                downloadRangeStart = len(mp3list) - int(rangeList[1])
                downloadRangeFinish = len(mp3list) - int(rangeList[0])
                if downloadRangeStart < 1 or downloadRangeFinish < 1:
                    print ("Error: bad input")
                    badInput = True
                if downloadRangeStart > downloadRangeFinish:
                    print ("Error: bad input")
                    badInput = True
        elif userDownload == "latest" or userDownload == "new" or userDownload == "New":
            downloadNew = True
        else:
            print ("Error: bad input")
            badInput = True

    if downloadAll:
        for i in range(len(mp3list)):
            print("Downloading: " + str(titles[i].firstChild.nodeValue))
            saveLoc = os.path.dirname(os.path.realpath(__file__)) + "/" + titles[i].firstChild.nodeValue + ".mp3"
            geturl(mp3list[i], saveLoc)
            print("\n")

    if downloadOne >= 0:
        print("Downloading: " + str(titles[int(downloadOne)].firstChild.nodeValue))
        saveLoc = os.path.dirname(os.path.realpath(__file__)) + "/" + titles[int(downloadOne)].firstChild.nodeValue + ".mp3"
        geturl(mp3list[int(downloadOne)], saveLoc)

    if downloadRangeStart > 0 and downloadRangeFinish > 0:
        for i in range(downloadRangeStart, downloadRangeFinish + 1):
            print("Downloading: " + str(titles[i].firstChild.nodeValue))
            saveLoc = os.path.dirname(os.path.realpath(__file__)) + "/" + titles[i].firstChild.nodeValue + ".mp3"
            geturl(mp3list[i], saveLoc)
            print("\n")

    if downloadNew:
        print("Downloading: " + str(titles[0].firstChild.nodeValue))
        saveLoc = os.path.dirname(os.path.realpath(__file__)) + "/" + titles[0].firstChild.nodeValue + ".mp3"
        geturl(mp3list[int(downloadOne)], saveLoc)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n')
        sys.exit(0)
