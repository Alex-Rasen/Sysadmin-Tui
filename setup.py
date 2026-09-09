from setuptools import setup, find_packages

setup(
    name="sysadmin-tui",
    version="0.1.0",
    packages=find_packages(),          # Encuentra 'src' y sus subpaquetes
    include_package_data=True,
    install_requires=[
        "textual",
        "pydantic",
        "pydantic-settings",
        "PyYAML",
    ],
    entry_points={
        "console_scripts": [
            "sysadmin-tui=src.main:main",
        ],
    },
)
