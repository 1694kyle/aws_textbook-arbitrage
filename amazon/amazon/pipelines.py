# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
from amazon import settings
import logging
# from scrapy.exporters import CsvItemExporter


class InitialPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        # spider.item_count += 1
        # if spider.item_count > 10:
        #     spider.close_down = True
        if item['asin'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['asin'])
            return item


class TradeEligiblePipeline(object):
    def process_item(self, item, spider):
        if item['trade_in_eligible']: # or item.get('chegg_trade_value') or item.get('buyback_trade_value'):
            if not item['trade_value'] == ' ': item['trade_value'] = float(item['trade_value'])
            return item
        else:
            raise DropItem('Not Trade Eligible: {}'.format(item['asin']))


class PricePipeline(object):
    def process_item(self, item, spider):
        prices = ['lowest_used_price1', 'lowest_used_price2', 'lowest_new_price1', 'lowest_new_price2']#, 'any_lowest_price']
        price_values = []
        for price in prices:
            try:
                price_values.append(float(item[price]))
            except:
                continue  # no price for price key
        if len(price_values) == 0:
            raise DropItem('\tNo Price: {}'.format(item['asin']))
        else:
            min_price = min(price_values)
            item['price'] = min_price
            return item


class ProfitablePipeline(object):
    def process_item(self, item, spider):
        profitable, item = check_profit(item)
        if profitable:
            print 'Profitable: {0}\n\tProfit - {1}\n\tCost - {2}\n\tROI - {3}'.format(item['asin'], item['profit'], item['price'], item['roi'])
            logging.error('Profitable: {0}\n\tProfit - {1}\n\tCost - {2}\n\tROI - {3}'.format(item['asin'], item['profit'], item['price'], item['roi']))
            return item
        else:
            raise DropItem('\tNot Profitable: {}'.format(item['asin']))


class LoggedProfitablePipeline(object):
    def __init__(self):
        self.logged_profitable_items = []

    def process_item(self, item, spider):
        if item['asin'] not in self.logged_profitable_items:
            self.logged_profitable_items.append(item['asin'])
            return item
        # elif item['asin'] in spider.logged_profitable_items:
        #     if spider.logged_profitable_items[item['asin']]['trade_value'] != item['trade_value']:
        #         spider.logged_profitable_items[item['asin']] = item  # updating item
        #         print 'Item Updated: {}'.format(item['asin'])
        #         return item
        #     else:
        #         raise DropItem('\tAlready Logged Profitable: {}'.format(item['asin']))
        else:
            raise DropItem('\tAlready Logged Profitable: {}'.format(item['asin']))


def check_profit(item):
    price = item['price']
    chegg_value = item.get('chegg_trade_value', 0)
    buyback_value = item.get('buyback_trade_value', 0)
    trade_value = item.get('trade_value', 0)
    max_trade = max(chegg_value, buyback_value, trade_value)
    # find trade link
    if chegg_value == max_trade:
        item['trade_link'] = item['chegg_trade_link']
    elif buyback_value == max_trade:
        item['trade_link'] = item['buyback_trade_link']
    else:
        item['trade_link'] = item['url']

    true_profit = (max_trade - price) - 3.99  # account for shipping
    if true_profit > 10:
        item['roi'] = '%{}'.format(round(true_profit / price * 100, 2))
        item['profit'] = '${}'.format(trade_value - price)
        item['profitable'] = True
        return True, item
    else:
        return False, item


class DynamoDBPipeline(object):
    # todo: get this set up. possible to store scraped items for quicker searching

    pass


class WriteItemPipeline(object):
    def process_item(self, item, spider):
        with open(settings.LOCAL_OUTPUT_FILE, 'a') as f:
            for field in settings.FEED_EXPORT_FIELDS:
                f.write('{},'.format(item[field]))
            f.write('\n')

# tood: look up each profitable item and see if desired seller available and what price
# todo: so desired_price, desired_profit, desired_roi