from setuptools import setup, find_packages
from os.path import join, dirname


setup(
    name = "instagram",
    version = "2.1.0",
    author = "Oleg Yurchik",
    author_email = "oleg.yurchik@protonmail.com",
    url = "https://github.com/OlegYurchik/pyInstagram",
    description = "",
    long_description = open(join(dirname(__file__), "README.md")).read(),
    packages = find_packages(),
    install_requires = ["aiohttp", "pytest", "pytest-asyncio", "pytest-random-order", "requests"],
    test_suite = "tests/",
)
