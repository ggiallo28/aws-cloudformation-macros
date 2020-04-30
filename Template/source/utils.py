import json, re
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
    
    @classmethod
    def loads(cls, json_string):
        return TemplateLoader(cls.__create_key, json_string, CustomMembers = [S3, Git])
        
    @classmethod
    def init():
        return TemplateLoader.loads({
            'Description': 'This template is the result of the merge.', 
            'Resources': {}
        })
    
    def _find_functions(self):
        return []

    def __init__(self, create_key, cf_template = None, **kwargs):
        assert(create_key == TemplateLoader.__create_key), \
            "TemplateLoader objects must be created using TemplateLoader.loads or TemplateLoader.init"
        super(TemplateLoader, self).__init__(cf_template, **kwargs)
        
        self.functions = self._find_functions()
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
    
    def _replace_value(self, value):
        for src, dst in self._to_replace:
            value = re.sub('^'+src+'$', dst, value)
            value = re.sub('\${'+src+'}', '${'+dst+'}', value)
        return value

    def _rename_references(self, snippet):
        if type(snippet) in [str, int]:
            return

        for key in snippet:
            if type(key) == str\
                and type(snippet) == dict\
                    and type(snippet[key]) == str\
                        and (key.startswith('Fn::') or key in ['Ref','Condition']):         
                            snippet[key] = self._replace_value(snippet[key])
            else:
                self._rename_references(snippet[key] if type(snippet) == dict else key)
            
    def _update_des(self, prefix, value):
        return '[{}] {}'.format(prefix, value)

    def _update_dict(self, prefix, value):
        output = {}
        for k in value:
            output[prefix+k] = value[k]
            
            pair = (k, prefix+k)
            if not pair in self._to_replace:
                self._to_replace += [pair]
                
        return output
    
    def _update_export(self, prefix, key, value):
        if key == 'Fn::Sub':
            return '{}-{}'.format(prefix, value)
        elif key == 'Fn::Base64':
            return value
        elif key == 'Fn::Cidr':
            return value
        elif key == 'Fn::FindInMap':
            return value
        elif key == 'Fn::FindInMap':
            return value
        elif key == 'Fn::GetAtt':
            return value
        elif key == 'Fn::GetAZs':
            return value
        elif key == 'Fn::ImportValue':
            return value
        elif key == 'Fn::Join':
            return value
        elif key == 'Fn::Select':
            return value
        elif key == 'Fn::Split':
            return value
        elif key == 'Fn::Sub':
            return value
        elif key == 'Fn::Transform':
            return value
        elif key == 'Ref':
            return value
        else:
            return value
    
    def update_prefix(self, prefix):
        for props in self:
            key, value = props
            if key.startswith('_') or key in ['version', 'transform']:
                continue
                
            if key == 'description':
                if value == '':
                    continue
                    
                self[key] = self._update_des(prefix, value)
            else:
                self[key] = self._update_dict(prefix, value)
                for title in self[key]:
                    self[key][title].title = title
            if key == 'outputs':
                for resource in self[key]:
                    try:
                        [(export_key, export_val)] = self[key][resource].properties['Export'].data['Name'].items()
                        self[key][resource].properties['Export'].data['Name'][export_key] =\
                                self._update_export(prefix, export_key, export_val)
                    except Exception as e:
                        continue
                        
        template = json.loads(self.to_json())
        self._rename_references(template)
        
        return TemplateLoader(template, CustomMembers = [S3, Git])    
