#! <venv>/bin python3.8
# -*- coding: utf-8 -*-
"""
Created on 7/4/21 12:48 pm

@author: David Wong
"""
import logging
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.events import Events, EventData
from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters, ExperienceLevelFilters

chromedriver = '/usr/local/bin/chromedriver'

# Change root logger level (default is WARN)
logging.basicConfig(level=logging.WARN)
logging.getLogger('li:scraper').setLevel(logging.INFO)

jobs = []


def on_data(data: EventData):
    dct = {
        'title': data.title,
        'company': data.company,
        'date': data.date,
        'link': data.link,
        'description': data.description
    }

    jobs.append(dct)


def on_error(error):
    print('[ON_ERROR]', error)


def on_end():
    print('[END]')


scraper = LinkedinScraper(
    chromedriver,  # Custom Chrome executable path (e.g. /foo/bar/bin/chromedriver)
    headless=True,  # Overrides headless mode only if chrome_options is None
    max_workers=1,  # How many threads will be spawned to run queries concurrently (one Chrome driver for each thread)
    slow_mo=5,  # Slow down the scraper to avoid 'Too many requests (429)' errors
)

# Add event listeners
scraper.on(Events.DATA, on_data)
scraper.on(Events.ERROR, on_error)
scraper.on(Events.END, on_end)


def scrape(query: str,
           listing_age: int = None,
           relevance: str = None,
           job_type: list = None,
           experience: list = None,
           locations: list = ['Singapore'],
           limit: int = None):

    """
    :param query: str
        Job search query
    :param listing_age: int
        Age of job listing.
        Available Options:
            1, 7, 30
    :param relevance: str
        Linkedin Relevance Filter
        Available Options:
            recent, relevant
    :param job_type: list
        Linkedin Job Type
        Available Options:
            contract, temporary, part_time, full_time
    :param experience: list
        Linkedin Experience Filter
        Available Options:
            internship, entry_level, associate, mid_senior, director
    :param locations: list
        List of Locations to Search
        Available Options:
            Singapore
    :param limit: integer
        Max Number of Jobs to Fetch
    :return:
    """

    global jobs

    experience_filters = {
        'internship': ExperienceLevelFilters.INTERNSHIP,
        'entry_level': ExperienceLevelFilters.ENTRY_LEVEL,
        'associate': ExperienceLevelFilters.ASSOCIATE,
        'mid_senior': ExperienceLevelFilters.MID_SENIOR,
        'director': ExperienceLevelFilters.DIRECTOR,
    }
    time_filters = {
        1: TimeFilters.DAY,
        7: TimeFilters.WEEK,
        30: TimeFilters.MONTH,
        None: TimeFilters.ANY
    }

    relevance_filters = {
        'recent': RelevanceFilters.RECENT,
        'relevant': RelevanceFilters.RELEVANT,
    }

    type_filters = {
        'contract': TypeFilters.CONTRACT,
        'temporary': TypeFilters.TEMPORARY,
        'part_time': TypeFilters.PART_TIME,
        'full_time': TypeFilters.FULL_TIME
    }

    time_filter = time_filters.get(listing_age)
    relevance_filter = relevance_filters.get(relevance)
    type_filter = [type_filters[e] for e in job_type] if job_type else None
    experience_filter = [experience_filters[e] for e in experience] if experience else None

    jobs = []
    queries = [
        Query(
            query=query,
            options=QueryOptions(
                locations=locations,
                optimize=True,
                limit=limit,
                filters=QueryFilters(
                    relevance=relevance_filter,
                    time=time_filter,
                    type=type_filter,
                    experience=experience_filter
                )
            )
        )
    ]
    scraper.run(queries)
    [e.update({'query': query}) for e in jobs]

    return jobs
