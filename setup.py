from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

module_data = {}
with open(path.join(here, "showtime", "__init__.py")) as fp:
    exec(fp.read(), module_data)

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='showtime-cli',
    version=module_data['__version__'],
    packages=[
        'showtime',
    ],
    author='Evgeniy Vasilev',
    author_email='aquilax@gmail.com',
    license='MIT',
    description='Command line show tracker using the TVMaze public API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=module_data['__url__'],
    keywords='tv commandline application show tvmaze',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities',
    ],
    install_requires=[
        'cmd2==1.0.2',
        'python-tvmaze==1.0.1',
        'ratelimit==2.2.1',
        'tinydb==4.0.0',
        'terminaltables==3.1.0',
        'python-dateutil==2.8.1',
        'typing-extensions==3.7.4.2',
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
