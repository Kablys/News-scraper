# -*- coding: utf-8 -*-
import re
import scrapy

class DelfiSpider(scrapy.Spider):
    name = 'delfi'

    custom_settings = {
        'LOG_FILE': 'log.txt',

        'FEED_FORMAT': 'json',
        'FEED_URI': 'delfi.json',
        'FEED_EXPORT_ENCODING': 'utf-8',

        'CONCURRENT_REQUESTS_PER_DOMAIN' : '1',

        'AUTOTHROTTLE_ENABLED' : 'True',
        'AUTOTHROTTLE_START_DELAY' : '5.0',
        'AUTOTHROTTLE_MAX_DELAY' : '60.0',
        'AUTOTHROTTLE_TARGET_CONCURRENCY' : '1.0',
        'AUTOTHROTTLE_DEBUG' : 'True',

        'HTTPCACHE_ENABLED' : 'True',
        'HTTPCACHE_EXPIRATION_SECS' : '0',  # Never expire.
    }
    allowed_domains = ['delfi.lt']
    # Articles from all channles and categories during 01.01.2017 - 01.01.2018 period
    archive_url = 'https://www.delfi.lt/archive/index.php?fromd=01.01.2017&tod=01.01.2018&channel={}&category=0&query=&page=1'
    start_urls = [archive_url.format('600'), # Auto
                  archive_url.format('903'), # Sportas
                  archive_url.format('906'), # Veidai
                  archive_url.format('907'), # Verslas
                  archive_url.format('908'), # Mokslas
                 ]

    def parse(self, response):
        match = re.search(r'&channel=(\d+).+&page=(\d+)', response.request.url)
        channel = match.group(1)
        page = int(match.group(2))

        for num, article in enumerate(response.css('.CBarticleTitle::attr(href)').extract()):
            # Skip video articles
            if "/video/" in article:
                self.logger.info('Skip (video) article {}'.format(article))
                continue
            self.logger.info('Cha: {}, req {}/1000 article: {}'.format(channel, (page-1)*100+num+1, article))
            yield scrapy.Request(url=article, callback=self.parse_article)

        next_page = response.css('.next::attr(href)').extract_first()
        next_page = ''.join(next_page.split())
        # parsing up to 11 page because expecting 1000 articles, but some are skipped (video)
        if (next_page is not None) and (page < 11):
            yield response.follow(next_page, callback=self.parse)

    def parse_article(self, response):
        url = response.request.url
        categorys = response.css('[itemprop=title]::text').extract()
        if categorys == []: # If article is missing categorys extract them from url
            categorys = re.search(r'https:\/\/www\.delfi\.lt\/(\w+)\/', url).group(1)
        yield {
            'title': response.css('h1::text').extract_first().strip(),
            'date': response.css('[class$=source-date]::text').extract_first(),
            'categorys': categorys,
            'intro': " ".join(response.xpath('//*[@itemprop]/b//text()').extract()),
            'text': " ".join(response.xpath('//*[@itemprop="articleBody"]/p//text()').extract()),
            'tags': response.css('.ttl_link::text').extract(),
            # 'body': response.body_as_unicode(),
            'url' : url,
        }
