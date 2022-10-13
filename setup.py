from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="spotify-image-py",
    version="1.0",
    author="KarlHlmgrn",
    author_email="karlhlmgrn.github@gmail.com",
    description="Simple library to get currently playing song from Spotify, optimal for small projects",
    install_requires=[
        "Flask>=2.2.2",
        "Pillow>=9.2.0",
        "qrcode>=7.3.1",
        "requests>=2.25.1",
        "six>=1.16.0"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KarlHlmgrn/spotify-image-py",
    packages=find_packages()
)
