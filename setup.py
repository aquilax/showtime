from setuptools import setup

setup(
    name='showtime-cli',
    version='0.1',
    packages=[
        'showtime-cli',
    ],
    author = 'Evgeniy Vasilev',
    author_email = 'aquilax@gmail.com',
    description = 'Command line show tracker using the TVMaze public API',
    url = 'https://github.com/aquilax/showtime',
    keywords = ['tv', 'command line', 'application', 'show', 'tvmaze'],
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities',
    ],
    install_requires = [
        'cmd2==0.7.5',
        'python-tvmaze==1.0.1',
        'ratelimit==1.4.0',
        'tinydb==3.3.1',
        'terminaltables==3.1.0',
    ],
    entry_points={
        'console_scripts':
        [
            'showtime-cli = showtime.command:main'
        ]
    }
)
