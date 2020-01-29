from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from datetime import datetime
from pathlib import Path
import re
import os


class Blubrry:

    def __init__(self, username, password, wait=10):
        self.username = username
        self.password = password
        self.wait = 5
        self.episode_data = {}

    def create_driver(self, preferences=None, headless=False):
        if preferences:
            profile = webdriver.FirefoxProfile()
            for pref_key, pref_value in preferences.items():
                profile.set_preference(pref_key, pref_value)
        options = Options()
        options.headless = headless
        self.driver = webdriver.Firefox(executable_path=r'/usr/local/bin/geckodriver', service_log_path=os.path.devnull)
        self.driver.implicitly_wait(self.wait)

    def login(self):
        self.driver.get('https://blubrry.com/signin.php')
        username_input = self.driver.find_element_by_id('username')
        password_input = self.driver.find_element_by_id('password')
        submit = self.driver.find_element_by_name('submit')

        username_input.clear()
        password_input.clear()

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        submit.click()

    def _set_date(self, start, stop):
        # requires start and stop to be datetime.datetime objects
        if isinstance(start, str):
            start = start.replace('-', '')
        else:
            start = start.strftime("%Y%m%d")
        if isinstance(stop, str):
            stop = stop.replace('-', '')
        else:
            stop = stop.strftime("%Y%m%d")
        url = f'https://stats.blubrry.com/stats/s-34209/h-d{start}-d{stop}/'
        self.driver.get(url)

    def scrape_episode_data(self, ep_num, start, stop, dpc='Clients'):
        self._set_date(start, stop)
        ep_link_xpath = f'//tr[contains(@title, "{ep_num}")]//a'
        ep_link = self.driver.find_element_by_xpath(ep_link_xpath).get_attribute('href')
        self.driver.get(ep_link)
        # actually scraping the data
        ep_data = {}  # will write to later
        ep_data["downloads"] = self._scrape_download_data()
        ep_data["geo"] = self._scrape_geo_data()
        ep_data["dpc"] = self._scrape_dpc_data(dpc)
        return(ep_data)

    def _scrape_download_data(self):
        self.driver.find_element_by_link_text('more detail').click()
        download_elements = self.driver.find_elements_by_class_name('basicinfo-detail')  # note elements is plural
        downloads_raw = [div.text for div in download_elements]
        downloads = [int(re.sub(r'.*:\s?|\s?new!\s?|,', '', dl)) for dl in downloads_raw]
        download_dict = {
            "total": downloads[0] + downloads[1],
            "full": downloads[0],
            "partial_plays": downloads[1],
            "1_25": downloads[2],
            "25_50": downloads[3],
            "50_75": downloads[4],
            "75_99": downloads[5]
        }
        return(download_dict)

    def _expand_list(self, expand_text='See Full List'):
        try:
            self.driver.find_element_by_link_text(expand_text).click()
        except NoSuchElementException:
            pass

    def _scrape_geo_data(self):
        self.driver.find_element_by_link_text('World').click()
        self._expand_list()
        geo_data = self.driver.find_elements_by_xpath('//table[@id="country_results"]/tbody/tr')
        countries = {}
        for row in geo_data:
            cells = row.find_elements_by_css_selector('td')
            countries[cells[0].text] = int(cells[2].text)
        return(countries)

    def _scrape_dpc_data(self, dpc):
        # dpc refers to if we are scraping distribution, platforms, or clients
        # they're essentially the same thing, will have to pick one at some point
        if dpc.title() not in ('Distribution', 'Platforms', 'Clients'):
            return(None)
        else:
            self.driver.find_element_by_link_text(dpc.title()).click()
            self._expand_list()
            dpc_data = self.driver.find_elements_by_xpath(f'//table[@id="{dpc[:-1].lower()}_results"]/tbody/tr')
            dpc_dict = {}
            for row in dpc_data:
                dpc_label = row.find_element_by_css_selector('a.more-info-popover')
                dpc_total = row.find_element_by_css_selector('td.report-table-total')
                dpc_dict[dpc_label.text] = int(dpc_total.text)
            return(dpc_dict)


if __name__ == '__main__':
    blubrry = Blubrry('rawtalkpodcast@gmail.com', 'k33p1tr4w', 0)
    blubrry.create_driver()
    blubrry.login()
    test = blubrry.scrape_episode_data(66, '2019-09-11', '2019-10-23', 'Platforms')


