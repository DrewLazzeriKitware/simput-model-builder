import click
import json
import re
import copy
import constants as const
from pathlib import Path
from yaml import load, Loader
from templates import model, name_param, dyn_view


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


def create_definitions(atts, path=None, dyn=False):
  path = atts if path is None else path
  # Add new attributes to the definition
  for att in atts:
    model['definitions'][att] = {
      'label': att.replace('_', ' '),
      # Dynamic views require an extra parameter so that the 
      # user can set its name.
      'parameters': name_param(path) if dyn else []
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
    param_id = parse_key(path.split('/')[-1])
    view[att_name] = dyn_view(att_name, label, f'{param_id}_')
    create_definitions([att_name], path, dyn=True)


def find_pararms(att, data, id='', params=None):
  if dynamic_token(id) and not dynamic_view(att):
    return

  # Find and return all keys that require input (the model parameters)
  params = {} if params is None else params
  for key, value in data.items():
    if isinstance(value, dict):
      if leaf_token(value) and not general_annotation(key):
        params[f'{id}{key}'] = value
      else:
        if dynamic_token(key) and dynamic_view(att):
          params[f'{parse_key(key)}_'] = value
        elif intermediate_token(value):
          params[f'{id}{key}'] = value['__value__']
        find_pararms(att, value, f'{id}{key}/', params)
  
  return params


def _create_parameters(path, id, data):
  # Create the parameter and set its attributes
  label = parse_parameter_label(id)

  # '.{dynamic_token}/path' -> 'dynamic_key_/path'
  param_id = f'{path}/{id}'
  for key in param_id.split('/'):
    if parse_key(key) != key:
      param_id = param_id.replace(key, f'{parse_key(key)}_')

  leaf_token = param_id.split('/')[-1]

  if general_annotation(leaf_token):
    param_id = param_id.replace(f'/{leaf_token}', '')
    label = param_id

  if leaf_token.endswith('_'):
    param_id = param_id.split('/')[-1]

  param = {
    'id': param_id,
    'label': label,
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
  domains = data.get('domains', {}).keys()
  param_type = next((key for key in domains if key in const.TYPES), False)
  if param_type == const.ENUM:
    param['ui'] = 'enum'
    enum = data.get('domains', {}).get(const.ENUM, {})
    enum_list = enum.get('enum_list', [])
    if all('v' in opt for opt in enum_list):
      # For now use the most recent version if more than one listed
      latest_version = list(enum_list.keys())[-1]
      enum_list = enum.get('enum_list', [])[latest_version]
    param['domain'] = {val: val for val in enum_list}
  else:
    if param_type == const.BOOL:
      param['type'] = 'bool'
    elif param_type == const.DOUBLE:
      param['type'] = 'double'
    elif param_type == const.INT:
      param['type'] = 'int'
    else:
      param['type'] = 'string'

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
  return re.findall('\{(.*)\}', key)[0]


def dynamic_token(key):
  return key.startswith('.{')


def dynamic_view(att):
  return 'Properties' in att


def general_annotation(key):
  return key.startswith('_')


def intermediate_token(item):
  return '__value__' in item.keys()


def leaf_token(item):
  return isinstance(item, dict) and 'help' in item.keys()


def parse_parameter_label(id):
  # '.{dynamic_token}/path' -> 'Dynamic Path'
  label = []
  for value in id.split('/'):
    item = parse_key(value)
    if item[0].islower():
      item = item.title()
    label.append(item.rsplit('_', 1)[0])
  return (' ').join(label)


def create_parameters(data, attr_paths):
  # Use the path associated with each attribute to find all of 
  # the attribute's parameters
  for att, path in attr_paths.items():
    params = []
    values = value_from_path(data, path.split('/'))
    param = find_pararms(att, values)
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
  if 'Core' in model['order']:
    order.insert(0, order.pop(order.index('Core')))
  model['order'] = order

  with open(f'{output}/model.json', 'w', encoding='utf8') as f:
    json.dump(model, f, ensure_ascii=False)

if __name__ == '__main__':
    cli()
