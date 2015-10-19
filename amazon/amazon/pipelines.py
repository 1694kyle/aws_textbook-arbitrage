# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
from amazon import settings
import logging
from amazonproduct.api import API
from amazonproduct.errors import AWSError
import time

class InitialPipeline(object):
    # def __init__(self):
    #     self.ids_seen = set()

    def process_item(self, item, spider):
        # spider.item_count += 1
        # if spider.item_count > 10:
        #     spider.close_down = True
        if item['asin'] in spider.ids_seen:
            raise DropItem("Duplicate item found: {}" .format(item['asin']))
        else:
            spider.ids_seen.add(item['asin'])
            with open(settings.LOCAL_ITEM_LOG, 'a') as f:
                f.write('{}\n'.format(item['asin']))
            return item


class PricePipeline(object):
    def process_item(self, item, spider):
        if len(spider.running_items) > 8:
            items = get_price_data(spider.running_items)
            spider.running_items = []
            for item in items:
                return item
        else:
            raise DropItem()


class TradeEligiblePipeline(object):
    def process_item(self, item, spider):
        if item['trade_in_eligible']:
            return item
        else:
            raise DropItem('Not Trade Eligible: {}'.format(item['asin']))


class ProfitablePipeline(object):
    def process_item(self, item, spider):
        profitable, item = check_profit(item)
        if profitable:
            try:
                logging.error('Profitable: {0}\n\tProfit - {1}\n\tCost - {2}\n\tROI - {3}'.format(item['asin'], item['profit'], item['price'], item['roi']))
            except:
                pass
            return item
        else:
            raise DropItem('\tNot Profitable: {}'.format(item['asin']))


class DynamoDBPipeline(object):
    # todo: get this set up. possible to store scraped items for quicker searching
    def process_item(self, item, spider):
        return item


class WriteItemPipeline(object):
    def process_item(self, item, spider):
        with open(settings.LOCAL_OUTPUT_FILE, 'a') as f:
            for field in settings.FEED_EXPORT_FIELDS:
                f.write('{},'.format(item[field]))
            f.write('\n')


def check_profit(item):
    price = item['price']
    chegg_value = item.get('chegg_trade_value', 0)
    buyback_value = item.get('buyback_trade_value', 0)
    trade_value = item.get('trade_value', 0)
    max_trade = max(chegg_value, buyback_value, trade_value)
    # find trade link
    # if chegg_value == max_trade:
    #     item['trade_link'] = item['chegg_trade_link']
    # elif buyback_value == max_trade:
    #     item['trade_link'] = item['buyback_trade_link']
    # else:
    #     item['trade_link'] = item['url']

    true_profit = (max_trade - price) - 3.99  # account for shipping
    if true_profit > 10:
        item['roi'] = '%{}'.format(round(true_profit / price * 100, 2))
        item['profit'] = '${}'.format(trade_value - price)
        item['profitable'] = True
        return True, item
    else:
        return False, item


def get_price_data(items):
        asins = [k for k, v in items.iteritems()]
        response = amzn_search(asins)
        for item in response.Items.Item:
            asin = item.ASIN
            Item = items[asin]
            if hasattr(item.ItemAttributes, 'IsEligibleForTradeIn'):
                print 'Eligible: {}'.format(asin)
                Item['trade_in_eligible'] = bool(item.ItemAttributes.IsEligibleForTradeIn)
                Item['trade_value'] = item.ItemAttributes.TradeInValue.Amount / 100.0
                Item['lowest_used_price'] = item.OfferSummary.LowestUsedPrice.Amount / 100.0
                Item['lowest_new_price'] = item.OfferSummary.LowestNewPrice.Amount / 100.0
            else:
                Item['trade_in_eligible'] = False
                continue
        return items


def amzn_search(asins):
    api = API(locale='us')
    response = _get_amzn_response(asins, api)
    if not response:
        return None
    else:
        return response


def _get_amzn_response(asins, api):
    query = 'response = api.item_lookup(",".join(asins), ResponseGroup="Large")'
    err_count = 0
    while True:
        try:
            exec(query)
            return response

        except AWSError, e:
            err_count += 1
            print 'AWS Error: {}'.format(e.code)
            if err_count > 5:
                return None
            time.sleep(2)
            continue








# todo: look up each profitable item and see if desired seller available and what price
# todo: so desired_price, desired_profit, desired_roi