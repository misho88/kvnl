#!/usr/bin/env python3

import setuptools

import kvnl
long_description = kvnl.__doc__

setuptools.setup(
    name='kvnl',
    version='0.1.0',
    author='Mihail Georgiev',
    author_email='misho88@gmail.com',
    description='Pipes - Functions for Building Data Pipelines',
    long_description=long_description,
    long_description_content_type='text/plain',
    url='https://github.com/misho88/kvnl',
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    #py_modules=['kvnl']
)
