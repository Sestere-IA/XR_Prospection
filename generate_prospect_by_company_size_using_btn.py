"""
Command to generate CSV : scrapy crawl prospectpercompanysize -o name_company_link_company_size.csv
"""

import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from logzero import logger
from webdriver_manager.chrome import ChromeDriverManager
import time
import scrapy.utils.misc
import scrapy.core.scraper


def warn_on_generator_with_return_value_stub(spider, callable):
    pass


scrapy.utils.misc.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub
scrapy.core.scraper.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub


class ProspectItem(scrapy.Item):
    company_name = scrapy.Field()
    name_signatory = scrapy.Field()
    link_company = scrapy.Field()
    company_size = scrapy.Field()


class ProspectSpiderPerCompanySize(scrapy.Spider):
    name = "prospectpercompanysize"
    allowed_domains = ["toscrape.com"]
    custom_settings = {'FEED_EXPORT_ENCODING': 'utf-8',
                       'FEED_URI': 'CSV/name_company_link_company_size.csv'}

    # Using a dummy website to start scrapy request
    def start_requests(self):
        url = "http://quotes.toscrape.com"
        yield scrapy.Request(url=url, callback=self.parse_prospect)

    def parse_prospect(self, response):
        page_count = 1
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        options.add_experimental_option("prefs",
                                        {"profile.default_content_setting_values.cookies": 2})  # TODO to verify
        driver = webdriver.Chrome(ChromeDriverManager().install())
        url = 'https://www.securite-routiere.gouv.fr/employeurs-engages/liste-des-employeurs-engages-page-1-57?page=1' \
              '&range=All&zipcode=All'
        driver.get(url)
        driver.implicitly_wait(10)
        # Explicit wait
        wait = WebDriverWait(driver, 5)

        # Accept Cookie (necessary or impossble to click on next btn)
        coockie_accept_btn = driver.find_element(By.XPATH, '//*[@id="footer_tc_privacy_button_3"]')
        coockie_accept_btn.click()

        drop_down_menu = driver.find_element(By.CLASS_NAME, "filter-select.filter-select_range")
        drop_down_menu.click()

        time.sleep(1)

        dropdown_menu_clicked = driver.find_element(By.CLASS_NAME, "dropdown-menu")
        all_comany_size = dropdown_menu_clicked.text.strip().split("\n")
        logger.info(all_comany_size)

        drop_down_menu.click()

        for company_size in all_comany_size:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "filter-select.filter-select_range")))
            drop_down_menu = driver.find_element(By.CLASS_NAME, "filter-select.filter-select_range")
            webdriver.ActionChains(driver).move_to_element(drop_down_menu).click(drop_down_menu).perform()
            dropdown_menu_clicked = driver.find_element(By.CLASS_NAME, "dropdown-menu")
            item = dropdown_menu_clicked.find_element(By.PARTIAL_LINK_TEXT, company_size)
            item.click()

            filtre_btn = driver.find_element(By.CLASS_NAME, "full.grey.cta-round")
            filtre_btn.click()
            # To del
            time.sleep(5)

            for i in range(0, 200):
                driver.implicitly_wait(10)
                # Explicit wait
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "company-item")))
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "page-item")))
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "filter-select.filter-select_range")))
                next_btn = driver.find_elements(By.CLASS_NAME, 'page-item')

                # Go to scrapy
                sel = scrapy.Selector(text=driver.page_source)

                # Find company name
                companies = sel.css("li.company-item")

                for company in companies:
                    company_name = company.css("p::text").get()
                    name_signatory = company.css("p.signatory::text").get()
                    link_company = company.css("div.img-wrapper a.link-over ::attr(href)").extract()

                    item = ProspectItem()
                    item["company_name"] = company_name
                    item["name_signatory"] = name_signatory
                    item["link_company"] = link_company
                    item["company_size"] = company_size

                    yield item

                logger.info(f"Scraping page :{page_count}")
                page_count += 1

                # Terminating and reinstantiating webdriver every 200 URL to reduce the load on RAM
                if (i != 0) and (i % 200 == 0):
                    driver.quit()
                    logger.info("Chromedriver restarted")

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "page-item")))

                if next_btn[-2].get_attribute("class") == "page-item disabled":
                    break
                else:
                    next_btn[-2].click()  # Click on next btn
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "page-item")))

        logger.info(f"Scraped {page_count} PM2.5 readings.")
        driver.quit()
