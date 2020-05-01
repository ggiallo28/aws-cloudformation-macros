import json, re, troposphere
from troposphere import Parameter, Ref, Output, Sub
from troposphere import AWSObject as Resource
from troposphere import Join, Select, Export, Base64, Cidr, FindInMap, GetAtt, GetAZs, ImportValue
from troposphere.template_generator import TemplateGenerator
from troposphere import AWSObject, AWSProperty, Tags
from troposphere.compat import policytypes
from troposphere.validators import boolean, integer
from troposphere import Template
from cfn_flip import flip
from collections.abc import Iterable 

try:
    basestring
except NameError:
    basestring = str

class Git(AWSObject):
    resource_type = "Template::Git"

    props = {
        'Mode': (basestring, True),
        'Provider': (basestring, True),
        'Repo': (basestring, True),
        'Branch': (basestring, False),
        'Owner': (basestring, False),
        'OAuthToken': (basestring, False),
        'Path': (basestring, True),
        'Parameters': (dict, False),
        'NotificationARNs': ([basestring], False),
        'Tags': ((Tags, list), False),
        'TimeoutInMinutes': (integer, False),
        'TemplateBucket': (basestring, False),
        'TemplateKey': (basestring, False),
    }

class S3(AWSObject):
    resource_type = "Template::S3"

    props = {
        'Mode': (basestring, True),
        'Provider': (basestring, True),
        'Bucket': (basestring, True),
        'Key': (basestring, True),
        'Parameters': (dict, False),
        'NotificationARNs': ([basestring], False),
        'Tags': ((Tags, list), False),
        'TimeoutInMinutes': (integer, False),
        'TemplateBucket': (basestring, False)
    }

class TemplateLoader(TemplateGenerator):
    __create_key = object()
    __sub_regex = r"(\${[^}]+})"
    
    @classmethod
    def loads(cls, json_string):
        return TemplateLoader(cls.__create_key, cls._sub_to_join(json_string), CustomMembers = [S3, Git])
        
    @classmethod
    def init(cls):
        return TemplateLoader.loads({
            'Description': 'This template is the result of the merge.', 
            'Resources': {}
        })

    @classmethod
    def _sub_to_join(cls, template):
        template_clone = json.loads(json.dumps(template))
        cls._translate_value(template_clone)
        return json.loads(json.dumps(template_clone).replace('Fn::Sub','Fn::Join'))
    
    @classmethod
    def _translate_value(cls, template):
        if type(template) == dict:
            for key in template:
                if key == 'Fn::Sub':
                    try:
                        split_list = [s for s in re.split(cls.__sub_regex, template[key]) if len(s) > 0]
                    except TypeError:
                        raise('Error with', template[key], key)
                    for index, value in enumerate(split_list):
                        if re.match(cls.__sub_regex, value):
                            split_list[index] = Ref(value[2:-1]).data
                    template[key] = ["",split_list]
                cls._translate_value(template[key])
                
    def __init__(self, create_key, cf_template = None, **kwargs):
        assert(create_key == TemplateLoader.__create_key), \
            "TemplateLoader objects must be created using TemplateLoader.loads or TemplateLoader.init"
        super(TemplateLoader, self).__init__(cf_template, **kwargs)
        self._to_replace = []
        
    def __iter__(self):
        fields = list(vars(self).keys())
        for props in fields:
            yield (props, getattr(self, props))

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
        
    def __iadd__(self, other):
        for props in self:
            key, value = props
            if key.startswith('_') or key in ['version', 'transform']:
                continue

            if key == 'description':
                if value == '':
                    continue
                self[key] = "" if self[key] is None else self[key]
                other[key] = "" if other[key] is None else other[key]
                    
                self[key] = "{} {}".format(self[key], other[key])
            else:
                self[key] = {**self[key], **other[key]}
        return self
    
    @staticmethod
    def __setattr(bucket, key, value):
        if type(key) == int:
            bucket[key] = value
        if type(key) == str:
            if hasattr(bucket, key):
                setattr(bucket, key, value)
            else:
                bucket[key] = value
    
    def _create_export_resource(self, key, data):
        if type(data) == dict:
            [(data_key, data_value)] = data.items()
            return self._create_export_resource(data_key, data_value)
        if type(data) == list:
            for index, item in enumerate(data):
                if type(item) == str:
                    continue
                if type(item) == list:
                    data[index] = self._create_export_resource(None, item)
                if type(item) == dict:
                    [(item_key, item_value)] = item.items()
                    data[index] = self._create_export_resource(item_key, item_value)
        if key is not None:
            key = key.replace('Fn::', '')
            if type(data) == list:
                return getattr(troposphere, key)(*data)
            if type(data) == str:
                return getattr(troposphere, key)(data)
        return data

    def _fix_export(self, export):
        name = export.data['Name']
        for Obj in [Join, Select, Export, Base64, Cidr, FindInMap, GetAZs, ImportValue]:
            if isinstance(name, Obj):
                return export    
        [(key, value)] = name.items()
        return Export(self._create_export_resource(key, value))

    def _replace_ref(self, template, ref, prop):
        for (title, parameter) in self.parameters.items():
            if title == ref.data['Ref']:
                if 'Default' in parameter.properties:
                    if type(prop) == str and hasattr(template, prop):
                        setattr(template, prop, parameter.properties['Default'])
                    elif type(prop) == int or prop in template:
                        template[prop] = parameter.properties['Default']

    def _update_prefix(self, prefix):
        for (key, value) in self:
            if key.startswith('_') or key in ['description', 'parameters', 'version', 'transform'] or\
                type(value) in [str, int]:
                    continue

            prefixed_object = {}
            for arg in value:
                prefixed_object[prefix+arg] = value[arg]
            self[key] = prefixed_object
        
    def find_relations(self, to_replace=False, prefix=""):
        if len(prefix) > 0:
            self._update_prefix(prefix)
        self._find_relations(self, None, None, to_replace, prefix)
        
    def _find_relations(self, template, parent = None, parent_prop = None, to_replace=False, prefix=""):
        
        description_attr = 'description' if hasattr(template, 'description') else 'Description'
        if hasattr(template, description_attr) and len(prefix)>0:
            description = getattr(template, description_attr)
            if description is not None and not '[{}]'.format(prefix) in description:
                setattr(template, description_attr, '[{}] {}'.format(prefix, description))
                
        if type(template) in [str, int] or template is None:
            return

        if type(template) == dict:
            for key in template:
                self._find_relations(template[key], template, key, to_replace, prefix)

        if type(template) == list:
            for element in template:
                self._find_relations(element, template, template.index(element), to_replace, prefix)

        for Obj in [Join, Select, Export, Base64, Cidr, FindInMap, GetAZs, ImportValue]:
            if isinstance(template, Obj):
                self._find_relations(template.data, template, 'data', to_replace, prefix)    
                
        if isinstance(template, Resource) and len(prefix)>0:
            if not prefix in template.title:
                setattr(template, 'title', '{}{}'.format(prefix, template.title))

        if isinstance(template, Output):
            if hasattr(template, 'Export') and len(prefix) > 0:
                data = getattr(getattr(template, 'Export'), 'data')
                TemplateLoader.__setattr(data, 'Name', Join("-",[prefix, data['Name']]))
        
        if hasattr(template, 'Condition'):
            template.Condition = prefix + template.Condition

        if isinstance(template, Parameter):
            pass

        if isinstance(template, Ref):
            if not isinstance(parent, Parameter):
                self._replace_ref(parent, template, parent_prop)
            value = template.data['Ref']
            if value not in list(self.parameters.keys()) and not value.startswith('AWS::'):
                TemplateLoader.__setattr(parent, parent_prop, Ref(prefix + value))

        if isinstance(template, GetAtt):
            pass

        if hasattr(template, 'props'):
            for prop in {**template.props, **{'Conditions':(dict, False)}}:
                processed_prop = prop if hasattr(template, prop) else prop.lower()
                if hasattr(template, processed_prop):
                    snippet = getattr(template, processed_prop)

                    if isinstance(snippet, Export):
                        snippet = self._fix_export(snippet)
                        setattr(template, processed_prop, snippet)

                    self._find_relations(snippet, template, processed_prop, to_replace, prefix)
    
    def set_default_parameters(self, params):
        for title in self.parameters:
            parameter = self.parameters[title]
            if not 'Default' in parameter.properties:
                parameter.properties['Default'] = params[title]
    
    def del_default_on_parameters(self):
        for title in self.parameters:
            parameter = self.parameters[title]
            if 'Default' in parameter.properties:
                del parameter.properties['Default']

    def del_parameters(self):
        self.parameters = {}
                
    def to_json(self, keep_parameters=True):
        json_string = super().to_json()
        if keep_parameters:
            return json_string
        else:
            json_obj = json.loads(json_string)
            if 'Parameters' in json_obj:
                del json_obj['Parameters']
            return json.dumps(json_obj)
               
    def to_yaml(self, keep_parameters=True):
        json_string = self.to_json(keep_parameters)
        return flip(json_string)