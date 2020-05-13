from resources import *
from troposphere.template_generator import TemplateGenerator
import boto3
import os
import json

DEFAULT_BUCKET = os.environ.get(
    'DEFAULT_BUCKET', 'macro-template-default-831650818513-us-east-1')
s3 = boto3.client('s3')


class TemplateLoader(TemplateGenerator):
    __create_key = object()
    TemplateGenerator.add_version = TemplateGenerator.set_version
    TemplateGenerator.add_description = TemplateGenerator.set_description

    Ref.is_ref = lambda x: True

    @classmethod
    def loads(cls, json_string):
        return TemplateLoader(cls.__create_key,
                              json_string,
                              CustomMembers=[S3, Git])

    @classmethod
    def init(cls):
        return TemplateLoader.loads({
            'Description': 'This template is the result of the merge.',
            'Resources': {}
        })

    def __init__(self, create_key, cf_template=None, **kwargs):
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
        if data in Template.resources:
            return data

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
                value["Name"] = {
                    "Fn::Join": ["-", [self.prefix, value["Name"]]]
                }

            ## The reference in DependsOn is changed. A reference can have the Macro:: prefix, it must be preserved.
            #if key == "DependsOn":
            #    for index, _ in enumerate(value):
            #        if value[index].replace(Template.macro_prefix,
            #                                "") in self.logical_ids:
            #            value[index] = Template.macro_prefix + self.prefix + value[
            #                index].replace(Template.macro_prefix, "")

            # Finally we change the logical id for the resource
            if key in self.logical_ids:
                key = self.prefix + key

            # Recursive call to translate the whole template
            return (key, self._translate(value))

        # Update all custom references
        if type(data) == str:
            if data.startswith(Template.macro_prefix):
                values = data.split(Template.macro_separator)
                if values[1] != self.prefix:
                    values.insert(1, self.prefix)
                    data = Template.macro_separator.join(values)
        return data

    # To avoid conflicts during inline import the logical id for each resource is changed.
    # This function adds a prefix to all resources name.
    def translate(self, prefix):
        self.prefix = prefix
        self.logical_ids = []
        for _, value in self:
            if type(value) == dict:
                # Get all resources logica ids
                self.logical_ids += list(value.keys())

        json_string = json.loads(self.to_json())
        json_string = self._translate(json_string)
        return self.loads(json_string)


    # Given the logica resource id, this function return all the resources in a template
    # if inline mode is active otherwise it return the logical id of the nested stack.
    def _get_logical_ids(self, logical_id, import_templates):
        logical_ids = []
        logical_id = logical_id.replace(Template.macro_prefix, "")
        if logical_id in import_templates: # find the logical_id inside import_templates
            _, related_inline_template = import_templates[logical_id]
            for resource in related_inline_template.resources:
                if self.is_custom_resource(resource, import_templates):
                    logical_ids.append(Template.macro_prefix + resource)
                else:
                    logical_ids.append(resource)
            return logical_ids
        else:
            return [logical_id]  # Is Nested Resource

    ## Set attributes for inline resources
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
            ## Append DependsOn attributes, add the attributes from main template to all resource in the imported template.
            ## It resolve depends on relation. Worst case is when inline macro resource dependson an other inline
            ## macro resource, in this case we have N:N relation.
            top_resource_depends_on = getattr(top_level_resource, 'DependsOn')

            depends_on_template = []
            for attribute in top_resource_depends_on:
                if Template.macro_prefix in attribute:
                    depends_on_template += self._get_logical_ids(attribute, import_templates)

            depends_on_aws = [
                attribute for attribute in top_resource_depends_on
                if not Template.macro_prefix in attribute
            ]

            ## Append or set DependsOn value.
            ## Iterate over all resources inside current imported template.
            for title in self.resources:
                if hasattr(self.resources[title], 'DependsOn'):
                    resource_depends_on = getattr(self.resources[title],'DependsOn')
                    setattr(self.resources[title], 'DependsOn', depends_on_aws + depends_on_template + resource_depends_on)
                else:
                    setattr(self.resources[title], 'DependsOn', depends_on_aws + depends_on_template)

    ## Set attributes for nested resources or AWS resource
    def resolve_attrs(self, import_templates):
        for title in self.resources:
            if hasattr(self.resources[title], 'DependsOn'):
                depends_on = getattr(self.resources[title], 'DependsOn')

                depends_on_template = [
                    d for d in depends_on if Template.macro_prefix in d
                ]
                depends_on_aws = [
                    d for d in depends_on if Template.macro_prefix not in d
                ]

                for depends_on_value in depends_on_template:
                    key = depends_on_value.replace(Template.macro_prefix, "")
                    top_level_resource, inline_template = import_templates.get(
                        key,  # Check if dependson resource is in imported templates
                        (
                            self.resources.get(key, None), self
                        )  # Check if depends on resource is in Current Template (this object)
                    )

                    if top_level_resource and inline_template == self:  # Current Template Resource, Depends on Nested Stack or AWS Resource
                        if self.is_custom_resource(key):
                            key = Template.macro_prefix + key
                        depends_on_aws.append(key)

                    elif top_level_resource and inline_template != self:  # Imported Resource, Depends on Inline Stack / Multiple Resources
                        values = list(inline_template.resources.keys())
                        for index, key in enumerate(values):
                            if self.is_custom_resource(key, import_templates):
                                values[index] = Template.macro_prefix + key
                        depends_on_aws += values

                depends_on_aws = list(
                    set(depends_on_aws))  # Remove duplicates and set value
                setattr(self.resources[title], 'DependsOn', depends_on_aws)

    def is_custom_resource(self, logical_id, import_templates=None):
        # Check if logical_id is in current template
        if not import_templates:
            return isinstance(self.resources[logical_id], Template)
        else: # Check if logical_id is in imported resources
            inline_templates = [
                import_templates[resource][1] 
                for resource in import_templates
            ]

            for inline_template in inline_templates:
                for title in inline_template.resources:
                    if title == logical_id:
                        return isinstance(inline_template.resources[title], Template)
            return False

    ## Used to perform recursive call if there are resource to import
    def contains_custom_resources(self):
        if any([
                isinstance(res, S3) or isinstance(res, Git)
                for res in self.resources.values()
        ]):
            return True
        else:
            return False

    def _get(self, args):
        if type(args) == list:
            if Template.macro_prefix in args[0]:
                args[0] = args[0].replace(Template.macro_prefix, "")
                return {
                    "Fn::GetAtt":
                    [''.join(args[:-1]).replace(":", ""), args[-1]]
                }
        if type(args) == str:
            return {
                "Fn::GetAtt": args.replace(Template.macro_prefix, "").replace(":", "")
            }

    def _ref(self, args):
        if type(args) == list:
            if Template.macro_prefix in args[0]:
                args[0] = args[0].replace(Template.macro_prefix, "")
                return {"Ref": ''.join(args).replace(":", "")}
        if type(args) == str:
            return {"Ref": args.replace(Template.macro_prefix, "").replace(":", "")}

    def evaluate_custom_expression(self):
        return self._evaluate_custom_expression(self.to_dict())

    def _evaluate_custom_expression(self, data):
        if type(data) == dict and "Fn::GetAtt" in data:
            evaluated_params = self._evaluate_custom_expression(
                data["Fn::GetAtt"])
            return self._get(evaluated_params)

        if type(data) == dict and "Ref" in data:
            evaluated_params = self._evaluate_custom_expression(data["Ref"])
            return self._ref(evaluated_params)

        if type(data) == list:
            return [self._evaluate_custom_expression(d) for d in data]

        if type(data) == dict:
            return {
                key: self._evaluate_custom_expression(data[key])
                for key in data
            }

        return data
