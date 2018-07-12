from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name = 'instaparser',
    version = '1.0',
    
    author = "Oleg Yurchik",
    author_email = "oleg.yurchik@protonmail.com",
    
    description = "",
    long_description = open(join(dirname(__file__), 'README.md')).read(),
    
    packages = find_packages(),
    install_requires = [],
)
