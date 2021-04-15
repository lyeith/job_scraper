#! <venv>/bin python3.8
# -*- coding: utf-8 -*-
"""
Created on 6/4/21 10:30 am

@author: David Wong
"""
from time import sleep

from bs4 import BeautifulSoup
from tqdm.auto import tqdm

import requests
import random
import urllib

import pendulum


class Scraper:
    """JobsScraper is a simple job postings scraper for Indeed."""

    def __init__(self, country: str, query: str, location: str, limit: int, max_delay: int = 0,
                 listing_age: int = None):
        """
        Create a JobsScraper object.
        Parameters
        ------------
        country: str
            Prefix country.
            Available countries:
            AE, AQ, AR, AT, AU, BE, BH, BR, CA, CH, CL, CO,
            CZ, DE, DK, ES, FI, FR, GB, GR, HK, HU, ID, IE,
            IL, IN, IT, KW, LU, MX, MY, NL, NO, NZ, OM, PE,
            PH, PK, PL, PT, QA, RO, RU, SA, SE, SG, TR, TW,
            US, VE, ZA.
        query: str
            Job position.
        location: str
            Job location.
        limit: int
            Number of pages to be scraped. Each page contains 15 results.
        max_delay: int, default = 0
            Max number of seconds of delay for the scraping of a single posting.
        full_details: bool, default = False
            If set to True, it scrapes individual job pages for the full job description
        listing_age: int, default = None
            Available Values: 1, 3, 7, 14
        """

        payload = {
            'q': query,
            'l': location,
            'fromage': listing_age,
        }

        url_encode = urllib.parse.urlencode(payload)

        if country.upper() == "US":
            self._url = f'https://indeed.com/jobs?{url_encode}'
        else:
            self._url = f'https://{country}.indeed.com/jobs?{url_encode}'

        self._query = query
        self._country = country
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'}
        self._pages = limit
        self._max_delay = max_delay
        self._jobs = []

    @staticmethod
    def _clean_text(txt):
        return txt.text.strip().replace('\n', '')

    @classmethod
    def _clean_date(cls, txt):

        txt = cls._clean_text(txt)

        days_ago = 0 if txt in ('Just posted', 'Today') \
            else int(txt.replace('+', '').replace('days ago', '').replace('day ago', ''))

        return pendulum.today().subtract(days=days_ago).to_date_string()

    def _generate_url(self, txt):
        return f'https://indeed.com{txt}' if self._country.upper() == 'US' else f'https://{self._country}.indeed.com{txt}'

    def _transform_summary_page(self, soup):

        trans_f = {
            'title': self._clean_text,
            'address': self._clean_text,
            'company': self._clean_text,
            'summary': self._clean_text,
            'url': self._generate_url,
            'date': self._clean_date,
            'salary': self._clean_text
        }

        jobs = soup.find_all('div', class_='jobsearch-SerpJobCard')

        for job in jobs:

            job = {
                'title': job.find('a', class_='jobtitle'),
                'address': job.find('div', class_='location') or job.find('span', class_='location'),
                'company': job.find('span', class_='company'),
                'summary': job.find('div', {'class': 'summary'}),
                'url': job.h2.a.get('href'),
                'date': job.find('span', class_='date date-a11y'),
                'salary': job.find('span', class_='salary'),
            }

            try:
                job.update({k: trans_f[k](v) for k, v in job.items() if v is not None})
            except Exception as e:
                print(e)

            self._jobs.append(job)

    def _get_page(self, url):

        if self._max_delay > 0:
            sleep(random.randint(0, self._max_delay))

        with requests.Session() as request:
            r = request.get(url=url, headers=self._headers)

        return BeautifulSoup(r.content, 'html.parser')

    def _get_description(self, soup) -> str:

        res = soup.find('div', id='jobDescriptionText')

        return res.get_text() if res is not None else None

    def _find_captcha(self, soup):
        if soup.title.string == 'hCaptcha solve page':
            raise Exception('Captcha Solve Prompted')

    def _clean_jobs(self, lst):
        def clean_salary(txt):
            if txt is None:
                return None, None

            if 'a month' in txt:
                res = txt.replace('$', '').replace(',', '').replace(' a month', '').split(' - ')
                divisor = 1
            elif 'a year' in txt:
                res = txt.replace('$', '').replace(',', '').replace(' a year', '').split(' - ')
                divisor = 12

            if len(res) == 1:
                return None, int(res[0]) / divisor
            else:
                return int(res[0]) / divisor, int(res[1]) / divisor

        for idx, elem in enumerate(lst):
            lst[idx]['min_salary'], lst[idx]['max_salary'] = clean_salary(elem['salary'])
            lst[idx]['query'] = self._query

        return lst

    def scrape(self) -> list:
        """
        Perform the scraping for the parameters provided in the class constructor.
        If duplicates are found, they get dropped.
        Returns
        ------------
        list of jobs
        """

        for i in tqdm(range(0, self._pages * 10, 10), desc="Performing Initial Scrape...", total=self._pages):
            page = self._get_page("{}&start={}".format(self._url, i))
            self._find_captcha(page)
            self._transform_summary_page(page)

        return self._clean_jobs(self._jobs)
