#!/usr/bin/env bash
docker-compose -f docker-compose.build.yml -p pypi_scraper "$@"