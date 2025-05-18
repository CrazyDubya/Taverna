from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="living-rusted-tankard",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A text-based RPG set in a mysterious tavern where time moves forward",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/living-rusted-tankard",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Role-Playing",
    ],
    python_requires='>=3.8',
    install_requires=[
        "pydantic>=2.0.0",
        "typing-extensions>=4.7.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "black>=23.7.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tavern=cli:main",
        ],
    },
)
