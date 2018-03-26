# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from setuptools import setup, find_packages


setup(
    name="holvi_toolkit",
    version='0.0.1',
    description="Holvi customised toolkit for python",
    author="Mohammed Salman",
    author_email="mohammed@holvi.com",
    license='MIT',
    classifiers=[
        'Development Status :: 1 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    packages=["statsd"],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    url='https://github.com/holvi/holvi-python-toolkit'
)
