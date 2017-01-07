#!/usr/bin/env bash
docker-compose -f docker-compose.prod.yml -p pypi_scraper "$@"