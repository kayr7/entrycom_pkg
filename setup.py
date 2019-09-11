import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="entrycom",
    version="0.0.1",
    author="Kay Rottmann",
    author_email="entrycom@kay-rottmann.de",
    description="Package to access 2n entrycom",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kayr7/entrycom",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)