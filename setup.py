from setuptools import setup, find_packages

setup(
    name="humanaios-operations",
    version="1.0.0",
    description="HumanAIOS Operations Hub — Integrated funding discovery, research profiling, and proposal tracking",
    author="HumanAIOS",
    author_email="info@humanaios.ai",
    url="https://github.com/humanaios-ui/operations",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31,<3",
    ],
    entry_points={
        "console_scripts": [
            "haios=humanaios_operations.cli:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
