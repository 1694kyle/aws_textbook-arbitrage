from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider, Request, Rule, CrawlSpider
from datetime import datetime
from scrapy.selector import Selector
from amazon.items import AmazonItem
import pdb
import re
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy.exceptions import CloseSpider
import logging

def load_xpaths():
    xpaths = {
        'title': '//span[@id="productTitle"]/text()',
        'asin': '',
        # 'any_lowest_price': '//span[contains(@class, "price") and contains(text(), "$")]/text()[1]',
        'lowest_used_price1': '//a[contains(text(),"Used")]/text()[2]',
        'lowest_new_price1': '//a[contains(text(),"New")]/text()[2]',
        'lowest_used_price2': '//span[a[contains(text(),"Used")]]/span/text()',
        'lowest_new_price2': '//span[a[contains(text(),"New")]]/span/text()',
        'trade_in_eligible': ' ',
        'trade_value': '//span[@id="tradeInButton_tradeInValue"]/text()',
        'url': ' ',
        'price': ' ',
        'profit': ' ',
        'profitable': ' ',
        'roi': ' ',
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
            logging.error('Searching {} section with {} subsections'.format(category, int(float(li_count)) - 3))
            self.visited_categories.append(category)

        yield Request(response.url)


    def parse_amzn_item_page(self, response):
        if self.close_down:
            raise CloseSpider(reason='API usage exceeded')
        regex_title = re.compile(r'http://www.amazon.com/(.+)/dp.*')
        sel = Selector(response)
        item = AmazonItem()
        for name, path in self.item_xpaths.iteritems():
            try:
                item[name] = sel.xpath(path).extract()[0].strip().replace(',', '').replace('$', '')
            except (KeyError, IndexError, ValueError):
                item[name] = ' '

        item['url'] = response.url
        # if '-' in item['any_lowest_price']: item['any_lowest_price'] = item['any_lowest_price'][:item['any_lowest_price'].index(' -')]

        try:  # todo: LinkExtractor pulling some denied site. Don't know why
            item['asin'] = re.search('.*\/dp\/([\w\d]+).*', response.url).group(1)
        except:
            yield None

        if item['title'] == ' ':
            try:
                item['title'] = regex_title.match(response.url).groups()[0].replace('-', ' ')
            except:
                pass

        if not item['trade_value'] == ' ':
            item['trade_in_eligible'] = True
        else:
            item['trade_in_eligible'] = False

        ### check other trade sites ###
        #todo: work on these later
        # if item['isbn13'] != ' ':
        #     buyback_url = build_buyback_link(item['isbn13'].replace('-', ''))
        #     chegg_url = build_chegg_link(item['isbn13'].replace('-', ''))
        # elif item['isbn10'] != ' ':
        #     buyback_url = build_buyback_link(item['isbn10'].replace('-', ''))
        #     chegg_url = build_chegg_link(item['isbn10'].replace('-', ''))
        # else:
        #     buyback_url = None
        #     chegg_url = None
        # if buyback_url: yield Request(buyback_url, callback=self.parse_buyback_item_page, meta={'item': item})
        # if chegg_url: yield Request(chegg_url, callback=self.parse_chegg_item_page, meta={'item': item})
        yield item

    def parse_buyback_item_page(self, response):
        item = response.meta['item']
        sel = Selector(response)
        trade_value = float(sel.xpath('//div[@class="shipping"]/ul/li[1]/td[3]/span/text()').extract()[0].replace('$', ''))  # todo: can't drill-down to price
        item['buyback_trade_value'] = trade_value
        item['buyback_trade_link'] = response.url
        yield item

    def parse_chegg_item_page(self, response):
        sel = Selector(response)
        item = response.meta['item']
        chegg_trade_value = float(sel.xpath('//div[@class="amex-price"]/div/text()').extract()[0].replace('$', ''))
        item['chegg_trade_value'] = chegg_trade_value
        item['chegg_trade_link'] = response.url
        yield item
