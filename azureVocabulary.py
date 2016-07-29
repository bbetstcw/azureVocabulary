from keywordExtract import run
from markdown import markdown
from mdFileStructure import Article
import operator
import glob
import re

folders = [
    "articles/app-service-web/",
    "articles/automation/",
    "articles/hdinsight/",
    "articles/media-services/",
    "articles/redis-cache/",
    "articles/traffic-manager/",
    "articles/virtual-network/",
    "articles/active-directory/",
    "articles/batch/",
    "articles/cache/",
    "articles/cdn/",
    "articles/cloud-services/",
    "articles/event-hubs/",
    "articles/expressroute/",
    "articles/mobile-services/",
    "articles/scheduler/",
    "articles/service-bus/",
    "articles/site-recovery/",
    "articles/sql-database/",
    "articles/storage/",
    "articles/virtual-machines/",
    "articles/application-gateway/",
    "articles/backup/",
    "articles/notification-hubs/",
    "articles/"
  ]

path = "C:/Users/Administrator/Documents/GitHub/azure-content-pr/"
includeReg = r"(\[AZURE\.INCLUDE\s*\[.+\]\((../)+includes/(.+\.md)\)\])"
def getKeywordsUnion(filename, allKeywords):
    keywords = getKeywords(filename)
    for k,v in keywords.items():
        try:
            allKeywords[k] += v
        except KeyError:
            allKeywords[k] = v

def getKeywordsIntersection(filename, allKeywordSet):
    keywords = set(getKeywords(filename).keys())
    return allKeywordSet & keywords

def getKeywords(filename):
    print("processing: "+filename)
    file = open(filename,"r", encoding="utf8")
    md = file.read()
    includes = re.findall(includeReg, md)
    for include in includes:
        includeFile = open(path+"includes/"+include[2], "r", encoding="utf8")
        includeText = includeFile.read()
        includeFile.close()
        md = md.replace(include[0], includeText)
    html = markdown(md)
    file.close()
    article = Article(html)
    return article.getKeywords()

def getUnion():
    for folder in folders:
        fileList = glob.glob(path+folder+"/*.md")
        allKeywords = {}
        for filename in fileList:
            getKeywordsUnion(filename, allKeywords)
        sortedKeyword = [ tuple[0]+"\n" for tuple in sorted(allKeywords.items(), key=operator.itemgetter(1), reverse=True)]
        output = open("output/"+folder.replace("/","-")+".txt", "w", encoding="utf8")
        output.writelines(sortedKeyword)
        output.close()

def getIntersection():
    for folder in folders:
        fileList = glob.glob(path+folder+"/*.md")
        allKeywordSet = set(getKeywords(fileList[0]).keys())
        for filename in fileList[1:]:
            allKeywordSet = getKeywordsIntersection(filename, allKeywordSet)
        sortedKeyword = sorted(list(allKeywordSet))
        output = open("IntersectionOutput/"+folder.replace("/","-")+".txt", "w", encoding="utf8")
        output.writelines([term+"\n" for term in sortedKeyword])
        output.close()

getIntersection()