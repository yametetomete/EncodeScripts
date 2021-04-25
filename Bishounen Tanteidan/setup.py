#!/usr/bin/env python3

import setuptools

name = "tanteidan_common"
version = "0.0.0"
release = "0.0.0"

setuptools.setup(
    name=name,
    version=release,
    author="louis",
    author_email="louis@poweris.moe",
    description="yametetomete pretty boy detective club common module",
    packages=["tanteidan_common"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'tenteidan-common': ['py.typed', 'workraw-settings', 'final-settings'],
    },
    python_requires='>=3.8',
)
