from setuptools import setup, find_packages

setup(
    name="pibooth_delayed_google_sync",
    version="1.7.0",
    description="Plugin Pibooth : synchronisation différée Google Photos",
    author="auto",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["pibooth>=2.0.0"],
    entry_points={
        'pibooth': [
            'pibooth_delayed_google_sync = pibooth_delayed_google_sync'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
