from setuptools import setup
from generators import __version__

setup(name='generators',
      version=__version__,
      description='Tool for Creating plantuml Files from rdf model.',
      url='https://github.com/dfriedenberger/generators.git',
      author='Dirk Friedenberger',
      author_email='projekte@frittenburger.de',
      license='GPLv3',
      packages=['generators', 'generators.util'],
      scripts=['bin/gen'],
      install_requires=[],
      zip_safe=False)
