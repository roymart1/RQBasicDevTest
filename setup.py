import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="frwmpr",
    version="0.0.1",
    author="Martin-Pierre Roy",
    author_email="mroy@zentelia.com",
    description="auto fw test package 001",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/robotiqinc/automatic_testing/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)