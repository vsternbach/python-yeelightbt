from setuptools import setup

with open('yeelightble/version.py') as f: exec(f.read())

setup(
    name='yeelightble',

    version=__version__,
    description='Python library for interfacing with yeelight\'s bt lights',
    url='https://github.com/vsternbach/yeelightble',

    author='Vlad Sternbach',

    license='GPLv3',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
    ],

    keywords='yeelightble yeelight bluepy ble bluetooth candela',

    packages=['yeelightble'],

    python_requires='>=3.4',
    install_requires=['bluepy', 'construct==2.9.52', 'click', 'redis', 'retry'],
    entry_points={
        'console_scripts': [
            'yeelightble=yeelightble.cli:cli'
        ],
    },
    scripts=['systemd.py']
)
