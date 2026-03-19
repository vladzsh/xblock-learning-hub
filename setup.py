"""Setup for vladx XBlock."""

import os

from setuptools import setup


def package_data(pkg, roots):
    """Find all files under each root directory for package data."""
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))
    return {pkg: data}


setup(
    name='vladx-xblock',
    version='0.2',
    description='VladX Learning Hub -- an educational XBlock demonstrating the full XBlock API',
    license='AGPL v3',
    packages=['vladx'],
    install_requires=['XBlock'],
    entry_points={
        'xblock.v1': [
            'vladx = vladx:VladXBlock',
        ],
    },
    package_data=package_data("vladx", ["static", "public", "translations"]),
)
