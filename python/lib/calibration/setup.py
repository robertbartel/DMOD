from setuptools import setup, find_namespace_packages

try:
    with open('README.md', 'r') as readme:
        long_description = readme.read()
except:
    long_description = ''

exec(open('dmod/calibration/_version.py').read())

setup(
    name='dmod-calibration',
    version=__version__,
    description='Client interface package for components of the National Water Model as a Service architecture',
    long_description=long_description,
    author='',
    author_email='',
    url='',
    license='',
    include_package_data=True,
    install_requires=['dmod-core>=0.1.0', 'ngen-cal'],
    packages=find_namespace_packages(include=['dmod.*'], exclude=('tests'))
)