from distutils.core import setup
setup(
  name='scrapium',
  packages=['scrapium'],
  version='0.9',
  description='Scraping tools',
  author='Alvaro Garcia Gomez',
  author_email='maxpowel@gmail.com',
  url='https://github.com/maxpowel/scrapium',
  download_url='https://github.com/maxpowel/scrapium/archive/master.zip',
  keywords=['web', 'scraping'],
  classifiers=['Topic :: Adaptive Technologies', 'Topic :: Software Development', 'Topic :: System', 'Topic :: Utilities'],
  install_requires=['beautifulsoup4', 'requests', 'retrying']
)
