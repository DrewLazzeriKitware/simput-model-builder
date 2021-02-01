# Base Model
model = {
  'output': {},
  'defaultActiveView': 'Core',
  'order': [],
  'views': {},
  'definitions': {}
}

# Name Parameter
def name_param(att_name):
  parent, param_id = att_name.split('/')
  param_id = param_id.replace('.{', '').replace('}', '')
  name = [{
    'id': f'{param_id}_',
    'label': 'Name',
    'size': 1,
    'type': 'string',
    'help': f'User-defined instance from {parent} Names'
  }]

  return name

# Dynamic View Base
def dyn_view(att_name, label, param_id):
  view = {
    'label': label,
    'attributes': [att_name],
    'size': -1,
    'hooks': [
      {
        'type': 'copyParameterToViewName',
        'attribute': f'{att_name}.{param_id}',
      }
    ]
  }

  return view
