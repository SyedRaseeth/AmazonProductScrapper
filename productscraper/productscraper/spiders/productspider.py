import scrapy
import json
import scrapy
from urllib.parse import urljoin
from gc import callbacks
import re


class ProductspiderSpider(scrapy.Spider):
    name = "product"
    
    

    def start_requests(self):
        keyword_list = ["gaming laptops"]
        for keyword in keyword_list:
            amazon_search_url = f"https://www.amazon.com/s?k={keyword}&page=1"
            yield scrapy.Request(url = amazon_search_url, callback = self.discover_product, meta= {"keyword" : keyword, "page" : 1})
            
    def discover_product(self, response):
        page = response.meta["page"]
        keyword = response.meta["keyword"]
        
        products = response.css("div.gsx-ies-anchor")
        for product in products:
            relative_url = product.css("h2 a.a-link-normal::attr(href)").get()
            product_url = urljoin("https://www.amazon.com/",relative_url)
            yield scrapy.Request(url = product_url, callback = self.product_details, meta = {"keyword" : keyword, "page" : page} )
            
            if page == 1:
                available_pages = response.css("span.s-pagination-item::text").getall()
                last_page = available_pages[-1]
            
                for page_num in range(0,int(last_page)):
                    amazon_search_url = f"https://www.amazon.com/s?k={keyword}&page={page_num}"
                    yield scrapy.Request(url = amazon_search_url, callback = self.discover_product, meta= {"keyword" : keyword, "page" : page_num})
        
        
    def product_details(self,response):
        bullets = response.css('ul.a-spacing-mini li span.a-list-item ::text').getall()
        for bullet in bullets:
            bullet = bullet.strip()
        price = response.css('.a-price span[aria-hidden="true"]::text').get("")
        if not price:
            price = response.css('span.a-price span.a-offscreen ::text').get("")
            
        image_data = json.loads(re.findall(r"colorImages':.*'initial':\s*(\[.+?\])},\n", response.text)[0])
        variant_data = re.findall(r'dimensionValuesDisplayData"\s*:\s* ({.+?}),\n', response.text)
        
        yield {
            "name": response.css("#productTitle::text").get("").strip(),
            "price": price,
            "stars": response.css("i[data-hook=average-star-rating] ::text").get("").strip(),
            "rating_count": response.css("span.a-size-base::text").get().strip(),
            "feature_bullets": bullets,
            "images": image_data,
            "variant_data": variant_data,
        }