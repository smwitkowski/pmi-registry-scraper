# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PmiItem(scrapy.Item):
    # Define all the fields for the item here
    record_id = scrapy.Field()
    full_name = scrapy.Field()
    location = scrapy.Field()
    certification = scrapy.Field()
    year_earned = scrapy.Field()