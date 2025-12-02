from setuptools import setup, find_packages

setup(
    name="risk-core",
    version="0.1.0",
    description="Pure Python risk calculation library - no HTTP, no DB",
    author="A.___",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
        ]
    },
)
