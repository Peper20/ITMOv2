"""
Настройка пакета для обучающих практик ИТМО
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="itmo-python-practices",
    version="1.0.0",
    author="Преподаватели ИТМО",
    author_email="example@itmo.ru",
    description="Обучающие практики по Python для студентов ИТМО",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itmo-python-practices",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "itmo-practices=examples.hello_world:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
