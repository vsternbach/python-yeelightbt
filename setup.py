from setuptools import setup

with open('yeelightbtle/version.py') as f: exec(f.read())

setup(
    name='yeelightbtle',

    version=__version__,
    description='Python library for interfacing with yeelight\'s bt lights',
    url='https://github.com/vsternbach/yeelightbtle',

    author='Vlad Sternbach',

    license='GPLv3',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
    ],

    keywords='yeelight bluepy',

    packages=['yeelightbtle'],

    python_requires='>=3.4',
    install_requires=['bluepy', 'construct==2.9.52', 'click', 'decouple', 'redis'],
    entry_points={
        'console_scripts': [
            'yeelightbtle=yeelightbtle.cli:cli',
            'yeelightbtled=yeelightbtle.daemon:daemon'
        ],
    },
    # scripts=['install.py']
)
