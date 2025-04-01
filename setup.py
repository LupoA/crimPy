# setup.py
from setuptools import setup, find_packages

setup(
    name="crimpy",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "numpy",
        "matplotlib",
        "PyQt5"
    ],
)
