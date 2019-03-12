# -*- coding: utf-8 -*-
import sys
import scrapy


class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ['httpbin.org', 'google.com']
    # start_urls = ['http://httpbin.org/']

    custom_settings = dict(
        # JOBDIR='crawls/test',
        # ROBOTSTXT_OBEY=False,
        # USER_AGENT='Mozilla/5.0',
        # COOKIES_ENABLED=False,
        # CONCURRENT_REQUESTS=2,
        # DOWNLOAD_DELAY=1,
        # LOGSTATS_INTERVAL=1,
        FEED_EXPORT_ENCODING='utf-8'
    )

    num = 1

    def start_requests(self):
        # AttributeError: 'TestSpider' object has no attribute 'arg1'
        # self.logger.debug('self.arg1: %s' % self.arg1)  # self.arg1: val1
        # repr: 'Test\' "\xe6\xb5\x8b\xe8\xaf\x95'
        if sys.version_info[0] < 3 and getattr(self, 'arg1', None):
            self.logger.debug('self.arg1: ' + self.arg1.decode('utf-8'))
        else:
            self.logger.debug('self.arg1: %s' % getattr(self, 'arg1', None))  # self.arg1: None
        # self.logger.debug(self.settings.attributes.keys())
        # self.logger.debug(self.settings.attributes.values())
        # self.logger.debug(self.settings)
        # self.logger.debug(self.settings.attributes.items())
        if getattr(self, 'url', None):
            yield scrapy.Request(self.url)

        self.logger.debug('JOB: %s' % self.settings.get('JOB'))
        self.logger.debug('USER_AGENT: %s' % self.settings.get('USER_AGENT'))  # Scrapy/1.5.0 (+https://scrapy.org)
        self.logger.debug('ROBOTSTXT_OBEY: %s' % self.settings.getbool('ROBOTSTXT_OBEY'))  # True
        self.logger.debug('COOKIES_ENABLED: %s' % self.settings.getbool('COOKIES_ENABLED'))  # True
        self.logger.debug('CONCURRENT_REQUESTS: %s' % self.settings.getint('CONCURRENT_REQUESTS'))  # 16
        self.logger.debug('DOWNLOAD_DELAY: %s' % self.settings.getint('DOWNLOAD_DELAY'))  # 0
        self.logger.debug('CLOSESPIDER_TIMEOUT: %s' % self.settings.getint('CLOSESPIDER_TIMEOUT'))  # 0
        self.logger.debug('CLOSESPIDER_PAGECOUNT: %s' % self.settings.getint('CLOSESPIDER_PAGECOUNT'))  # 0

        self.log(u'Chinese characters: 汉字字符')
        self.logger.debug('2018-08-20 09:13:06 [apps_redis] DEBUG: Resuming crawl (675840 requests scheduled)')

        self.logger.warning('warn') #python2.7 AttributeError: 'LoggerAdapter' object has no attribute 'warn'
        self.logger.error('error')
        self.logger.warning('warning\n123abc')
        self.logger.error('error\n456abc')
        self.logger.error('error\n456abc')
        self.logger.critical('critical\n789abc')
        self.logger.warning('warning\n 123\nabc')
        self.logger.error('error\n 456\nabc')
        self.logger.critical('critical')
        self.logger.critical('critical\n 789\nabc')
        self.logger.critical('critical')
        self.logger.critical('critical')

        yield scrapy.Request('http://httpbin.org/redirect/1')
        yield scrapy.Request('http://httpbin.org/status/404')
        yield scrapy.Request('http://httpbin.org/headers')
        yield scrapy.Request('http://httpbin.org/headers')
        yield scrapy.Request('https://google.com/')

    def parse(self, response):
        self.log(response.text)
        if self.num == 1:
            yield scrapy.Request('https://www.baidu.com/')

        yield {u'Chinese 汉字 %s' % self.num: ''.join('0' + str(i) if i < 10 else str(i) for i in range(1, 100))}

        self.num += 1
