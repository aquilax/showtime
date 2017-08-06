from distutils.core import setup

setup(
    name='Showtime',
    version='0.1',
    packages=[
        'showtime',
    ],
    license='LICENSE',
    long_description=open('README.md').read(),
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
            'showtime = showtime.command:main'
        ]
    }
)
