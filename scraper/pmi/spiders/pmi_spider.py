""" A spider to scrape the PMI certification registry. """

import logging
import uuid

import cfscrape
import scrapy
from pmi.items import PmiItem
from scrapy import Request
from scrapy.selector import Selector


class PMISpider(scrapy.Spider):
    
    # Define the name of the spider, which is used to run the spider
    name = 'pmi-spider'
    
    # Define the URLs to crawl
    # There is only a single URL in the PMI registry
    start_urls = ['http://www.pmi.org/certifications/certification-resources/registry']
    
    def __init__(self, country=None, page_limit=25000, **kwargs):
        
        # TODO - Remove once the country codes are added
        self.country_abbreviation = country.upper()
        self.page_limit =page_limit
        super().__init__(**kwargs)
    
    def start_requests(self):
        """This function is called before crawling starts.
        
        This function is used to set the cookies and headers for the request. This is necessary because the PMI registry
        """
        logging.info("Getting cookies and headers")
        # logging.info("User-Agent: %s", user_agent)
        for url in self.start_urls:
            token, agent = cfscrape.get_tokens(url = url, user_agent = '_')
            yield Request(url=url, cookies=token, headers={'User-Agent': agent}, callback=self.pagination)
            
            
    def pagination(self, response):
        """This function is called to inform the spider how many pages to crawl."""
        
        # TODO - Create a file containing all the county codes to iterate over
        ## for country in country_codes:

        # Define the form data to be submitted
        formdata={
            "FirstName": "",
            "LastName": "", 
            "Credential": "", 
            "Country": self.country_abbreviation
            }
        
        # Submit the form data to the registry
        form_data = scrapy.FormRequest.from_response(
            response = response,
            formxpath="//form[@action='/certifications/certification-resources/registry']",
            method = "POST",
            formdata = formdata,
            cookies = response.request.cookies,
            headers = response.request.headers,
            callback=self.parse_pages
            )
        
        yield form_data

    def parse_pages(self, response):
        """This function is called to parse the results from each page."""
        
        # Get the total number records returned from the search
        n_records = int(Selector(response=response)
                        .xpath("//div[text()[contains(., 'results for')]]/span[1]/text()")
                        .extract_first())
        
        # Get the number of pages to crawl
        pages = list(range(1, n_records // self.page_limit + 2))
        
        # Iterate over each page and parse the results
        for page in pages:
        
            # Define the form data to be submitted for the current page
            page_formdata = {
                "FirstName": "", 
                "LastName": "", 
                "Credential": "", 
                "Country": self.country_abbreviation, 
                "CurrentPage": str(page), 
                "PageLimit": str(self.page_limit)
                }
            
            # Submit the form data to the registry
            results = scrapy.FormRequest.from_response(
                response = response,
                formxpath="//form[@action='/certifications/certification-resources/registry']",
                method = "POST",
                formdata= page_formdata,
                cookies = response.request.cookies,
                headers = response.request.headers,
                callback=self.parse_table
                )
            
            yield results
        
    def parse_table(self, response):
        
        # Create a new PmiItem object
        item = PmiItem()
        
        # Get all the rows in the table
        rows = Selector(response=response).xpath('//div[@class="registryItemPanel"]')
        
        # Iterate over each row and store the item in a scrapy item
        for row in rows:
            
            # Extract the data from the row
            full_name = row.xpath('div/div[1]/span[1]/text()').extract_first()
            location = row.xpath('div/div[1]/span[2]/text()').extract_first()
            
            item['full_name'] = full_name
            item['location'] = location
            
            # Get the certifications and certification related data
            for certification in row.xpath("div/div[2]/div[contains(@class, 'certification-info-panel')]"):
                item['certification'] = certification.xpath('img/@alt').extract_first()
                item['year_earned'] = certification.xpath('span[2]/text()').extract_first()
                item['record_id'] = str(uuid.uuid4())

                yield item