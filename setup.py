from setuptools import setup

setup(
  name='model_builder',
  version='0.1',
  py_modules=['model_builder'],
  install_requires=[
    'Click',
    'pyyaml'
  ],
  entry_points='''
    [console_scripts]
    model_builder=model_builder:cli
  ''',
)