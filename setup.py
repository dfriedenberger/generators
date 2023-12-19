from setuptools import setup
from generators import __version__

setup(name='generators',
      version=__version__,
      description='Tool for generating assets from rdf model.',
      long_description=open('README.md', encoding="UTF-8").read(),
      long_description_content_type='text/markdown',
      url='https://github.com/dfriedenberger/generators.git',
      author='Dirk Friedenberger',
      author_email='projekte@frittenburger.de',
      license='GPLv3',
      packages=['generators'],
      scripts=['bin/gen'],
      install_requires=['chevron'],
      zip_safe=False)
