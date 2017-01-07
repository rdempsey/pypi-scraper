"""Test PyPI Scraper."""
# To run with autotest and print all output to console run:
#   COMMAND LINE: py.test -vv --tb=line --cov=pypi_scraper
#   COMMAND LINE WITH REPORT: py.test -vv --tb=line --cov=pypi_scraper --cov-report html

import pytest
from mock import MagicMock, patch
from requests.exceptions import ConnectionError
from pypi_scraper.pypi_scraper import PyPIScraper
from scutils.log_factory import LogObject
import json


@pytest.fixture()
def pypi_scraper():
    """Create an instance of the PyPI Scraper."""
    pypi_scraper_instance = PyPIScraper(log_level='DEBUG',
                                        log_dir='./logs',
                                        log_file_name='pypi_scraper.log')

    return pypi_scraper_instance

class TestPyPIScraper(object):
    """Test the PyPI Scraper"""

    def test_setup_creates_logger(self, pypi_scraper):
        """Ensure _setup creates an instance of the logger."""
        pypi_scraper._setup()
        assert isinstance(pypi_scraper.logger, LogObject)

    def test_get_list_of_existing_packages_returns_proper_file_list(self, pypi_scraper, tmpdir):
        """Ensure we can get the existing list of package files the scraper has already created."""
        pypi_scraper._setup()

        # Create a temporary data folder and files
        temp_path = tmpdir.mkdir("data")
        temp_path.join("test1.json").write("content")
        temp_path.join("test2.json").write("content")
        temp_path.join("test3.json").write("content")

        pypi_scraper.base_save_path = temp_path

        package_list = pypi_scraper._get_list_of_existing_packages()

        assert len(package_list) == 3
        assert "test1" in package_list
        assert "test2" in package_list
        assert "test3" in package_list
        assert "test4" not in package_list

    def test_get_pypi_page_returns_html_or_none(self, pypi_scraper):
        """Ensure the PyPI homepage HTML is returned or None if not."""
        pypi_scraper._setup()

        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.return_value = '<html><body></body></html>'

        mock_failure = MagicMock()
        mock_failure.status_code = 404
        mock_failure.return_value = None

        with patch('pypi_scraper.pypi_scraper.requests') as mock_requests:
            mock_requests.return_value = mock_requests
            mock_requests.get = MagicMock(side_effect=[mock_success])

            result = pypi_scraper._get_pypi_homepage()

            assert result is not None

        with patch('pypi_scraper.pypi_scraper.requests') as mock_requests:
            mock_requests.return_value = mock_requests
            mock_requests.get = MagicMock(side_effect=[mock_failure])

            result = pypi_scraper._get_pypi_homepage()

            assert result is None

    def test_get_pypi_page_retries_on_connection_error(self, pypi_scraper):
        """Ensure the proper error, if one occurs, is returned when obtaining the PyPI homepage."""
        pypi_scraper._setup()

        mock_conn_err = ConnectionError()
        mock_success = MagicMock()
        mock_success.status_code = 200

        with patch('pypi_scraper.pypi_scraper.requests') as mock_requests:
            mock_requests.return_value = mock_requests
            mock_requests.get = MagicMock(side_effect=[mock_conn_err, mock_conn_err, mock_success])

            pypi_scraper.logger.error = MagicMock()

            pypi_scraper._get_pypi_homepage()

            assert pypi_scraper.logger.error.call_count == 2

    def test_get_list_of_packages_to_retrieve_returns_proper_package_list(self, pypi_scraper):
        """Ensure the proper list and count of packages is extracted from the source HTML."""
        pypi_scraper._setup()

        expected_package_list = ['virtual-touchpad', 'pugixmltodict', 'tcrudge', 'casket', 'auxly', 'wikilabels',
                                 'libsass', 'voicelabs', 'daftpunk', 'aomi', 'wikiclass', 'gprime', 'ores',
                                 'plugs-configuration', 'autolux', 'django-compat-patcher', 'gallery_get',
                                 'scilab_kernel', 'gitterest', 'perceval', 'editquality', 'vilify', 'PyAccessPoint',
                                 'converge', 'getpypie', 'pymcef', 'hitchvm', 'nester-pgaines937', 'connexion',
                                 'nodewire', 'pykafka-tools', 'commandlib', 'psmtool', 'fints', 'mr_bot', 'pycricbuzz',
                                 'alignak_demo', 'primesieve', 'vcdriver', 'ti']

        with open('tests/data/pypi_homepage_correct.htm') as source_file:
            result = pypi_scraper._get_list_of_packages_to_retrieve(source_file)

            assert len(result) == 40
            for package in expected_package_list:
                assert package in result

    def test_get_json_data_for_package_returns_json_or_none(self, pypi_scraper):
        """Ensure the json data for a package is returned or None if not."""
        pypi_scraper._setup()

        with open('tests/data/flask.json') as source_file:
            flask_json = json.load(source_file)

            mock_success = MagicMock()
            mock_success.status_code = 200
            mock_success.return_value = flask_json

            mock_failure = MagicMock()
            mock_failure.status_code = 404
            mock_failure.return_value = None

            with patch('pypi_scraper.pypi_scraper.requests') as mock_requests:
                mock_requests.return_value = mock_requests
                mock_requests.get = MagicMock(side_effect=[mock_success])

                result = pypi_scraper._get_json_data_for_package(package='flask')

                assert result is not None

            with patch('pypi_scraper.pypi_scraper.requests') as mock_requests:
                mock_requests.return_value = mock_requests
                mock_requests.get = MagicMock(side_effect=[mock_failure])

                result = pypi_scraper._get_json_data_for_package(package='flask')

                assert result is None

    def test_get_json_data_for_package_retries_on_connection_error(self, pypi_scraper):
        """Ensure the proper error, if one occurs, is returned when obtaining the json data for a package."""
        pypi_scraper._setup()

        mock_conn_err = ConnectionError()
        mock_success = MagicMock()
        mock_success.status_code = 200

        with patch('pypi_scraper.pypi_scraper.requests') as mock_requests:
            mock_requests.return_value = mock_requests
            mock_requests.get = MagicMock(side_effect=[mock_conn_err, mock_conn_err, mock_success])

            pypi_scraper.logger.error = MagicMock()

            pypi_scraper._get_json_data_for_package(package='flask')

            assert pypi_scraper.logger.error.call_count == 2

    def test_save_package_data_to_disk_properly_saves_file_to_disk(self, pypi_scraper, tmpdir):
        """Ensure the package json file is properly saved to disk."""
        pypi_scraper._setup()

        # Create a temporary data folder and files
        temp_path = tmpdir.mkdir("data")
        pypi_scraper.base_save_path = temp_path

        with open('tests/data/flask.json') as source_file:
            flask_json = json.load(source_file)
            result = pypi_scraper._save_package_data_to_disk(flask_json)
            assert result

        with pytest.raises(Exception) as context:
            package_json = None
            result = pypi_scraper._save_package_data_to_disk(package_json)
            assert result == False