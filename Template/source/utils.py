import json, re, troposphere
from troposphere import Parameter, Ref, Output, Sub, Condition
from troposphere import AWSObject as Resource, And
from troposphere import Join, Select, Export, Base64, Cidr, FindInMap, GetAtt, GetAZs, ImportValue
from troposphere.template_generator import TemplateGenerator
from troposphere import AWSObject, AWSProperty, Tags
from troposphere.compat import policytypes
from troposphere.validators import boolean, integer
from troposphere import Template
from cfn_flip import flip
from collections.abc import Iterable
from resources import S3, Git
from troposphere import cloudformation, Join, Ref
import logging
import boto3
import io

s3 = boto3.client('s3')

def s3_export(request_id, bucket_name, object_key, troposphere_template, template_params):
    if isinstance(bucket_name, Ref):
      bucket_name = params[bucket_name.data['Ref']]

    if isinstance(object_key, Ref):
      object_key = params[object_key.data['Ref']]

    if bucket_name is None:
        bucket_name = DEFAULT_BUCKET
        object_key = '{}/{}'.format(request_id, object_key)

    logging.info('Upload {} in {}'.format(object_key, bucket_name))
    template = troposphere_template.to_json()
    s3.upload_fileobj(io.BytesIO(template.encode()), bucket_name, object_key)

    return Join('',['https://', bucket_name, '.s3.amazonaws.com/', object_key])

def get_stack_template(request_id, resource_obj, resource_id, template_params, import_template):
    bucket_name = resource_obj.properties.get('TemplateBucket', None)
    object_key = resource_obj.properties.get('TemplateKey',\
        resource_obj.properties.get('Path',\
            resource_obj.properties.get('Key', None)))

    nested_stack = cloudformation.Stack(title = resource_id)

    for attr in nested_stack.attributes:
      if hasattr(resource_obj, attr):
        setattr(nested_stack, attr, getattr(resource_obj, attr))

    for prop in nested_stack.propnames:
      if prop in resource_obj.properties:
        setattr(nested_stack, prop, resource_obj.properties.get(prop))
    nested_stack.TemplateURL = s3_export(request_id, bucket_name, object_key, import_template, template_params)

    return nested_stack

class TemplateLoader(TemplateGenerator):
    __create_key = object()
    __macro_name = 'Template::'
    
    @classmethod
    def loads(cls, json_string):
        return TemplateLoader(cls.__create_key, json_string, CustomMembers = [S3, Git])
        
    @classmethod
    def init(cls):
        return TemplateLoader.loads({
            'Description': 'This template is the result of the merge.', 
            'Resources': {}
        })
                
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

    def _translate(self, data):
        if type(data) == dict:
            return dict(map(self._translate, data.items()))
        if type(data) == list:
            return list(map(self._translate, data))
        if type(data) == tuple:
            key, value = data
            if key == 'Ref':
                if value in self.logical_ids:
                    value = self.prefix + value
            if key == "Fn::GetAtt":
                if value[0] in self.logical_ids:
                    value[0] = self.prefix + value[0]
            if key == "Export":
                value["Name"] = { "Fn::Join" : [ "-", [ self.prefix,  value["Name"] ] ] }
            if key in self.logical_ids:
                key = self.prefix + key
            return (key, self._translate(value))

        if type(data) == str:
            if data.replace(self.__macro_name, "") in self.logical_ids:
                data = self.__macro_name + self.prefix + data.replace(self.__macro_name, "")            

        return data

    def translate(self, prefix):
        self.prefix = prefix
        self.logical_ids = []
        for _,value in self:
            if type(value) == dict: 
                self.logical_ids += list(value.keys())

        json_string = json.loads(self.to_json())
        json_string = self._translate(json_string)
        return self.loads(json_string)

    def _get_values(self, key, import_templates):
        key = key.replace(self.__macro_name, "")
        if key in import_templates:
            _, related_inline_template = import_templates[key]
            return [title for title in related_inline_template.resources]
        else:
            return [key] # Is Nested Resource

    def set_attrs(self, top_level_resource, import_templates):

        if hasattr(top_level_resource, 'DeletionPolicy'):
            ## Override
            value = getattr(top_level_resource, 'DeletionPolicy')
            for title in self.resources:
                setattr(self.resources[title], 'DeletionPolicy', value)

        if hasattr(top_level_resource, 'UpdateReplacePolicy'):
            ## Override
            value = getattr(top_level_resource, 'UpdateReplacePolicy')
            for title in self.resources:
                setattr(self.resources[title], 'UpdateReplacePolicy', value)

        if hasattr(top_level_resource, 'DependsOn'):
            ## Append
            top_depends_on = getattr(top_level_resource, 'DependsOn')

            values = []
            for value in top_depends_on:
                if self.__macro_name in value:
                    values += self._get_values(value, import_templates)
            values += [value for value in top_depends_on if not self.__macro_name in value]

            for title in self.resources:
                if hasattr(self.resources[title], 'DependsOn'):
                    bottom_depends_on = getattr(self.resources[title], 'DependsOn')
                    setattr(self.resources[title], 'DependsOn', values + bottom_depends_on)
                else:
                    setattr(self.resources[title], 'DependsOn', values)

    def resolve_attrs(self, import_templates):
        for title in self.resources:
            if hasattr(self.resources[title], 'DependsOn'):
                depends_on = getattr(self.resources[title], 'DependsOn')

                depends_on_template = [d for d in depends_on if self.__macro_name in d]
                depends_on_aws = [d for d in depends_on if self.__macro_name not in d]

                for depends_on_value in depends_on_template:
                    key = depends_on_value.replace(self.__macro_name, "")
                    top_level_resource, inline_template = import_templates.get(key,
                        (self.resources.get(key, None), self)
                    )

                    if top_level_resource and inline_template == self: # Local Template Resource, Depends on Nested Stack
                        depends_on_aws.append(key)

                    elif top_level_resource and inline_template != self: # Imported Resource, Depends on Inline Stack
                        values = list(inline_template.resources.keys())
                        depends_on_aws += values

                depends_on_aws = list(set(depends_on_aws))
                setattr(self.resources[title], 'DependsOn', depends_on_aws)

#    @staticmethod
#    def __setattr(bucket, key, value):
#        if type(key) == int:
#            bucket[key] = value
#        if type(key) == str:
#            if hasattr(bucket, key):
#                setattr(bucket, key, value)
#            else:
#                bucket[key] = value
#    
#    def _create_export_resource(self, key, data):
#        if type(data) == dict:
#            [(data_key, data_value)] = data.items()
#            return self._create_export_resource(data_key, data_value)
#        if type(data) == list:
#            for index, item in enumerate(data):
#                if type(item) == str:
#                    continue
#                if type(item) == list:
#                    data[index] = self._create_export_resource(None, item)
#                if type(item) == dict:
#                    [(item_key, item_value)] = item.items()
#                    data[index] = self._create_export_resource(item_key, item_value)
#        if key is not None:
#            key = key.replace('Fn::', '')
#            if type(data) == list:
#                return getattr(troposphere, key)(*data)
#            if type(data) == str:
#                return getattr(troposphere, key)(data)
#        return data
#
#    def _fix_export(self, export):
#        name = export.data['Name']
#        for Obj in [Join, Select, Export, Base64, Cidr, FindInMap, GetAZs, ImportValue]:
#            if isinstance(name, Obj):
#                return export    
#        [(key, value)] = name.items()
#        return Export(self._create_export_resource(key, value))
#
#    def _replace_ref(self, template, ref, prop):
#        for (title, parameter) in self.parameters.items():
#            if title == ref.data['Ref']:
#                if 'Default' in parameter.properties:
#                    if type(prop) == str and hasattr(template, prop):
#                        setattr(template, prop, parameter.properties['Default'])
#                    elif type(prop) == int or prop in template:
#                        template[prop] = parameter.properties['Default']
#
#    def _update_prefix(self, prefix):
#        for (key, value) in self:
#            if key.startswith('_') or key in ['description', 'parameters', 'version', 'transform'] or\
#                type(value) in [str, int]:
#                    continue
#
#            prefixed_object = {}
#            for arg in value:
#                prefixed_object[prefix+arg] = value[arg]
#            self[key] = prefixed_object
#        
#    def find_relations(self, to_replace=False, prefix="", condition = None):
#        if len(prefix) > 0:
#            self._update_prefix(prefix)
#        self._find_relations(self, None, None, to_replace, prefix, condition)
#        
#    def _find_relations(self, template, parent = None, parent_prop = None, to_replace=False, prefix="", condition = None):        
#        if type(template) in [str, int] or template is None:
#            return
#        
#        description_attr = 'description' if hasattr(template, 'description') else 'Description'
#        if hasattr(template, description_attr) and len(prefix)>0:
#            description = getattr(template, description_attr)
#            if description is not None and not '[{}]'.format(prefix) in description:
#                setattr(template, description_attr, '[{}] {}'.format(prefix, description))
#
#        if type(template) == dict:
#            for key in template:
#                self._find_relations(template[key], template, key, to_replace, prefix, condition)
#
#        if type(template) == list:
#            for element in template:
#                self._find_relations(element, template, template.index(element), to_replace, prefix, condition)
#
#        for Obj in [Join, Select, Export, Base64, Cidr, FindInMap, GetAZs, ImportValue]:
#            if isinstance(template, Obj):
#                self._find_relations(template.data, template, 'data', to_replace, prefix, condition)
#                
#        if hasattr(template, 'Condition'):
#            template.Condition = prefix + template.Condition
#                
#        if isinstance(template, Resource) and len(prefix)>0:
#            if not prefix in template.title:
#                setattr(template, 'title', '{}{}'.format(prefix, template.title))
#            if condition is not None:
#                if hasattr(template, 'Condition'):
#                    old_condition = getattr(template, 'Condition')
#                    new_condition = condition["key"] + old_condition
#                    self.add_condition(new_condition,  And(Condition(old_condition), condition["value"]))
#                    setattr(template, 'Condition', new_condition)
#                else:
#                    setattr(template, 'Condition', condition["key"])
#                    
#        if isinstance(template, Output):
#            if hasattr(template, 'Export') and len(prefix) > 0:
#                data = getattr(getattr(template, 'Export'), 'data')
#                TemplateLoader.__setattr(data, 'Name', Join("-",[prefix, data['Name']]))
#            if condition is not None:
#                if hasattr(template, 'Condition'):
#                    old_condition = getattr(template, 'Condition')
#                    new_condition = condition["key"] + old_condition
#                    self.add_condition(new_condition,  And(Condition(old_condition), condition["value"]))
#                    setattr(template, 'Condition', new_condition)
#                else:
#                    setattr(template, 'Condition', condition["key"])
#
#        if isinstance(template, Parameter):
#            pass
#
#        if isinstance(template, Ref):
#            getatt_regexp = re.compile("[A-Za-z0-9]+\.[A-Za-z0-9]+\.[A-Za-z]+")
#            ref_regexp = re.compile("[A-Za-z0-9]+\.[A-Za-z0-9]+")
#            
#            if not isinstance(parent, Parameter):
#                self._replace_ref(parent, template, parent_prop)
#            value = template.data['Ref']
#            if value not in list(self.parameters.keys()) and not value.startswith('AWS::'):
#                TemplateLoader.__setattr(parent, parent_prop, Ref(prefix + value))
#            
#            if getatt_regexp.match(value):
#                values = value.split(".")
#                template = GetAtt("".join(values[:2]), attrName=values[2])
#                TemplateLoader.__setattr(parent, parent_prop, template)
#            elif ref_regexp.match(value):
#                values = value.split(".")
#                template = Ref("".join(values))
#                TemplateLoader.__setattr(parent, parent_prop, template)
#            
#
#        if isinstance(template, GetAtt):
#            pass
#
#        if hasattr(template, 'props'):
#            for prop in {**template.props, **{'Conditions':(dict, False)}}:
#                processed_prop = prop if hasattr(template, prop) else prop.lower()
#                if hasattr(template, processed_prop):
#                    snippet = getattr(template, processed_prop)
#
#                    if isinstance(snippet, Export):
#                        snippet = self._fix_export(snippet)
#                        setattr(template, processed_prop, snippet)
#
#                    self._find_relations(snippet, template, processed_prop, to_replace, prefix, condition)
#    
#    def set_default_parameters(self, params):
#        for title in self.parameters:
#            parameter = self.parameters[title]
#            if not 'Default' in parameter.properties:
#                parameter.properties['Default'] = params[title]
#    
#    def del_default_on_parameters(self):
#        for title in self.parameters:
#            parameter = self.parameters[title]
#            if 'Default' in parameter.properties:
#                del parameter.properties['Default']
#
#    def del_parameters(self):
#        self.parameters = {}
#                
#    def to_json(self, keep_parameters=True):
#        json_string = super().to_json()
#        if keep_parameters:
#            return json_string
#        else:
#            json_obj = json.loads(json_string)
#            if 'Parameters' in json_obj:
#                del json_obj['Parameters']
#            return json.dumps(json_obj)
#               
#    def to_yaml(self, keep_parameters=True):
#        json_string = self.to_json(keep_parameters)
#        return flip(json_string)#