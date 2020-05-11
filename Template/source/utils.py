from troposphere.template_generator import TemplateGenerator
from resources import *
import boto3
import os, json

DEFAULT_BUCKET = os.environ.get('DEFAULT_BUCKET', 'macro-template-default-831650818513-us-east-1')
s3 = boto3.client('s3')

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
            # Change the name of the reference
            if key == 'Ref':
                if value in self.logical_ids:
                    value = self.prefix + value

            # Change the logical id reference in GetAtt
            if key == "Fn::GetAtt":
                if value[0] in self.logical_ids:
                    value[0] = self.prefix + value[0]

            # Export name is changed with a prefix
            if key == "Export":
                value["Name"] = { "Fn::Join" : [ "-", [ self.prefix,  value["Name"] ] ] }

            # The reference in DependsOn is changed. A reference can have the Macro:: prefix, it must be preserved.
            if key == "DependsOn":
                for index, _ in enumerate(value):
                    if value[index].replace(self.__macro_name, "") in self.logical_ids:
                        value[index] = self.__macro_name + self.prefix + value[index].replace(self.__macro_name, "")   

            # Finally we change the logical id for the resource
            if key in self.logical_ids:
                key = self.prefix + key

            # Recursive call to translate the whole template
            return (key, self._translate(value))

        return data

    # To avoid conflicts during inline import the logical id for each resource is changed.
    # This function adds a prefix to all resources name.
    def translate(self, prefix):
        self.prefix = prefix
        self.logical_ids = []
        for _,value in self:
            if type(value) == dict: 
                # Get all resources logica ids
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

    ## Set attributes for inline resouces
    def set_attrs(self, top_level_resource, import_templates):

        if hasattr(top_level_resource, 'DeletionPolicy'):
            ## Override the value of DeletionPolicy, propagate the value that comes from main template.
            value = getattr(top_level_resource, 'DeletionPolicy')
            for title in self.resources:
                setattr(self.resources[title], 'DeletionPolicy', value)

        if hasattr(top_level_resource, 'UpdateReplacePolicy'):
            ## Override the value of UpdateReplacePolicy, propagate the value that comes from main template.
            value = getattr(top_level_resource, 'UpdateReplacePolicy')
            for title in self.resources:
                setattr(self.resources[title], 'UpdateReplacePolicy', value)

        if hasattr(top_level_resource, 'DependsOn'):
            ## Append DependsOn values, add the values from main template to all resource in the imported template.
            ## It resolve depends on relation. Worst case is when inline macro resource dependson an other inline 
            ## macro resource, in this case we have N:N relation.  
            top_depends_on = getattr(top_level_resource, 'DependsOn')

            values = []
            for value in top_depends_on: 
                if self.__macro_name in value:
                    values += self._get_values(value, import_templates)
            values += [value for value in top_depends_on if not self.__macro_name in value]

            ## Append or set DependsOn value.
            for title in self.resources:
                if hasattr(self.resources[title], 'DependsOn'):
                    bottom_depends_on = getattr(self.resources[title], 'DependsOn')
                    setattr(self.resources[title], 'DependsOn', values + bottom_depends_on)
                else:
                    setattr(self.resources[title], 'DependsOn', values)

    ## Set attributes for nested resouces or AWS resource
    def resolve_attrs(self, import_templates):
        for title in self.resources:
            if hasattr(self.resources[title], 'DependsOn'):
                depends_on = getattr(self.resources[title], 'DependsOn')

                depends_on_template = [d for d in depends_on if self.__macro_name in d]
                depends_on_aws = [d for d in depends_on if self.__macro_name not in d]

                for depends_on_value in depends_on_template:
                    key = depends_on_value.replace(self.__macro_name, "")
                    top_level_resource, inline_template = import_templates.get(key, # Check if dependson resouce is in imported templates
                        (self.resources.get(key, None), self) # Check if depends on resouce is in Current Template (this object)
                    )

                    if top_level_resource and inline_template == self: # Current Template Resource, Depends on Nested Stack or AWS Resource
                        depends_on_aws.append(key)

                    elif top_level_resource and inline_template != self: # Imported Resource, Depends on Inline Stack / Multiple Resources
                        values = list(inline_template.resources.keys())
                        depends_on_aws += values

                depends_on_aws = list(set(depends_on_aws)) # Remove duplicates and set value
                setattr(self.resources[title], 'DependsOn', depends_on_aws)

    ## Used to perform recursive call if there are resource to import
    def is_custom(self):
        if any([isinstance(res, S3) or isinstance(res, Git) for res in self.resources.values()]):
            return True
        else:
            return False
