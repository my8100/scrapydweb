# coding: utf8
import os

from setuptools import find_packages, setup


CWD = os.path.dirname(os.path.abspath(__file__))

about = {}
with open(os.path.join(CWD, 'scrapydweb', '__version__.py')) as f:
    exec(f.read(), about)

with open("README.md", "r") as fh:
    long_description = fh.read()


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

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*",
    install_requires=[
        "flask >= 1.0.2",
        "flask-compress >= 1.4.0",
        "requests",
        "setuptools",
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
