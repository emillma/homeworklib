import setuptools

requirements = ["numpy"]

setuptools.setup(
    name="handoutgen",
    version="0.0.1",
    author="Emil Martens",
    author_email="emil.martens@gmail.com",
    description="Package used to create handout from solution code",
    url="youtube.com",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=['hwlib_keywords', 'hwlib'],
    package_dir={
        'hwlib': 'hwlib',
        'hwlib_keywords': 'hwlib_keywords',
    },
    include_package_data=True,
    # package_data={},
    python_requires=">=3.8",
    entry_points={
        'console_scripts': ['hwlib_generate=hwlib.entry:call'], }
)
