import json
from troposphere.template_generator import TemplateGenerator
from troposphere import AWSObject, AWSProperty, Tags
from troposphere.compat import policytypes
from troposphere.validators import boolean
from troposphere import Template

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
    }

class S3(AWSObject):
    resource_type = "Template::S3"

    props = {
        'Mode': (basestring, True),
        'Provider': (basestring, True),
        'Bucket': (basestring, True),
        'Key': (basestring, True),
        'Parameters': (dict, False)
    }

class TemplateLoader(TemplateGenerator):
    @staticmethod
    def loads(json_string, prefix = ""):
        template = TemplateLoader(json_string, CustomMembers = [S3, Git])
        if prefix == "":
            return template
        else:
            json_string = json.loads(template._update_prefix(prefix))
            return TemplateLoader(json_string, CustomMembers = [S3, Git])
        
    @staticmethod
    def init():
        empty_template = Template()
        empty_template.description = "This template is the result of the merge."
        return TemplateLoader(json.loads(empty_template.to_json()), CustomMembers = [S3, Git])

    def __init__(self, cf_template, **kwargs):
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
    
    def _update_export(self, prefix, value):
        pass
    
    def _update_prefix(self, prefix):
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
                        export = self[key][resource].properties['Export'].data['Name']
                        export_key = list(export.keys())[0]
                        export_value = '{}-{}'.format(prefix, list(export.values())[0])
    
                        self[key][resource].properties['Export'].data['Name'][export_key] = export_value
                    except:
                        continue
                
        self._to_replace += [(prefix+prefix,prefix)]
        template_string = self.to_json()
        for src, dst in self._to_replace:
            template_string = template_string.replace(src, dst)
        
        return template_string    
