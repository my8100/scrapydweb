# coding: utf-8
import io
import os
import re

from setuptools import find_packages, setup


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

about = {}
with open(os.path.join(CURRENT_DIR, 'scrapydweb', '__version__.py')) as f:
    exec(f.read(), about)

with io.open("README.md", 'r', encoding='utf-8') as f:
    long_description = re.sub(r':\w+:\s', '', f.read())  # Remove emoji


setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    license=about['__license__'],
    description=about['__description__'],

    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=find_packages(exclude=("tests", )),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <=3.9",
    install_requires=[
        "APScheduler==3.5.3",  # Aug 15, 2018
        "click==7.0",  # Sep 26, 2018
        "colorama==0.4.0",  # Oct 10, 2018
        "Flask==1.0.2",  # May 2, 2018
        "Flask-Compress==1.4.0",  # Jan 5, 2017
        "Flask-SQLAlchemy==2.4.0",  # Apr 25, 2019
        "idna==2.7",  # Jun 11, 2018    
        "itsdangerous==1.1.0",  # Oct 27, 2018
        "Jinja2==2.11.3",  # Nov 9, 2017
        "logparser==0.8.2",
        "MarkupSafe==1.1.1",  # Feb 24, 2019
        "pexpect==4.7.0",  # Apr 7, 2019
        "ptyprocess==0.6.0",  # Jun 22, 2018
        "pytz==2018.9",  # Jan 7, 2019
        "requests>=2.21.0",  # Dec 10, 2018
        "setuptools>=40.6.3",  # Dec 11, 2018
        "six==1.12.0",  # Dec 10, 2018
        "SQLAlchemy==1.3.24",  # Mar 31, 2021
        "tzlocal==1.5.1",  # Dec 1, 2017
        "w3lib==1.19.0",  # Jan 25, 2018
        "Werkzeug==0.14.1",  # Jan 1, 2018
    ],

    entry_points={
        "console_scripts": {
            "scrapydweb = scrapydweb.run:main"
        }
    },

    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ]
)
