# -*- coding: utf-8 -*-

import setuptools

with open('README.md') as f:
    long_description = f.read()

setuptools.setup(
    name='monapy',
    version='0.4.0',
    author='Andriy Stremeluk',
    author_email='astremeluk@gmail.com',
    description='Python Library to build declarative tools',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url='https://github.com/andriystr/Monapy',
    packages=setuptools.find_packages(exclude=['test*']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    python_requires='>=3.0'
)
