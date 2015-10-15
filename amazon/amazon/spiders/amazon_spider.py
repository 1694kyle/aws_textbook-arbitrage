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

def load_xpaths():
    xpaths = {
        'title': '//span[@id="productTitle"]/text()',
        'asin': '',
        'any_lowest_price': '//span[contains(@class, "price") and contains(text(), "$")]/text()[1]',
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
    allowed_domains = [r'www.amazon.com', r'buyback.abebooks.com', r'www.buybacktextbooks.com', r'www.chegg.com']
    start_urls = [
        r'http://www.amazon.com/New-Used-Textbooks-Books/b?node=465600'
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5})'
    }
    rules = (
        # inidividual item pages
        Rule(
            LinkExtractor(allow=('.+\/dp\/(\w*\d*)\/?',),), # restrict_xpaths=['//div[contains(@id, "result_")]']
            callback="parse_amzn_item_page",
            ),
        # category refinement and next pages
        Rule(
            LinkExtractor(allow=('.*amazon\.com\/s.*',), restrict_xpaths=['//div[@class="categoryRefinementsSection"]/ul/li/a', '//a[@id="pagnNextLink"]']),
            follow=True,
            ),
    )

    def __init__(self, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.name = 'amazon'
        self.item_xpaths = load_xpaths()
        self.logged_profitable_items = {}
        self.close_down = False
        self.item_count = 0

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

        try:  # todo: LinkExtractor pulling some denied site. Don't know why
            item['asin'] = re.search('.*\/dp\/([\w\d]+)\/?.*', response.url).group(1)
            # print item['asin']
            # print item['url']
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
