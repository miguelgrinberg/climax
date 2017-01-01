"""
climax
-----
Decorator based argparse wrapper inspired by click.
"""
from setuptools import setup


setup(
    name='climax',
    version='0.3.0',
    url='http://github.com/miguelgrinberg/climax/',
    license='MIT',
    author='Miguel Grinberg',
    author_email='miguelgrinberg50@gmail.com',
    description='Decorator based argparse wrapper inspired by click',
    long_description=__doc__,
    py_modules=['climax'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[],
    tests_require=[
        'mock',
        'coverage'
    ],
    test_suite='test_climax',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
