import click
import json
import re
import copy
import constants as const
from pathlib import Path
from yaml import load, Loader
from templates import model, name, dyn_view


exts = ['.yaml']


def create_view(data, fname):
  # By default treat each new file as a view
  view = model['views']
  atts, new_views, attr_paths = check_attributes(data)
  if atts:
    model['order'].append(fname)
    view[fname] = { 'label': fname, 'attributes': atts }
    create_definitions(atts)

  return new_views, attr_paths


def check_attributes(data, attr_paths=None):
  # If one of the attributes of a view is a user defined key,
  # break it out into its own view instead
  attr_paths = {} if attr_paths is None else attr_paths
  atts, dyn_views = [], []
  for att in data.keys():
    keys = data[att].keys()
    children = filter_keys(keys, ['.{', '_'], included=False)
    dyn_view = filter_keys(keys, ['.{'], included=True)
    if dyn_view:
      dyn_views.extend([f'{att}/{view}' for view in dyn_view])
    if children:
      atts.append(att)
      attr_paths[att] = att

  return atts, dyn_views, attr_paths


def create_definitions(atts, dyn=False):
  # Add new attributes to the definition
  for att in atts:
    model['definitions'][att] = {
      'label': att.replace('_', ' '),
      # Dynamic views require an extra parameter so that the 
      # user can set its name.
      'parameters': [name] if dyn else []
    }


def create_dynamic_view(data, views, fname, attr_paths):
  view = model['views']
  for path in views:
    keys = path.split('/')
    # Avoid repetitive naming, i.e. "Geom GeomInput Properties"
    name = f'{fname} {keys[0]}' if not keys[0].startswith(fname) else f'{keys[0]}'
    label = f'{name} Properties'

    att_name = label.replace(' ', '_')
    attr_paths[att_name] = path
    model['order'].append(att_name)
    view[att_name] = dyn_view(label, att_name)
    create_definitions([att_name], dyn=True)


def find_pararms(data, id='', params=None):
  # Find and return all keys that require input (the model parameters)
  params = {} if params is None else params
  for key, value in data.items():
    if isinstance(value, dict):
      if 'help' not in value.keys():
        find_pararms(value, f'{key}/', params)
      else:
        params[f'{id}{key}'] = value
  
  return params


def _create_parameters(path, id, data):
  # Create the parameter and set its attributes
  l1, *l2 = id.split('/')
  l1 = parse_key(l1).rsplit('_', 1)[0]
  param = {
    'id': f'{path}/{id}',
    'label': (' ').join([l1, *l2]),
    'size': 1
  }

  if const.MANDATORY in data.get('domains', {}).keys():
    # Indicate parameter is mandatory
    param['label'] = f'{param["label"]} (REQUIRED)'

  param_type = _set_type(param, data)

  default = data.get('default', None)
  if default is not None:
    # Set the default value if given
    param['default'] = [default] if param_type == const.ENUM else default

  # Clean up and add the help text
  help_text = data.get('help', '').strip('\n').split('] ', 1)
  param['help'] = help_text[1] if len(help_text) > 1 else help_text[0]

  return param


def _set_type(param, data):
  # Determine and set parameter type
  param_type = list(data.get('domains', {}).keys())[0]
  if param_type == const.ENUM:
    param['ui'] = 'enum'
    enum_list = data.get('domains', {}).get(const.ENUM, {}).get('enum_list', [])
    param['domain'] = {val: val for val in enum_list}
  else:
    if param_type == const.STRING:
      param['type'] = 'string'
    elif param_type == const.BOOL:
      param['type'] = 'bool'
    elif param_type == const.DOUBLE:
      param['type'] = 'double'
    elif param_type == const.INT:
      param['type'] = 'int'

  return param_type


def value_from_path(data, path):
  # Takes string path in form "path/to/value"
  return value_from_path(data[path[0]], path[1:]) if path else data


def filter_keys(keys, delimiters, included=False):
  for d in delimiters:
    keys = [k for k in keys if (d in k) is included]
  return keys


def parse_key(key):
  if not key.startswith('.{'):
    return key
  return re.findall('\{(.*)\}', key)[0].title()


def create_parameters(data, attr_paths):
  # Use the path associated with each attribute to find all of 
  # the attribute's parameters
  for att, path in attr_paths.items():
    params = []
    values = value_from_path(data, path.split('/'))
    keys = [k for k in values.keys() if not k.startswith('_') or k.startswith('.{')]
    param = find_pararms(values)
    for id, p in param.items():
      params.append(_create_parameters(path, id, p))
    model['definitions'][att]['parameters'].extend(params)


@click.command()
@click.option('-o', '--output', default='.',
              type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
              help='The directory to output the model file to. If no output ' +
              'is provided the file will be created in the current directory.')
@click.option('-d', '--directory', default=None,
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
              help='The directory of definition files.')
@click.option('-f', '--file', default=None, multiple=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
              help='A definition file to use.')
def cli(output, directory, file):
  """Accepts a single file, list of files, or directory name."""
  files = Path(directory).iterdir() if directory else [Path(f) for f in file]

  for f in files:
    # Create the views, attributes, and parameters needed
    # for each file
    fname = f.stem.capitalize()
    with open(f) as value:
      data = load(value, Loader=Loader)
      new_views, attr_paths = create_view(data, fname)
      if new_views:
        create_dynamic_view(data, new_views, fname, attr_paths)
      create_parameters(data, attr_paths)

  # For now core is first
  order = sorted(model['order'])
  order.insert(0, order.pop(order.index('Core')))
  model['order'] = order

  with open(f'{output}/model.json', 'w', encoding='utf8') as f:
    json.dump(model, f, ensure_ascii=False)
