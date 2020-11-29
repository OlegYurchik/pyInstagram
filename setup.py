from setuptools import setup, find_packages
from os.path import join, dirname


setup(
    name="pyinstagram",
    version="3.0.0",
    author="Oleg Yurchik",
    author_email="oleg.yurchik@protonmail.com",
    url="https://github.com/OlegYurchik/pyinstagram",
    description="",
    long_description=open(join(dirname(__file__), "README.md")).read(),
    packages=find_packages(),
    install_requires=["aiohttp"],
    tests_require=["pytest", "pytest-asyncio", "pytest-random-order"],
    test_suite="pyinstagram.tests",
)
