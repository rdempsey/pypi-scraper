# PyPI Scraper

Get the latest and greatest from PyPI.

## Details

* Pulls the JSON data for each package on the PyPI homepage on a timely basis
* Saves the JSON files to disk to a location of your choosing
* Retries functionality for all HTTP calls
* Test coverage: run the tests and check the numbers

## Requirements
* Docker
* Docker Compose

If you want to run it locally or run the tests you'll need:

* Python 3.6.x
* All the things in the requirements.txt file

## Run It Like This

* `git clone git@github.com:rdempsey/pypi_scraper.git`
* `cd pypi_scraper`
* Update `docker-compose.yml` to suit your fancy, specifically the data volume mount
* `docker login`
* `docker pull rdempsey/pypi-scraper:latest`
* `docker-compose up -d`

## Run the Tests With Coverage (Anaconda)

* `git clone git@github.com:rdempsey/pypi_scraper.git`
* `cd pypi_scraper`
* `conda create --name pypiscraper python=3.6`
* `source activate pypiscraper`
* `pip install -r requirements.txt`
* `py.test -vv --tb=line --cov=pypi_scraper`