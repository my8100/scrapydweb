# coding: utf8
from setuptools import find_packages, setup

from scrapydweb import __version__, __author__


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="scrapydweb",
    version=__version__,
    author=__author__,
    url="https://github.com/my8100/scrapydweb",
    
    description="Full-featured web UI for monitoring and controlling your Scrapyd servers",
    long_description=long_description,
    long_description_content_type="text/markdown",    

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "flask >= 1.0.2",
        "flask-compress >= 1.4.0",
        "requests",
    ],

    entry_points={
        "console_scripts": {
            "scrapydweb = scrapydweb.run:main"
        },
    },

    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
    ],
)
