#! /usr/bin/env python3

import asyncio
import aiohttp
import tqdm 

###Use tidy for pretty print xml: ./testasync... | tidy -xml > testasync_output.xml 
###Creates an xml file of all article links 

async def fetch_url(session, url):
    """testing aiohttp async function. Sitemap urls should be generated, not hardcoded.""" 
    async with session.get(url) as response:
        text = await response.text() #Need await in context manager async with 
        print("URL: {} - TEXT: {}".format(url, len(text)))
        return text

async def parse_url(session, url):
    """
    Calls fetch_url. Gets document(text) from url test. 
    See async_sitemap_crawl.py for article traversial via sitemap.
    """
    doc = await fetch_url(session, url)
    print("DOC: {}".format(doc, len(doc)))
    return doc

async def parse_urls(urls, loop):
    """Initialize async calls, track with progress bar.  Use gather for url gen iteration.""" 
    async with aiohttp.ClientSession(loop=loop) as session:
        tasks = [parse_url(session, url) for url in urls]
        #tqdm is a progress bar module that will be used in production env. 
        responses = [await f for f in tqdm.tqdm(asyncio.as_completed(tasks), total = len(tasks))] 
        return responses 

if __name__ == "__main__":
    #Temp location for hardcoded urls.  See sitemap_url_gen.py
    #Will need to incorporate callback function to save articles to database/csv
    urls = ['https://www.theatlantic.com/sitemaps/sitemap_2010_01.xml',
            'https://www.theatlantic.com/sitemaps/sitemap_2010_02.xml', 
            'https://www.theatlantic.com/sitemaps/sitemap-2010-03.xml',
            'https://www.theatlantic.com/sitemaps/sitemap-2010-04.xml'] 
    #Good for example.  Use gather() for multiple tasks with iterable. 
    loop = asyncio.get_event_loop()
    parsed_data = loop.run_until_complete(parse_urls( urls, loop)) 
    print(parsed_data) 
