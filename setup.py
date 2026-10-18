from setuptools import setup, find_packages

setup(
    name="spotlight-music",
    version="1.0.0",
    description="Ultra-lightweight background music player with Spotlight-style search",
    author="Emerson Madrid",
    packages=find_packages(),
    py_modules=["main", "player", "lyrics"],
    install_requires=[
        "yt-dlp>=2024.0.0",
    ],
    entry_points={
        "console_scripts": [
            "spotlight-music=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
