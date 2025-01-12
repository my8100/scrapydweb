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
    python_requires=">=3.6",
    install_requires=[
        "APScheduler==3.6.0",  # Mar 18, 2019
        "click==7.1.2",  # Apr 28, 2020
        "colorama==0.4.0",  # Oct 10, 2018
        "Flask==2.0.0",  # May 12, 2021
        "Flask-Compress==1.4.0",  # Jan 5, 2017
        "Flask-SQLAlchemy==2.4.0",  # Apr 25, 2019
        "idna==2.7",  # Jun 11, 2018
        "itsdangerous==2.0.0",  # May 12, 2021
        "Jinja2==3.0.0",  # May 12, 2021
        "logparser>=0.8.4",
        "MarkupSafe==2.0.0",  # May 12, 2021
        "pexpect==4.7.0",  # Apr 7, 2019
        "ptyprocess==0.6.0",  # Jun 22, 2018
        "pytz==2018.9",  # Jan 7, 2019
        "requests>=2.21.0",  # Dec 10, 2018
        "setuptools>=40.6.3",  # Dec 11, 2018
        "six==1.16.0",  # May 5, 2021
        "SQLAlchemy==1.3.24",  # Mar 31, 2021
        "tzlocal==1.5.1",  # Dec 1, 2017
        "w3lib==2.0.0",  # Aug 11, 2022
        "Werkzeug==2.0.0",  # May 12, 2021
    ],

    entry_points={
        "console_scripts": {
            "scrapydweb = scrapydweb.run:main"
        }
    },

    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ]
)
