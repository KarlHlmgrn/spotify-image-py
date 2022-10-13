from setuptools import setup, find_packages
from codecs import open

with open("README.md", "r") as f:
    long_description = f.read()

def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as fp:
        return fp.read().strip().splitlines()

requirements = read_requirements('requirements.txt')

setup(
    name='spotify-image-py',
    version='1.0',
    author='KarlHlmgrn',
    author_email='karlhlmgrn.github@gmail.com',
    description='Simple library to get currently playing song from Spotify, optimal for small projects',
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/KarlHlmgrn/spotify-image-py',
    packages=find_packages()
)