from setuptools import setup, find_packages
import logging
logger = logging.getLogger(__name__)

name = 'drawsvg'
package_name = name
version = '2.0.0'

try:
    with open('README.md', 'r') as f:
        long_desc = f.read()
except:
    logger.warning('Could not open README.md.  long_description will be set to None.')
    long_desc = None

setup(
    name = package_name,
    packages = find_packages(),
    version = version,
    description = 'A Python 3 library for programmatically generating SVG images (vector drawings) and rendering them or displaying them in a Jupyter notebook',
    long_description = long_desc,
    long_description_content_type = 'text/markdown',
    author = 'Casey Duckering',
    #author_email = '',
    url = f'https://github.com/cduck/{name}',
    download_url = f'https://github.com/cduck/{name}/archive/{version}.tar.gz',
    keywords = ['SVG', 'draw', 'graphics', 'iPython', 'Jupyter', 'widget'],
    license_files = ('LICENSE.txt',),
    license = 'MIT License',
    classifiers = [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Framework :: IPython',
        'Framework :: Jupyter',
    ],
    extras_require = {
        'raster': ['numpy~=1.16', 'imageio~=2.5', 'CairoSVG~=2.3'],
        'color': ['pwkit~=1.0'],
        'all': ['numpy~=1.16', 'imageio~=2.5', 'CairoSVG~=2.3', 'pwkit~=1.0'],
    },
)
