from setuptools import find_packages, setup


setup(
    name="defect-detection-system",
    version="0.1.0",
    description="Reproducible MLOps system for steel surface defect detection",
    author="Aleksandr",
    packages=find_packages("src"),
    package_dir={"": "src"},
)

