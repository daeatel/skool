try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import pip

# numpy and scipy are necessary for scikit-learn
pip.main(['install', 'numpy'])
pip.main(['install', 'scipy'])

setup(
    name='skool',
    version='0.1.0',
    author='Michal Vlasak',
    author_email='daeatel@gmail.com',
    packages=['skool'],
    scripts=[],
    url='https://github.com/daeatel/skool',
    license='LICENSE.txt',
    description='Online school package',
    long_description=open('README.md').read(),
    install_requires=[
        "BeautifulSoup == 3.2.1",
        "blinker == 1.3",
        "Distance == 0.1.3",
        "elasticsearch == 1.4.0",
        "iso8601 == 0.1.10",
        "jusText == 2.1.1",
        "lmdb == 0.84",
        "mongoengine == 0.8.7",
        "pymongo == 2.8",
        "pytz == 2015.2",
        "requests == 2.6.0",
        "scikit-learn == 0.15.2",
        "sumy == 0.3.0",
        "textblob == 0.9.0",
    ],
)
