from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='showtime-cli',
    version='0.2.1',
    packages=[
        'showtime',
    ],
    author='Evgeniy Vasilev',
    author_email='aquilax@gmail.com',
    license='MIT',
    description='Command line show tracker using the TVMaze public API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/aquilax/showtime',
    keywords='tv commandline application show tvmaze',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities',
    ],
    install_requires=[
        'cmd2==0.7.5',
        'python-tvmaze==1.0.1',
        'ratelimit==1.4.0',
        'tinydb==3.3.1',
        'terminaltables==3.1.0',
        'python-dateutil==2.6.1',
    ],
    extras_require={
        'test': ['tox'],
    },
    entry_points={
        'console_scripts':
        [
            'showtime = showtime.command:main'
        ]
    }
)
