#!/usr/bin/env python3

import setuptools

name = "pripri_common"
version = "0.0.0"
release = "0.0.0"

setuptools.setup(
    name=name,
    version=release,
    author="louis",
    author_email="louis@poweris.moe",
    description="princess principal common module",
    packages=["pripri_common"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'pripri_common': ['py.typed', 'final-settings'],
    },
    python_requires='>=3.8',
)
