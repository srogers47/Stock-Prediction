#! /usr/bin/env python3


def gen_urls():
    """
    Test generating sitemap urls for each month respectively between 2010 and 2020.  
    Will take a hardcoded base url as input and generate a set of urls as output.
    """ 
    base_url = 'https://www.theatlantic.com/sitemaps/sitemap_YEAR_MONTH.xml' #YEAR and MONTH are used as placeholders.  
    sitemap_urls = [] 
    #Nested iteration 
    for y in range(2010,2021,1): #10 years 
        temp_url = base_url.replace('YEAR', str(y)) 

        for m in range(1,13): #12 months 
            #If the month is represented with a single digit, will need a 0 before single digit.  Example '01', 02',..'10',...
            if m <= 9:
                new_url = temp_url.replace('MONTH', '0' + str(m)) 
            else: 
                new_url = temp_url.replace('MONTH', str(m)) 

            sitemap_urls.append(new_url)
            print(new_url) 

if __name__=="__main__":
    gen_urls() 

    
            
            

       


