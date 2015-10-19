from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider, Request, Rule, CrawlSpider
from datetime import datetime
from scrapy.selector import Selector
from amazon.items import AmazonItem
from amazon import settings
import pdb
import re
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy.exceptions import CloseSpider
import logging
from amazonproduct.api import API
from amazonproduct.errors import AWSError
import time

def load_xpaths():
    xpaths = {
        'title': '//span[@id="productTitle"]/text()',
        'asin': '',
        'isbn10': '//div[@id="isbn_feature_div"]/div/div[2]/span[2]/text()',
        'isbn13': '//div[@id="isbn_feature_div"]/div/div[1]/span[2]/text()',
    }

    return xpaths


def build_amzn_link(domain_suffix):
    return 'https://www.amazon.com{}'.format(domain_suffix)


def build_abe_link(isbn):
    return 'http://buyback.abebooks.com/cart.aspx?a=add&i={}|0|3&c={}&st=-1'.format(isbn)


def build_chegg_link(isbn):
    return 'https://www.chegg.com/sell-textbooks/search?buyback_search={}'.format(isbn)


def build_buyback_link(isbn):
    return r'http://www.buybacktextbooks.com/compare/{}'.format(isbn)


class AmazonSpider(CrawlSpider):
    name = 'amazon'
    allowed_domains = [r'www.amazon.com'] #, r'buyback.abebooks.com', r'www.buybacktextbooks.com', r'www.chegg.com']
    start_urls = [
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_0?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468220&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_1?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468226&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_2?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468204&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_3?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468224&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_4?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468212&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_5?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468206&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_6?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468222&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_7?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468228&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_8?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A684283011&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_9?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468216&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_10?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A468214&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600',
        r'http://www.amazon.com/s/ref=lp_465600_nr_n_11?fst=as%3Aoff&rh=n%3A283155%2Cn%3A%212349030011%2Cn%3A465600%2Cn%3A684300011&bbn=465600&ie=UTF8&qid=1444928100&rnid=465600'
    ]

    rules = (
        # inidividual item pages
        Rule(
            LinkExtractor(
                allow=('.+\/dp\/([\w\d]*).*s=books.*',),
                restrict_xpaths=['//li[contains(@id, "result_")]'],
            ),
            callback="parse_amzn_item_page",
            ),
        # category refinement and next pages
        Rule(
            LinkExtractor(
                allow=('.*amazon\.com\/s.*',),
                restrict_xpaths=['//div[@class="categoryRefinementsSection"]/ul/li/a', '//a[@id="pagnNextLink"]']),
            follow=True,
            callback='parse_result_page'
            ),

    )

    # todo: try parse_search_page and yield requests for item pages. Not sure why crawling tons of pages with no items

    def __init__(self, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.name = 'amazon'
        self.item_xpaths = load_xpaths()
        self.logged_profitable_items = {}
        self.close_down = False
        self.item_count = 0
        self.ids_seen = set()
        self.visited_categories = []
        self.running_items = {}

    def parse_result_page(self, response):
        sel = Selector(response)
        li_count = sel.xpath('count(//div[@class="categoryRefinementsSection"]/ul//li)').extract()[0]
        category_xpath = '//div[@class="categoryRefinementsSection"]/ul/li[strong]/strong/text()'

        try:
            category = sel.xpath(category_xpath).extract()[0]
        except:
            category = 'Not Found'

        if category in self.visited_categories:
            pass
        else:
            logging.info('Searching {} section with {} subsections'.format(category, int(float(li_count)) - 3))
            self.visited_categories.append(category)

        yield Request(response.url)

    def parse_amzn_item_page(self, response):
        if self.close_down:
            raise CloseSpider(reason='API usage exceeded')
        regex_title = re.compile(r'http:\/\/www.amazon.com\/(.+)\/dp.*')
        sel = Selector(response)
        item = AmazonItem()
        for name, path in self.item_xpaths.iteritems():
            try:
                item[name] = sel.xpath(path).extract()[0].strip().replace(',', '')
            except (KeyError, IndexError, ValueError):
                item[name] = ' '

        item['url'] = response.url

        try:  # todo: LinkExtractor pulling some denied site. Don't know why
            item['asin'] = re.search('.+\/dp\/([\w\d]*).*s=books.*', response.url).group(1)
        except:
            yield None

        if item['title'] == ' ':
            try:
                item['title'] = regex_title.match(response.url).groups()[0].replace('-', ' ')
            except:
                pass

        self.running_items[item['asin']] = item
        yield item

        # if len(self.running_items) > 2:
        #     self.get_price_data(self.running_items)

    # def get_price_data(self, items):
    #         asins = [item.get('asin') for item in self.running_items]
    #         response = amzn_search(asins)
    #         for item in response.Items.Item:
    #             asin = item.ASIN
    #             if hasattr(item.ItemAttributes, 'IsEligibleForTradeIn'):
    #                 Item = self.running_items[asin]
    #                 print 'Eligible: {}'.format(item.ASIN)
    #                 Item['trade_in_eligible'] = item.ItemAttributes.IsEligibleForTradeIn
    #                 Item['trade_value'] = item.ItemAttributes.TradeInValue.Amount / 100
    #                 Item['lowest_used_price'] = item.OfferSummary.LowestUsedPrice.Amount / 100
    #                 Item['lowest_new_price'] = item.OfferSummary.LowestNewPrice.Amount / 100
    #                 yield item
    #             else:
    #                 continue
    #             self.running_items = []



# def amzn_search(asins):
#     api = API(locale='us')
#     response = _get_amzn_response(asins, api)
#     if not response:
#         return None
#     else:
#         return response
#
#
# def _get_amzn_response(asins, api):
#     query = 'response = api.item_lookup(",".join(asins), ResponseGroup="Large")'
#     err_count = 0
#     while True:
#         try:
#             exec(query)
#             return response
#
#         except AWSError, e:
#             err_count += 1
#             print 'AWS Error: {}'.format(e.code)
#             if err_count > 5:
#                 return None
#             time.sleep(2)
#             continue
