from setuptools import setup, find_namespace_packages

with open('README.md', 'r') as readme:
    long_description = readme.read()

exec(open('dmod/modeldata/_version.py').read())

setup(
    name='dmod-modeldata',
    version=__version__,
    description='',
    long_description=long_description,
    author='',
    author_email='',
    url='',
    license='',
    install_requires=['numpy>=1.19.5', 'pandas', 'geopandas', 'dmod-communication>=0.3.0',
                      'hypy@git+https://github.com/noaa-owp/hypy@master#egg=hypy&subdirectory=python',
                      ],
    packages=find_namespace_packages(exclude=('tests', 'schemas', 'ssl', 'src'))
)
