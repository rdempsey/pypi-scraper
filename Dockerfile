FROM python:3.6-slim
MAINTAINER Robert Dempsey <robertonrails@gmail.com>

# Install Python requirements
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy over the code
COPY . /usr/src/app

# Start the pypi_scraper
CMD ["python", "pypi_scraper/pypi_scraper.py"]
