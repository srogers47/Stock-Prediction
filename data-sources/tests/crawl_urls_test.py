#! /usr/bin/env python3

import asyncio
import aiohttp
import tqdm 
import lxml
import json
from bs4 import BeautifulSoup as BS 
import re 


class Main:
    sitemap_urls = [] #List of urls returned from gen_urls(). 
    article_urls = [] #Article urls extracted from sitemaps. 

    def gen_urls(self):
        """
        Generating sitemap urls for each month respectively between 2010 and 2020.  
        Will take a hardcoded base url as input and generate a set of urls as output.
        """ 
        base_url = 'https://www.theatlantic.com/sitemaps/sitemap_YEAR_MONTH.xml' #YEAR and MONTH are used as placeholders.  
        #Nested iteration 
        for y in range(2010,2021,1): #10 years 
            temp_url = base_url.replace('YEAR', str(y)) 
            for m in range(1,13): #12 months 
                #If the month is represented with a single digit, will need a 0 before single digit.  Example '01', 02',..'10',...
                if m <= 9:
                    new_url = temp_url.replace('MONTH', '0' + str(m)) 
                else: 
                    new_url = temp_url.replace('MONTH', str(m)) 
                self.sitemap_urls.append(new_url)
                print(new_url) 
        return self.sitemap_urls

    async def fetch_url(self, session, url):
        """
        Fetch article urls extracted from sitemap xml files.
        Call coroutine crawl_url and pass in  article_url.
        """ 
        async with session.get(url) as response:
            text = await response.text() #Need await in context manager async with 
            #print("URL: {} - TEXT:I {}".format(url, len(text)))
            #Parse xml file for article urls 
            xml_soup = BS(text, "lxml")
            self.article_urls.append(xml_soup.loc.string) #NOTE: Due to async tasks completing without order, article urls won't be sorted. 
            article_tasks = [self.crawl_url(session, article_url) for article_url in self.article_urls] #Create task for crawling article urls. 
            results = await asyncio.gather(*article_tasks) #Gather tasks to run as coroutines
            return results


    async def crawl_url(self, session, article_url):
        """Crawl article urls and extract text/html.""" 
        print(article_url) 
        async with session.get(article_url) as response: #from article_urls
            html = await response.text() 
            print("THIS IS HTML ", html) 
            soup = BS(html, "html.parser") #Make the soup, parse html to extract article data points.
            #Selectors are dynamic (with exception to author), will change periodically.  
            #Select via class containing desired text. 
            content = soup.main.article
            print("THIS IS CONTENT",content) 

            ###REGULAR EXPRESSIONS with css selectors 

            title = content.select_one("h1[class^='ArticleTitle']").string
            author = content.select_one("address[id='byline']") #Locate via id, NOT regex
            author = author.a.string #Author nested in <a tag text
            article_text = content.select_one("p[class^='ArticleParagraph']").string #All article text.
            date_posted = content.select_one("time[class^='ArticleTimestamp']").attrs  #Data posted for sorting events to compare to financial data.


            #NOTE: Prepare data for insert. Need to serialize data into JSON before inserting into mongodb database.
            #First create a dict 
            temp_dict = {
                    "Title":title,
                    "Author":author,
                    "Text":article_text, #NOTE: DEBUG. Text in json is "null"? Fix extraction 
                    "Date/time":str(date_posted) #Should i specify string? 
                    } 
            #Then serialize
            json_article = json.dumps(temp_dict) 
            print(json_article) 
            return json_article 

        #NOTE:Next test will look at async placement of json into non-relational database --> async_data_storage.py 



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
            #responses = [await f for f in tqdm.tqdm(asyncio.as_completed(tasks), total = len(tasks))] 
            return responses 

if __name__ == "__main__":
    #Will need to incorporate callback function to save articles to database/csv
    m = Main() 
    m.gen_urls() 
    loop = asyncio.get_event_loop()
    parsed_data = loop.run_until_complete(m.parse_urls(m.sitemap_urls, loop)) 
    print(m.article_urls) #NOTE: Debugging 
    print(parsed_data) 
