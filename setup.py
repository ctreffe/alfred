import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

version = {}
with open('alfred3/_version.py') as f:
    exec(f.read(), version)

setuptools.setup(
    name="alfred3",
    version=version["__version__"],
    author="Christian Treffenstädt, Paul Wiemann, Johannes Brachem",
    author_email="treffenstaedt@psych.uni-goettingen.de",
    description="A library for rapid development of dynamic and interactive online experiments in the social sciences.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ctreffe/alfred3-dbtools",

    packages=setuptools.find_packages(),
    package_data={"alfred3": ["files/*", "staic/*", "templates/*"]},

    install_requires=[
        "pymongo>=3.10",
        "future>=0.18",
        "cryptography>=2.9",
        "jinja2>=2.11",
        "Flask>=1.1",
        "xmltodict>=0.12",
        "PySide2>=5.2",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.5",
)

