"""ECget -- Get Environment Canada Weather & Hydrometric Data

Copyright 2014 Doug Latornell and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from setuptools import (
    find_packages,
    setup,
)


PROJECT = 'ECget'
VERSION = '0.1'
DEV_STATUS = '2 - Pre-Alpha'


python_classifiers = [
    'Programming Language :: Python :: {0}'.format(py_version)
    for py_version in ['2', '2.7', '3', '3.2', '3.3']]
other_classifiers = [
    'Development Status :: ' + DEV_STATUS,
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python :: Implementation :: CPython',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Education',
    'Intended Audience :: Developers',
    'Intended Audience :: End Users/Desktop',
]
try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''
install_requires = [
    # see requirements.txt for versions most recently used in development
    'arrow',
    'cliff',
    'requests',
]

setup(
    name=PROJECT,
    version=VERSION,
    description='Get Environment Canada Weather & Hydrometric Data',
    long_description=long_description,
    author='Doug Latornell',
    author_email='djl@douglatornell.ca',
    url='https://bitbucket.org/douglatornell/ecget',
    download_url=(
        'https://bitbucket.org/douglatornell/ecget/get/default.tar.gz'),
    license='Apache License, Version 2.0',
    classifiers=python_classifiers + other_classifiers,
    platforms=['MacOS X', 'Linux'],
    install_requires=install_requires,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'ecget = ecget.main:main',
        ],
        'ecget.app': [
            'river flow = ecget.river:RiverFlow',
        ],
        'ecget.get_data': [
            'river.discharge = ecget.river:RiverDischarge',
        ],
    },
)
