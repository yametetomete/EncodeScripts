#!/usr/bin/env python3

import setuptools

name = "vivy_common"
version = "0.0.0"
release = "0.0.0"

setuptools.setup(
    name=name,
    version=release,
    author="louis",
    author_email="louis@poweris.moe",
    description="yametetomete vivy common module",
    packages=["vivy_common"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'vivy_common': ['py.typed', 'workraw-settings', 'final-settings', 'shaders/FSRCNNX_x2_56-16-4-1.glsl'],
    },
    python_requires='>=3.8',
)
