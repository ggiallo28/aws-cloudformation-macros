from troposphere import AWSObject, AWSHelperFn, AWSProperty
from troposphere import Tags, Ref, Join, GetAtt, Export, Template, Join
from troposphere.template_generator import TemplateGenerator
from troposphere.validators import boolean, integer
from troposphere import cloudformation
import os

BRANCH_DEFAULT = 'master'

TEMPLATE_NAME_DEFAULT = 'template.yaml'

ASSERT_MESSAGE = """Template format error: {} value in {} is invalid. 
The value must not depend on any resources or imported values. 
Check if Parameter exists."""

DEFAULT_BUCKET = os.environ.get(
    'DEFAULT_BUCKET', 'macro-template-default-831650818513-us-east-1')

MACRO_NAME = 'Template'

MACRO_SEPARATOR = '::'

MACRO_PREFIX = MACRO_NAME + MACRO_SEPARATOR

setattr(TemplateGenerator, 'add_description', TemplateGenerator.set_description)
setattr(TemplateGenerator, 'add_version', TemplateGenerator.set_version)

def is_macro(x):
	return False
setattr(AWSObject, 'is_macro', is_macro)

def extract(x):
	return list(x.data.values()).pop()
setattr(AWSHelperFn, 'extract', extract)

class TemplateLoaderCollection():

	def __init__(self):
		self.templates = {}

	def __getitem__(self, key):
		return self.templates[key]

	def __setitem__(self, key, value):
		self.templates[key] = value

	def __iter__(self):
		for key in self.templates:
			yield (key, *self.templates[key])

	def update(self, data):
		self.templates.update(data)

	def get(self, key, default=None):
		return self.templates.get(key, default)

	def items(self):
		return self.templates.items()

	def contains(self, key):
		return key in self.templates

	def to_dict(self):
		return self.templates

#def prefix_prp(self, template):
#	self.resource = template._prefix_functions(self.resource)
#setattr(AWSProperty, 'prefix', prefix_prp)
#
#def prefix_fn(self, template):
#    self.data = template._prefix_functions(self.data)
#setattr(AWSHelperFn, 'prefix', prefix_fn)
#
#def prefix_tags(self, template):
#    self.tags = template._prefix_functions(self.tags)
#setattr(Tags, 'prefix', prefix_tags)
#
#def prefix_getatt(self, template):
#    self.data['Fn::GetAtt'][0] = template._prefix + self.data['Fn::GetAtt'][0]
#setattr(GetAtt, 'prefix', prefix_getatt)
#
#def prefix_ref(self, template):
#    self.data['Ref'] = template._prefix + self.data['Ref']
#setattr(Ref, 'prefix', prefix_ref)
#
#def export_name_parser(template, data):
#    parser = TemplateGenerator({
#        'Resources': {
#            'ExportParser': {
#                'Type': 'Custom::Parser',
#                'Properties': {
#                    'Parser': data
#                }
#            }
#        }
#    })
#    return parser.resources['ExportParser'].resource['Properties']['Parser']
#
#def prefix_export(self, template):
#    if type(self.data['Name']) == dict:
#        self.data['Name'] = export_name_parser(template, self.data['Name'])
#        self.data['Name'].prefix(template)
#    self.data['Name'] = Join("", [template._prefix, self.data['Name']]).to_dict() 
#setattr(Export, 'prefix', prefix_export)
#
#def _prefix_functions(self, data):
#    if type(data) == dict:
#        return dict(filter(lambda x: not x is None, map(self._prefix_functions, data.items())))
#    if type(data) == list:
#        return list(filter(lambda x: not x is None, map(self._prefix_functions, data)))
#    if type(data) == tuple:
#        key, value = data
#        return (key, self._prefix_functions(value))
#    if type(data) in [str, int]:
#        return data
#    data.prefix(self)  
#    return data
#setattr(TemplateGenerator, '_prefix_functions', _prefix_functions)   
#
#def prefix_outputs(self):
#    keys = list(self.outputs.keys())
#    for k in keys:
#        self.outputs[self._prefix + k] = self.outputs.pop(k)
#        self.outputs[self._prefix + k].title = self._prefix + k
#        self._prefix_functions(self.outputs[self._prefix + k].resource)           
#setattr(TemplateGenerator, '_prefix_outputs', prefix_outputs)
#
#def prefix_resources(self):
#    keys = list(self.resources.keys())
#    for k in keys:
#        self.resources[self._prefix + k] = self.resources.pop(k)
#        self.resources[self._prefix + k].title = self._prefix + k
#        self._prefix_functions(self.resources[self._prefix + k].resource)
#setattr(TemplateGenerator, '_prefix_resources', prefix_resources)
#