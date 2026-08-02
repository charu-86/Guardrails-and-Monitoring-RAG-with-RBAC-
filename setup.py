"""
Setup script for Guardrails and Monitoring RAG with RBAC.
"""

from setuptools import setup, find_packages


def parse_requirements(filename: str) -> list:
    """Parse requirements.txt and return a list of dependencies."""
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    requirements = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)
    return requirements


setup(
    name="guardrails-monitoring-rag-rbac",
    version="0.1.0",
    author="Charu Kashyap",
    description=(
        "A comprehensive framework for implementing guardrails, monitoring, "
        "and Role-Based Access Control (RBAC) in RAG systems."
    ),
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/charu-86/Guardrails-and-Monitoring-RAG-with-RBAC-",
    packages=find_packages(exclude=["tests*", "examples*"]),
    python_requires=">=3.8",
    install_requires=parse_requirements("requirements.txt"),
    extras_require={
        "dev": [
            "pytest>=7.3",
            "black",
            "flake8",
            "mypy",
        ],
    },
    package_data={
        "config": ["config.yaml"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
    ],
)
