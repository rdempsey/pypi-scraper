#!/usr/bin/env python

"""
Scrape the PyPI Index and download all the package data.
"""

from bs4 import BeautifulSoup
import requests
from requests.exceptions import ConnectionError
import json
from time import sleep
import random
from scutils.log_factory import LogFactory
from os import getenv
from os import listdir
from os.path import isfile, join
import traceback
from retrying import retry


class PyPIScraper(object):

    def __init__(self,
                 pypi_source_page='https://pypi.python.org/pypi',
                 base_save_path='/usr/src/app/data',
                 log_level='INFO',
                 log_dir='/var/log/rulemanager',
                 log_file_name='rulemanager.log'):
        """
        PyPI Scraper base class.

        :param str pypi_source_page: PyPI homepage url
        :param str base_save_path: full path without the trailing slash to the directory to save the json files to
        :param str log_level: logging level
        :param str log_dir: full path to log file directory
        :param str log_file_name: log file name
        """

        self.pypi_source_page = pypi_source_page
        self.base_save_path = base_save_path
        self.log_level = log_level
        self.log_dir = log_dir
        self.log_file_name = log_file_name

    def _setup(self):
        """Create the logger and set up the rest of the configuration."""
        self.logger = LogFactory.get_instance(json=True,
                                              stdout=False,
                                              name='pypi_scraper',
                                              level=self.log_level,
                                              dir=self.log_dir,
                                              file=self.log_file_name)

    def _retry_if_requests_connection_error(exception):
        """Retry the request if the requests request produced a connection error."""
        return isinstance(exception, ConnectionError)

    def _get_list_of_existing_packages(self):
        """
        Get the list of existing packages.

        :return: retrieved_packages: list of existing package names
        """
        current_files = [
            f for f in listdir(self.base_save_path)
            if isfile(join(self.base_save_path, f))
        ]
        retrieved_packages = [
            f[:-5] for f in current_files
        ]

        return retrieved_packages

    @retry(retry_on_exception=_retry_if_requests_connection_error,
           wait_exponential_multiplier=500,
           wait_exponential_max=10000,
           stop_max_attempt_number=5)
    def _get_pypi_homepage(self):
        """
        Get the PyPI homepage

        :return html_to_parse: HTML of the PyPI homepage, or None
        """
        try:
            self.logger.info("Getting the PyPI homepage")
            response = requests.get(self.pypi_source_page)

            if 200 <= response.status_code < 300:
                html_to_parse = response.content
                return html_to_parse
            else:
                return None
        except Exception as e:
            self.logger.error("Caught exception retrieving the PyPI homepage", extra={
                'error_type': 'RequestsError',
                'ex': traceback.format_exc()
            })
            if isinstance(e, ConnectionError):
                raise

    def _get_list_of_packages_to_retrieve(self, html_to_parse):
        """
        Build the list of packages to retrieve.

        :param html_to_parse: html source code used to extract the package names
        :return packages_to_retrieve: list of package names
        """
        soup = BeautifulSoup(html_to_parse, 'html.parser')

        self.logger.info("Extracting package names")

        package_names = [
            link.get('href').split('/')[2]
            for link in soup.find('table', class_='list').find_all('a')
            if link is not None
        ]

        return package_names

    @retry(retry_on_exception=_retry_if_requests_connection_error,
           wait_exponential_multiplier=500,
           wait_exponential_max=10000,
           stop_max_attempt_number=5)
    def _get_json_data_for_package(self, package):
        """
        Retrieve the json data for a package.
    
        :param package: name of the package to retrieve the data for
        :return package_in_json: package data in json format, or None
        """
        url = self.pypi_source_page + "/{}/json".format(package)
    
        try:
            self.logger.info("Retrieving data for: {}".format(package))
            package_page_response = requests.get(url)

            if 200 <= package_page_response.status_code < 300:
                package_in_json = package_page_response.json()
                return package_in_json
            else:
                return None
        except Exception as e:
            self.logger.error("Caught exception retrieving package data", extra={
                'error_type': 'RequestsError',
                'ex': traceback.format_exc()
            })
            if isinstance(e, ConnectionError):
                raise

    def _save_package_data_to_disk(self, package_data):
        """
        Save the package data to disk.

        :param package_data: package data in json format
        :return boolean: True if successful, False if not
        """
        try:
            package_name = package_data.get('info', {}).get('name', None)
            file_name = self.base_save_path + "/{}.json".format(package_name)
            self.logger.info("Saving data for: {}".format(package_name))
            with open(file_name, 'w') as outfile:
                json.dump(package_data, outfile, indent=2, sort_keys=True, separators=(',', ':'))
        except Exception as e:
            self.logger.error("Caught exception retrieving the PyPI homepage", extra={
                'error_type': 'JSONError',
                'ex': traceback.format_exc()
            })
            raise

        return True

    def run(self):
        """
        Run the Pypi updater.
        """
        self._setup()

        self.logger.info("Starting update")

        html_to_parse = self._get_pypi_homepage()

        if html_to_parse:
            package_list = self._get_list_of_packages_to_retrieve(html_to_parse)

            if len(package_list) > 0:
                # Get the package info for all the packages
                self.logger.info("Beginning package information retrieval")
                files_written = 0

                for package in package_list:
                    # Get the package data
                    package_data_json = self._get_json_data_for_package(package)

                    # If we have package data, save it to disk
                    if package_data_json is not None:
                        if self._save_package_data_to_disk(package_data_json):
                            files_written += 1

                    # Wait a few seconds between getting package data pages
                    time_to_sleep = random.random() + random.randint(1, 3)
                    sleep(time_to_sleep)

                self.logger.info("{} packages retrieved in this run".format(files_written))
            else:
                self.logger.info("No new packages found")


if __name__ == '__main__':
    """
    Run the PuyPI Scraper
    """
    # Set a random seed for the random number generator
    random.seed()

    scraper = PyPIScraper(pypi_source_page=getenv('PYPI_SOURCE_PAGE'),
                          log_level=getenv('LOG_LEVEL'),
                          log_dir=getenv('LOG_DIR'),
                          log_file_name=getenv('LOG_FILE_NAME'))

    while True:
        # Retrieve an update every 7-9 minutes
        scraper.run()
        time_to_next_run = (random.random() + random.randint(7, 9)) * 60
        sleep(time_to_next_run)
