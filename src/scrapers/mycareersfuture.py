#! <venv>/bin python3.8
# -*- coding: utf-8 -*-
'''
Created on 6/4/21 10:31 am

@author: David Wong
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from tqdm import tqdm

import urllib
import pendulum
import logging


class Scraper:
    def __init__(self):
        self.driver = self.init_chromedriver()

    def scrape(self,
               query: str,
               employment_type: str = None,
               posting_company: str = None,
               sort_by: str = 'new_posting_date',
               salary: str = None,
               listing_age: int = None,
               **kwargs):
        """
        :param query:
            Your Search Term
        :param employment_type:
             One of ['Permanent', 'Full Time', 'Part Time', 'Contract'] or None
        :param posting_company:
            One of ['Direct', 'Third Party'] or None
        :param sort_by:
            One of ['new_posting_date', 'relevancy', 'min_monthly_salary'] or None
        :param salary:
            integer or None
        :param listing_age:
            integer or None
        :return:
        """

        payload = {
            'search': query,
            'employmentType': employment_type,
            'postingCompany': posting_company,
            'sortBy': sort_by,
            'salary': salary
        }
        payload = {k:v for k, v in payload.items() if v is not None}

        posted_after = pendulum.today().subtract(days=listing_age) if listing_age else None

        lst = []

        url = 'https://www.mycareersfuture.gov.sg/search?{}'.format(urllib.parse.urlencode(payload))

        logging.info(f'Requesting {url}')
        self.driver.get(url)

        logging.info('Waiting for Page Load')
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'job-card-0')))

        job_str = self.driver.find_element_by_xpath("//div[@data-cy='search-result-headers']").text

        if 'jobs found' in job_str:
            job_no = int(job_str.split('\n')[0].split('of')[0].strip().replace(' jobs found', ''))
        else:
            job_no = int(job_str.split('\n')[0].split('of')[0].strip())

        logging.info(f'Detected {job_no} jobs')
        pbar = tqdm(total=job_no)

        continue_running = True
        while continue_running:
            for i in range(22):
                WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'job-card-0')))

                job_card_id = f'job-card-{i}'
                try:
                    self.driver.find_element_by_id(job_card_id).click()
                except:
                    break

                WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'job_description')))

                post_date = pendulum.parse(self.driver.find_element_by_id('last_posted_date').text.replace('Posted ', ''),
                                           strict=False)
                if post_date < posted_after:
                    logging.info(f'Post Date: {post_date} is earlier than Posted After {posted_after}. Ending Loop')
                    continue_running = False
                    break

                salary = self.driver.find_element_by_xpath("//span[@class='salary_range dib f2-5 fw6 black-80']")\
                    .text.replace('$', '').replace(',', '').split('to')

                min_salary, max_salary = salary if len(salary) == 2 else (None, salary)
                if type(max_salary) == list and max_salary[0] == 'salary undisclosed':
                    max_salary = None

                dct = {
                    'title': self.driver.find_element_by_id('job_title').text,
                    'company': self.driver.find_element_by_xpath("//p[@data-cy='company-hire-info__company']").text,
                    'date': post_date,
                    'link': self.driver.current_url,
                    'description': self.driver.find_element_by_id('job_description').text,
                    'experience': self.driver.find_element_by_id('seniority').text,
                    'address': self.driver.find_element_by_id('address').text,
                    'employment_type': self.driver.find_element_by_id('employment_type').text,
                    'job_category': self.driver.find_element_by_id('job-categories').text,
                    'min_salary': min_salary,
                    'max_salary': max_salary
                }

                lst.append(dct)
                pbar.update(1)
                self.driver.back()

            try:
                WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'job-card-0')))
                self.driver.find_element_by_xpath("//span[@data-cy='pagination__next']").click()
            except Exception as e:
                logging.info('No more pages. Ending loop.')
                break

        pbar.close()
        self.driver.close()

        [e.update({'query': query}) for e in lst]

        return lst

    @staticmethod
    def init_chromedriver(chrome_executable_path='/usr/local/bin/chromedriver',
                          width=1472,
                          height=828):

        chrome_options = Options()
        chrome_options.headless = True
        chrome_options.page_load_strategy = 'normal'

        chrome_options.add_argument('--enable-automation')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument(f'--window-size={width},{height}')
        chrome_options.add_argument('--lang=en-GB')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-accelerated-2d-canvas')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--ignore-certificate-errors')

        # Disable downloads
        chrome_options.add_experimental_option(
            'prefs', {
                'safebrowsing.enabled': 'false',
                'download.prompt_for_download': False,
                'download.default_directory': '/dev/null',
                'download_restrictions': 3,
                'profile.default_content_setting_values.notifications': 2,
            }
        )

        return webdriver.Chrome(
            executable_path=chrome_executable_path,
            options=chrome_options,
        )
