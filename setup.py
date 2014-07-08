#!/usr/bin/env python

import os
import sys
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


_install_requires = [
    "parsimonious>=0.5,<0.6",
    "dodge>=0.1.5,<0.2",
]

if sys.version_info[:2] <= (2, 6):
    _install_requires.append("argparse>=1.1,<2.0")

setup(
    name='mammoth',
    version='0.3.3',
    description='Convert Word documents to simple and clean HTML',
    long_description=read("README"),
    author='Michael Williamson',
    author_email='mike@zwobble.org',
    url='http://github.com/mwilliamson/python-mammoth',
    packages=['mammoth', 'mammoth.docx', 'mammoth.style_reader'],
    scripts=["scripts/mammoth"],
    keywords="docx word office clean html",
    install_requires=_install_requires,
)

