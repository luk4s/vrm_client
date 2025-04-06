from setuptools import setup, find_packages

setup(
    name="vrm_client",
    version="1.0.0",
    license="MIT",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov"
        ],
    },
    entry_points={
        'console_scripts': [
            'vrm-client=vrm_client.docker_entrypoint:main',
        ],
    },
    python_requires='>=3.10',
    author="Lukáš Pokorný",
    author_email="admin@luk4s.cz",
    description="VRM API Client with InfluxDB integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/luk4s/vrm-client",
    keywords="victron,vrm,solar,energy,monitoring,influxdb",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)