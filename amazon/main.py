from scrapy.crawler import CrawlerProcess
from amazon.spiders.amazon_spider import AmazonSpider


from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())

process.crawl(AmazonSpider)
process.start()
