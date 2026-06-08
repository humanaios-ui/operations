from setuptools import setup, find_packages

setup(
    name="humanaios-funding",
    version="1.0.0",
    description="HumanAIOS Funding & Resource Pipeline",
    author="Night (HumanAIOS LLC)",
    author_email="aioshuman@gmail.com",
    url="https://github.com/humanaios-ui/humanaios-funding-pipeline",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.6,<3",
        "requests>=2.31,<3",
        "beautifulsoup4>=4.12,<5",
        "lxml>=5.0",
    ],
    entry_points={
        "console_scripts": [
            "haios-funding=humanaios_funding.cli:main",
            "haios-check=humanaios_funding.checker:run",
            "haios-report=humanaios_funding.report:generate",
        ]
    },
)
