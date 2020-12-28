# Base Model
model = {
  'output': {},
  'defaultActiveView': 'Core',
  'order': [],
  'views': {},
  'definitions': {}
}

# Name Parameter
name = {
  'id': 'name',
  'label': 'Name',
  'size': 1,
  'type': 'string'
}

# Dynamic View Base
def dyn_view(label, att_name):
  view = {
    'label': label,
    'attributes': [att_name],
    'size': -1,
    'hooks': [
      {
        'type': 'copyParameterToViewName',
        'attribute': f'{att_name}.name',
      }
    ]
  }

  return view
