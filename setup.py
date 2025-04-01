from setuptools import setup, find_packages

setup(
    name="asshm",
    version="1.0.0",
    description="Advanced SSH Manager - A modern, portable session manager for PuTTY and WinSCP connections",
    author="McDevStudios",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyQt6>=6.6.0",
        "pyinstaller>=6.3.0"
    ],
    entry_points={
        "console_scripts": [
            "asshm=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.10",
)
