from setuptools import setup, find_packages

setup(
    name="podcast-rss-processor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "lxml",
        "openai",
        "python-dotenv",
        "pytest",
        "pytest-cov"
    ],
    python_requires=">=3.13",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for ingesting, cleaning, and tagging podcast RSS feeds",
    keywords="podcast, rss, feed, processing, tagging",
    url="https://github.com/yourusername/podcast-rss-processor",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.13",
    ],
) 