#! /usr/bin/env python3

import asyncio
import aiohttp
#import tqdm 
import lxml
import json
from bs4 import BeautifulSoup as BS 



class Main:
    sitemap_urls = [] #List of urls returned from gen_urls(). 
    article_urls = [] #Article urls extracted from sitemaps. 
    articles_missing_text = 0 #Need to skip articles without article text to avoid disruptive type errors.

    def gen_urls(self):
        """
        Generating sitemap urls for each month respectively between 2010 and 2020.  
        Will take a hardcoded base url as input and generate a set of urls as output.
        """ 
        base_url = 'https://www.theatlantic.com/sitemaps/sitemap_YEAR_MONTH.xml' #YEAR and MONTH are used as placeholders.  
        #Nested iteration for each month of each year.
        for y in range(2010,2021,1): #10 years 
            temp_url = base_url.replace('YEAR', str(y)) 
            for m in range(1,13): #12 months 
                #If the month is represented with a single digit, will need a 0 before single digit.  Example '01', 02',..'10',...
                if m <= 9:
                    new_url = temp_url.replace('MONTH', '0' + str(m)) 
                else: 
                    new_url = temp_url.replace('MONTH', str(m)) 
                self.sitemap_urls.append(new_url)
        return self.sitemap_urls

    async def fetch_url(self, session, url):
        """
        Fetch article urls extracted from sitemap xml files.
        Call coroutine crawl_url and pass in  article_url.
        """ 
        async with session.get(url) as response:
            text = await response.text() #Need await in context manager async with 
            #Parse xml file for article urls 
            xml_soup = BS(text, "lxml")
            self.article_urls.append(xml_soup.loc.string) #NOTE: Due to async tasks completing without order, article urls won't be sorted. 
            article_tasks = [self.crawl_url(session, article_url) for article_url in self.article_urls] #Create task for crawling article urls. 
            results = await asyncio.gather(*article_tasks) #Gather tasks to run as coroutines
            return results


    async def crawl_url(self, session, article_url):
        """
        Crawl article urls and extract datapoints.
        Serialize data.
        """ 
        articles_json = {"Title":[], "Author":[], "Date/Time Posted":[], "Article Text":[]} #All articles will be serialized prior to database storage.  
        article_text = [] #Article text extracted from a variable amount of <p> tags nested in seperate elements. 
        #Check url route to discern artcles from photos and videos  
        if ('/photo/' in article_url) or ('/video/' in article_url): 
            print(f"{article_url} displays media with inefficient amount of text")
            self.articles_missing_text += 1 #Will aid in calculating confidence (p-level) 
            return self.articles_missing_text 
        else:
            async with session.get(article_url) as response: #from article_urls
                html = await response.text()  
                soup = BS(html, "lxml") #Make the soup, parse html to extract article data points.
                
                #Selectors are dynamic (with exception to author), will change per request/render.  
                #Select via class containing desired text. 
            
                title = soup.select_one('h1[class^="ArticleHeader"]')

                print(title) 
                author = soup.find("address", {'id'='byline'})
                author = author.a 
                date_posted = soup.header.time.attrs['datetime']  #Data posted for sorting events to compare to financial data.
                
                #All text is in <p> tags some nested inside <blockqoutes within <section class="ArticleContent..."      
                text_container = soup.select_one('section[class^="ArticleContent"]') 
                if text_container.p:
                    for p in text_container.p:              #What if there are multiple blockquote
                        article_text.append(p.text) 
                    
                if text_container.blockquote:
                    for p in text_container.blockquote.p:
                        article_text.append(p.text) 

                #Prepare data for insert. Need to serialize data into JSON before inserting into mongodb database.
                #First create a dict 
                #Then serialize
                articles_dict["Title"].append(title)
                articles_dict["Author"].append(author)
                articles_dict["Date/Time Posted"].append(date_posted)
                articles_dict["Article Text"].append(article_text) 
                #In database_test.py code will save articles. This test soley concerns crawling article urls and extracting data points. 
                json_article = json.dumps(articles_dict)
                print(json_article) 
                return json_article 

    async def parse_url(self, session, url): 
        """
        Calls fetch_url. Gets document article link from sitemap url.
        """
        doc = await self.fetch_url(session, url)
        print("DOC: {}".format(doc, len(doc))) 
        return doc


    async def parse_urls(self, sitemap_urls, loop):
        """Initialize async calls.""" 
        async with aiohttp.ClientSession(loop=loop) as session:
            tasks = [self.parse_url(session, str(url)) for url in self.sitemap_urls] #Create tasks for getting article urls from sitemap_urls list. 
            responses = await asyncio.gather(*tasks) 
            return responses 

if __name__ == "__main__":
    #Will need to incorporate callback function to save articles to database/csv
    m = Main() 
    m.gen_urls() 
    loop = asyncio.get_event_loop()
    parsed_data = loop.run_until_complete(m.parse_urls(m.sitemap_urls, loop)) 
    print(parsed_data) 
    print("Scraped", int(len(self.article_urls)) - int(self.articles_missing_text), "out of", len(self.article_urls)) #Debugging..how many articles get skipped over?
