import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# Parse version from _version.py in package directory
# See https://packaging.python.org/guides/single-sourcing-package-version/#single-sourcing-the-version
version = {}
with open("src/alfred3/_version.py") as f:
    exec(f.read(), version)

setuptools.setup(
    name="alfred3",
    version=version["__version__"],
    author="Christian Treffenstädt, Johannes Brachem, Paul Wiemann",
    author_email="treffenstaedt@psych.uni-goettingen.de",
    description="A library for rapid development of dynamic and interactive online experiments in the social sciences.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ctreffe/alfred",
    packages=setuptools.find_packages("src"),
    package_data={
        "alfred3": [
            "files/*",
            "static/css/*",
            "static/img/*",
            "static/js/*",
            "templates/*",
            "element/templates/*",
            "element/templates/html/*",
            "element/templates/js/*"
        ]
    },
    package_dir={"": "src"},
    install_requires=[
        "pymongo>=3.10",
        "cryptography>=3.4",
        "jinja2>=2.11",
        "Flask>=1.1",
        "thesmuggler>=1.0",
        "Click>=7.1",
        "emoji>=1.2",
        "cmarkgfm>=0.5",
        "requests>=2.25",
        "bleach>=3.3"
    ],
    entry_points="""
    [console_scripts]
    alfred3=alfred3.cli:cli
    """,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
