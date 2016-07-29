import re
import nltk
from bs4 import BeautifulSoup
from bs4 import NavigableString, Comment, Doctype
from keywordExtract import run

sentenceTokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
titleMul = 5.0
descriptionMul = 5.0
openingMul = 2.5
childMul = 0.5
endingMul = 2.0

class ArticleNode(object):
    """
    the super class
    """
    def __init__(self, parent, children, html):
        self.parent = parent
        self.children = children
        self.html = html
        self.keywords = None

    def getKeywords(self):
        if self.keywords == None:
            childrenKeywordLists = [child.getKeywords() for child in self.children if len(child.getKeywords()) > 0]
            self.keywords = {}
            for li in childrenKeywordLists:
                for k,v in li.items():
                    try:
                        self.keywords[k] += v
                    except KeyError:
                        self.keywords[k] = v
        return self.keywords

class Article(ArticleNode):
    tagsReg = r"(\<p\>\s*\<tags\s*\n?(\s*\w+\..+\n?)+\s*/\>\s*\</p\>)"
    def __init__(self, html):
        soup = BeautifulSoup(html,"html.parser")
        self.opening = []
        try:
            self.title = Sentence(self,soup.properties["pagetitle"])
        except (TypeError, KeyError):
            self.title = ArticleNode(self, [], "")
        try:
            self.description = Sentence(self,soup.properties["description"])
        except (TypeError, KeyError):
            self.description = ArticleNode(self, [], "")
        hasHead = False
        for i in range(1,7):
            if len(soup.find_all("h"+str(i))) != 0:
                children = self.__contentInit(soup, html, i)
                hasHead = True
                break
        if not hasHead:
            opening = [structuralize(self, str(p).strip()) for p in soup.contents if str(p).strip()!=""]
            self.opening = []
            children = []
            for o in opening:
                if len(o) > 0:
                    children.extend(o)
        return super().__init__(None, children, html)

    def __contentInit(self, soup, html, headNum):
        block_titles = soup.find_all("h"+str(headNum))
        tags = re.findall(Article.tagsReg, html)
        if len(tags) == 0:
            beginIndex = 0
        else:
            beginIndex = html.find(tags[0][0])+len(tags[0][0])
        endIndex = html.find("<h"+str(headNum))
        self.opening = structuralize(self, html[beginIndex:endIndex].strip())
        beginIndex = endIndex
        endIndex = html[beginIndex+3:].find("<h"+str(headNum))
        children = []
        while endIndex != -1:
            block = Block(self, html[beginIndex:beginIndex+endIndex+3].strip(), headNum)
            children.append(block)
            beginIndex += endIndex+3
            endIndex = html[beginIndex+3:].find("<h"+str(headNum))
        block = Block(self, html[beginIndex:].strip(), headNum)
        children.append(block)
        return children

    def getKeywords(self):
        if self.keywords == None:
            titleKeys = self.title.getKeywords()
            for key in titleKeys.keys():
                titleKeys[key] = titleKeys[key]*titleMul
            descriptionKeys = self.description.getKeywords()
            for key in descriptionKeys.keys():
                descriptionKeys[key] = descriptionKeys[key]*descriptionMul
            openingKeysList = [a.getKeywords() for a in self.opening if len(a.getKeywords())>0]
            openingKeys = {}
            for li in openingKeysList:
                for k,v in li.items():
                    try:
                        openingKeys[k] += v*openingMul
                    except KeyError:
                        openingKeys[k] = v*openingMul
            childrenKeys = super().getKeywords()
            for key in childrenKeys.keys():
                childrenKeys[key] = childrenKeys[key]*childMul
            keysList = []
            if len(titleKeys) > 0:
                keysList.append(titleKeys)
            if len(descriptionKeys) > 0:
                keysList.append(descriptionKeys)
            if len(openingKeysList) > 0:
                keysList.append(openingKeys)
            if len(childrenKeys) > 0:
                keysList.append(childrenKeys)
            self.keywords = {}
            for list in keysList:
                for k,v in list.items():
                    try:
                        self.keywords[k] += v
                    except KeyError:
                        self.keywords[k] = v
        return self.keywords

class Block(ArticleNode):
    def __init__(self, parent, html, headNum):
        soup = BeautifulSoup(html,"html.parser")
        self.title = Sentence(self, "".join([str(x).strip() for x in soup.find_all("h"+str(headNum))[0].contents]))
        self.opening = []
        hasHead = False
        for i in range(headNum+1,7):
            if len(soup.find_all("h"+str(i))) != 0:
                children = self.__contentInit(soup, html, i, headNum)
                self.ending = []
                hasHead = True
                break
        if not hasHead:
            olIndex = html.find("<ol")
            ulIndex = html.find("<ul")
            if olIndex == -1 and ulIndex == -1:
                opening = [structuralize(self, str(p).strip()) for p in soup.contents if str(p).strip()!=""]
                self.opening = []
                children = []
                for o in opening:
                    if len(o) > 0:
                        children.extend(o)
                self.ending = []
            else:
                self.opening = []
                children = []
                self.ending = []
                olCount = len(soup.find_all("ol"))
                ulCount = len(soup.find_all("ul"))
                addTo = self.opening
                listCount = 0
                for p in soup.contents:
                    if type(p) != Doctype and type(p) != NavigableString and type(p) != Comment and "".join([str(x).strip() for x in p.contents])!="":
                        if p.name == "h"+str(headNum):
                            continue
                        elif p.name == "ol":
                            addTo = children
                            listCount += 1 + len(p.find_all("ol")) + len(p.find_all("ul"))
                        elif p.name == "ul":
                            addTo = children
                            listCount += 1 + len(p.find_all("ol")) + len(p.find_all("ul"))
                        elif len(p.find_all("ol")) != 0 or len(p.find_all("ul")) != 0:
                            addTo = children
                            listCount += len(p.find_all("ol")) + len(p.find_all("ul"))
                        addTo.extend(structuralize(self, str(p)))
                        if listCount >= olCount+ulCount:
                            addTo = self.ending
        return super().__init__(parent, children, html)

    def __contentInit(self, soup, html, headNum, parentHeadNum):
        block_titles = soup.find_all("h"+str(headNum))
        beginIndex = html.find("</h"+str(parentHeadNum)+">")+5
        endIndex = html.find("<h"+str(headNum))
        self.opening = structuralize(self, html[beginIndex:endIndex].strip())
        beginIndex = endIndex
        endIndex = html[beginIndex+3:].find("<h"+str(headNum))
        children = []
        while endIndex != -1:
            children.append(Block(self, html[beginIndex:beginIndex+endIndex+3].strip(), headNum))
            beginIndex += endIndex+3
            endIndex = html[beginIndex+3:].find("<h"+str(headNum))
        children.append(Block(self, html[beginIndex:].strip(), headNum))
        return children

    def getKeywords(self):
        if self.keywords == None:
            titleKeys = self.title.getKeywords()
            for key in titleKeys.keys():
                titleKeys[key] = titleKeys[key]*titleMul
            openingKeysList = [a.getKeywords() for a in self.opening if len(a.getKeywords())>0]
            openingKeys = {}
            for li in openingKeysList:
                for k,v in li.items():
                    try:
                        openingKeys[k] += v*openingMul
                    except KeyError:
                        openingKeys[k] = v*openingMul
            childrenKeys = super().getKeywords()
            for key in childrenKeys.keys():
                childrenKeys[key] = childrenKeys[key]*childMul
            endingKeysList = [a.getKeywords() for a in self.ending if len(a.getKeywords())>0]
            endingKeys = {}
            for li in endingKeysList:
                for k,v in li.items():
                    try:
                        endingKeys[k] += v*endingMul
                    except KeyError:
                        endingKeys[k] = v*endingMul
            keysList = []
            if len(titleKeys) > 0:
                keysList.append(titleKeys)
            if len(openingKeysList) > 0:
                keysList.append(openingKeys)
            if len(childrenKeys) > 0:
                keysList.append(childrenKeys)
            if len(endingKeysList) > 0:
                keysList.append(endingKeys)
            self.keywords = {}
            for list in keysList:
                for k,v in list.items():
                    try:
                        self.keywords[k] += v
                    except KeyError:
                        self.keywords[k] = v
        return self.keywords

class Steps(ArticleNode):
    def __init__(self, parent, html):
        soup = BeautifulSoup(html, "html.parser")
        children = [ListItem(self, "".join([str(x).strip() for x in li.contents])) for li in soup.find_all("li")]
        return super().__init__(parent, children, html)

class UnorderList(ArticleNode):
    def __init__(self, parent, html):
        soup = BeautifulSoup(html, "html.parser")
        children = [ListItem(self, "".join([str(x).strip() for x in li.contents])) for li in soup.find_all("li")]
        return super().__init__(parent, children, html)

class ListItem(ArticleNode):
    def __init__(self, parent, html):
        soup = BeautifulSoup(html, "html.parser")
        if len(soup.find_all("p")) > 0 or len(soup.find_all("ul")) > 0 or len(soup.find_all("ol")) > 0:
            children = structuralize(self, html)
        else:
            children = [Sentence(self, sentence) for sentence in sentenceTokenizer.tokenize(html)]
        return super().__init__(parent, children, html)

class BlockQuote(ArticleNode):
    def __init__(self, parent, html):
        soup = BeautifulSoup(html, "html.parser")
        if len(soup.find_all("p")) > 1 or len(soup.find_all("ul")) > 0 or len(soup.find_all("ol")) > 0:
            children = structuralize(self, html)
        else:
            children = [Paragraph(self, "".join([str(x).strip() for x in soup.p.contents]))]
        return super().__init__(parent, children, html)

class Paragraph(ArticleNode):
    def __init__(self, parent, html):
        if html.count("|")>=4:
            table = "<table>\n"
            lines = html.split("\n")
            for line in lines:
                line = line.strip()
                if line[0] == "|":
                    line = line[1:]
                if line[len(line)-1] == "|":
                    line = line[:len(line)-1]
                tds = line.split("|")
                tr = "<tr>"
                for td in tds:
                    tr += "<td> "+td+"</td>"
                tr += "</tr>"
                table += tr
            html = table+"</table>"
        soup = BeautifulSoup(html, "html.parser")
        if len(soup.find_all("table")) > 0 or len(soup.find_all("ul")) > 0 or len(soup.find_all("ol")) > 0:
            children = structuralize(self, html)
        else:
            sent = sentenceTokenizer.tokenize(html)
            children = [Sentence(self, sentence) for sentence in sent]
        return super().__init__(parent, children, html)

class Table(ArticleNode):
    def __init__(self, parent, html):
        soup = BeautifulSoup(html, "html.parser")
        children = []
        for tr in soup.contents:
             if "".join([str(x).strip() for x in tr.contents])!="":
                children.append(Sentence(self, tr.get_text("; ", strip=True)))
        return super().__init__(parent, children, html)

class Sentence(ArticleNode):
    def __init__(self, parent, html):
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        if text != "":
            self.terms = run(text)
        else:
            self.terms = {}
        return super().__init__(parent, [], html)

    def getKeywords(self):
        return self.terms

class Code(ArticleNode):
    def __init__(self, parent, html):
        return super().__init__(parent, [], html)

    def getKeywords(self):
        return {}

def structuralize(parent, html):
    soup = BeautifulSoup(html, "html.parser")
    l = len(soup.contents)
    if l == 0:
        return []
    elif l == 1:
        if soup.contents[0].name == "ol":
            return [Steps(parent, "".join([str(x).strip() for x in soup.ol.contents]))]
        elif soup.contents[0].name == "ul":
            return [UnorderList(parent, "".join([str(x).strip() for x in soup.ul.contents]))]
        elif soup.contents[0].name == "li":
            return [ListItem(parent, "".join([str(x).strip() for x in soup.li.contents]))]
        elif soup.contents[0].name == "p":
            return [Paragraph(parent, "".join([str(x).strip() for x in soup.p.contents]))]
        elif soup.contents[0].name == "table":
            return [Table(parent, "".join([str(x).strip() for x in soup.table.contents]))]
        elif soup.contents[0].name == "pre":
            return [Code(parent, "".join([str(x).strip() for x in soup.pre.contents]))]
        elif soup.contents[0].name == "blockquote":
            return [BlockQuote(parent, "".join([str(x).strip() for x in soup.blockquote.contents]))]
        else:
            return [Sentence(parent, html)]
    else:
        part = Article(html)
        part.opening.extend(part.children)
        return part.opening


