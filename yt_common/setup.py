#!/usr/bin/env python3

import setuptools

name = "yt_common"
version = "0.0.0"
release = "0.0.0"

setuptools.setup(
    name=name,
    version=release,
    author="louis",
    author_email="louis@poweris.moe",
    description="yametetomete encodes common module",
    packages=["yt_common"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'yt_common': ['py.typed'],
    },
    python_requires='>=3.8',
)
