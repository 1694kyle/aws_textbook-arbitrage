# -*- coding: utf-8 -*-

# Scrapy settings for amazon project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

import os
import datetime
date = datetime.datetime.today().date().strftime('%m-%d-%Y')

BOT_NAME = 'amazon'

SPIDER_MODULES = ['amazon.spiders']
NEWSPIDER_MODULE = 'amazon.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS =16

CONCURRENT_ITEMS = 200

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 0

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP=16

# Disable cookies (enabled by default)
#COOKIES_ENABLED=False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED=False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en',
  # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
}

DEPTH_LIMIT = 500
# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'amazon.middlewares.MyCustomSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'amazon.middlewares.MyCustomDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'amazon.pipelines.SomePipeline': 300,

ITEM_PIPELINES = {
    'amazon.pipelines.InitialPipeline': 100,
    'amazon.pipelines.PricePipeline': 200,
    'amazon.pipelines.TradeEligiblePipeline': 300,
    'amazon.pipelines.ProfitablePipeline': 400,
    # 'amazon.pipelines.LoggedProfitablePipeline': 600,
    # 'amazon.pipelines.WriteItemPipeline': 700,
    # 'amazon.pipelines.DynamoDBPipeline': 800,
}

item_count = 1

OUTPUT_BUCKET = 'textbook-arbitrage'
LOG_FOLDER = OUTPUT_BUCKET + '/scraping_logs'
RESULT_FOLDER = OUTPUT_BUCKET + '/scraping_results'

LOCAL_OUTPUT_DIR = os.path.join(os.environ.get('HOME'), 'Desktop', 'Scraping Results')
LOCAL_OUTPUT_FILE = os.path.join(LOCAL_OUTPUT_DIR, 'Results/results {}'.format(date))
LOCAL_ITEM_LOG = os.path.join(LOCAL_OUTPUT_DIR, 'Items/items {}'.format(date))
if not os.path.isdir(os.path.join(LOCAL_OUTPUT_DIR, 'Results')): os.makedirs(os.path.join(LOCAL_OUTPUT_DIR, 'Results'))
if not os.path.isdir(os.path.join(LOCAL_OUTPUT_DIR, 'Items')): os.makedirs(os.path.join(LOCAL_OUTPUT_DIR, 'Items'))
if not os.path.isdir(os.path.join(LOCAL_OUTPUT_DIR, 'Logs')): os.makedirs(os.path.join(LOCAL_OUTPUT_DIR, 'Logs'))
open(LOCAL_OUTPUT_FILE, 'wb').close()
open(LOCAL_ITEM_LOG, 'wb').close()

FEED_URI = 's3://textbook-arbitrage/scraping_results/results-{}.csv'.format(date)
FEED_FORMAT = 'csv'
FEED_EXPORT_FIELDS = ['title', 'asin', 'price', 'trade_value', 'profit', 'roi', 'url']
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_KEY')

# LOG_LEVEL = 'ERROR'
# LOG_FILE = os.path.join(LOCAL_OUTPUT_DIR, 'Logs', 'log {}'.format(date))
# open(LOG_FILE, 'wb').close()

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# NOTE: AutoThrottle will honour the standard settings for concurrency and delay
AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY=5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY=60
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG=False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED=True
#HTTPCACHE_EXPIRATION_SECS=0
#HTTPCACHE_DIR='httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES=[]
#HTTPCACHE_STORAGE='scrapy.extensions.httpcache.FilesystemCacheStorage'
