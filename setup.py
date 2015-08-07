try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

    from setuptools import setup, find_packages


setup(
    name='poll',
    version='0.1.1',
    author="Benjamin Hodgson",
    author_email="benjamin.hodgson@huddle.net",
    url="https://github.com/benjamin-hodgson/build",
    description="Utilities for polling, retrying, and exception handling",
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=["setuptools"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
