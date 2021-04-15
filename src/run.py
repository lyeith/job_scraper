#! <venv>/bin python3.8
# -*- coding: utf-8 -*-
"""
Created on 6/4/21 10:30 am

@author: David Wong
"""
import argparse

import logging
import os
import sys

from pygadgets.db_util import *
from pygadgets.query_util import *

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

from scrapers import mycareersfuture, indeed, linkedin


def scrape_indeed(**kwargs):
    table_info = {
        'fields': {
            'title': 'text',
            'company': 'text',
            'date': 'timestamp',
            'url': 'text',
            'summary': 'text',
            'address': 'text',
            'min_salary': 'int',
            'max_salary': 'int',
            'query': 'text'
        },
        'constraints': ['url']
    }

    kwargs['max_delay'] = 10
    kwargs['limit'] = int(kwargs['limit']) if 'limit' in kwargs else 10
    kwargs['listing_age'] = int(kwargs['listing_age']) if 'listing_age' in kwargs else None

    s = indeed.Scraper(**kwargs)

    logging.info('Starting Indeed Scraper...')

    return s.scrape(), table_info


def scrape_mycareersfuture(**kwargs):
    table_info = {
        'fields': {
            'title': 'text',
            'company': 'text',
            'date': 'timestamp',
            'link': 'text',
            'description': 'text',
            'experience': 'text',
            'address': 'text',
            'employment_type': 'text',
            'job_category': 'text',
            'query': 'text',
            'min_salary': 'int',
            'max_salary': 'int'
        },
        'constraints': ['link']
    }

    kwargs['listing_age'] = int(kwargs['listing_age']) if 'listing_age' in kwargs else None
    s = mycareersfuture.Scraper()

    logging.info('Starting MyCareersFutureScraper Scraper...')

    return s.scrape(**kwargs), table_info


def scrape_linkedin(**kwargs):
    table_info = {
        'fields': {
            'title': 'text',
            'company': 'text',
            'date': 'timestamp',
            'link': 'text',
            'description': 'text',
            'query': 'text'
        },
        'constraints': ['link']
    }

    kwargs['experience'] = kwargs['experience'].split(' ') if 'experience' in kwargs else None
    kwargs['job_type'] = kwargs['job_type'].split(' ') if 'job_type' in kwargs else None
    kwargs['locations'] = kwargs.pop('location').split(' ') if 'location' in kwargs else None

    logging.info('Starting Linkedin Scraper...')

    return linkedin.scrape(**kwargs), table_info


def parse_args(argv):
    parser = argparse.ArgumentParser()

    # MyCareersFuture Specific
    parser.add_argument('--employment_type')
    parser.add_argument('--posting_company')
    parser.add_argument('--sort_by')
    parser.add_argument('--salary')

    # Indeed Specific
    parser.add_argument('--country')

    # Linkedin Specific
    parser.add_argument('--experience')
    parser.add_argument('--relevance')
    parser.add_argument('--job_type')

    # General Arguments
    parser.add_argument('--listing_age')
    parser.add_argument('--location')  # Linkedin and Indeed
    parser.add_argument('--limit')

    # Non-optional
    parser.add_argument('--scraper', required=True)
    parser.add_argument('--query', required=True)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--table', required=True)

    args = parser.parse_args(argv).__dict__

    args['limit'] = int(args['limit']) if 'limit' in args else None
    args['listing_age'] = int(args['listing_age']) if 'listing_age' in args else None
    return {k: v for k, v in args.items() if v is not None}


def load(lst, schema, table, table_info):

    fields = table_info['fields']
    constraints = table_info['constraints']

    conf = {
        'host': os.environ['db_host'],
        'port': os.environ['db_port'],
        'database': os.environ['db_schema'],
        'user': os.environ['db_login'],
        'password': os.environ['db_password']
    }

    conn, db_time = connect_postgres(conf, readonly=False)
    common.pg_load(conn, lst, schema, table, fields, constraints=constraints)


def main(argv):

    arg_dict = parse_args(argv)

    scraper_lib = {
        'indeed': scrape_indeed,
        'mycareersfuture': scrape_mycareersfuture,
        'linkedin': scrape_linkedin
    }

    logging.info('Beginning Job Scraper...')
    s_func = scraper_lib[arg_dict.pop('scraper')]
    schema = arg_dict.pop('schema')
    table = arg_dict.pop('table')

    job_lst, table_info = s_func(**arg_dict)
    logging.info(f'Scraped {len(job_lst)} jobs!')

    logging.info('Loading into Postgres...')
    load(job_lst, schema, table, table_info)
    logging.info('Done!')


if __name__ == '__main__':
    main(sys.argv[1:])
