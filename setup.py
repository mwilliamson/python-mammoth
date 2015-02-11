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
    version='0.3.11',
    description='Convert Word documents from docx to simple and clean HTML and Markdown',
    long_description=read("README"),
    author='Michael Williamson',
    author_email='mike@zwobble.org',
    url='http://github.com/mwilliamson/python-mammoth',
    packages=['mammoth', 'mammoth.docx', 'mammoth.style_reader', 'mammoth.writers'],
    scripts=["scripts/mammoth"],
    keywords="docx word office clean html markdown md",
    install_requires=_install_requires,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)

