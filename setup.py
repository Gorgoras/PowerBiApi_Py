from setuptools import setup
setup(
  name = 'powerbiapi_py',
  packages = ['powerbiapi_py'],
  version = '0.0.3',
  description = "Pi Consulting's Python wrapper around PowerBI REST API",
  author = 'Martin Zurita',
  author_email = 'mzurita@piconsulting.com.ar',
  url = 'https://github.com/PiConsulting/powerbiapi_py',
  download_url = 'https://github.com/PiConsulting/powerbiapi_py/archive/0.0.3.tar.gz',
  keywords = ['powerbi'],
  license = 'MIT',
  install_requires=['pyyaml', 'requests'],
  classifiers = [],
)