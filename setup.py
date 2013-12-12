#!/usr/bin/env python

import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='mammoth',
    version='0.1.0',
    description='Convert Word documents to simple and clean HTML',
    long_description=read("README"),
    author='Michael Williamson',
    author_email='mike@zwobble.org',
    url='http://github.com/mwilliamson/python-mammoth',
    packages=['mammoth', 'mammoth.docx'],
    keywords="docx word office clean html",
    install_requires=[
        "parsimonious>=0.5,<0.6",
    ]
)

