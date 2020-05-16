import sys
sys.path.insert(1, 'source/libs')
sys.path.insert(1, 'source')

import json
import unittest
from cfn_flip import to_json
import logging

logging.basicConfig(level=logging.INFO)

from simulator import *
from utils import *
from troposphere import Join

with open('test/utils_resources_1st_test.yaml') as f:
    content = f.readlines()

import_template_dict = json.loads(to_json(''.join(content)))

with open('test/utils_resources_top_test.yaml') as f:
    content = f.readlines()

main_template_dict = json.loads(to_json(''.join(content)))

import_template_dict_params =  {
    "Name": "user-name",
    "Environment": "prod"
}

main_template_dict_params = {
    "GitHubUser": "ggiallo28",
    "BucketName": "macro-template-default-831650818513-us-east-1",
    "TemplateKey": "Template/sns-topics-template.yaml",
    "Environment": "prod",
    "RepositoryName": "aws-cloudformation-macros",
    "BranchName": "master"
}

def mock_s3_export(request_id, bucket_name, object_key, troposphere_template, template_params):
    bucket_name = 'mock-bucket-name'
    object_key = 'mock-object-key'

    return Join('',['https://', bucket_name, '.s3.amazonaws.com/', object_key])

class TestUtilsMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import_template = Simulator(import_template_dict, import_template_dict_params)
        import_template = import_template.simulate()
        cls.import_template = TemplateLoader.loads(import_template)

        cls._prefix = 'PREFIX'

    def test_obj(self):
        self.assertTrue(self.import_template)

    def test_evaluate_custom_expression(self):
        tdata = json.loads(self.import_template.to_json())

        self.assertEqual(
            tdata['Resources']['SNSTopicNestedDefault']['Properties']['NotificationARNs'][0]['Ref'],
            'Template::SNSTopiInlineCondition::UrgentPriorityAlarm'
        )

        self.assertEqual(
            tdata['Resources']['SNSTopicNestedDefault']['Properties']['Tags'][1]['Value']['Fn::GetAtt'],
            [ 'Template::SNSTopiInlineCondition::UrgentPriorityAlarm', 'TopicName' ]
        )
      
    def test_translate(self):
        tdata = json.loads(self.import_template.translate(prefix=self._prefix).to_json())

        self.assertTrue(self._prefix + 'UrgentPriorityAlarmArn' in tdata['Outputs'])
        self.assertTrue(self._prefix + 'HighPriorityAlarmArn' in tdata['Outputs'])
        self.assertTrue(self._prefix + 'MediumPriorityAlarmArn' in tdata['Outputs'])
        self.assertTrue(self._prefix + 'LowPriorityAlarmArn' in tdata['Outputs'])

        self.assertTrue('Fn::Join' in tdata['Outputs'][self._prefix + 'UrgentPriorityAlarmArn']['Export']['Name'])
        self.assertTrue('Fn::Join' in tdata['Outputs'][self._prefix + 'HighPriorityAlarmArn']['Export']['Name'])
        self.assertTrue('Fn::Join' in tdata['Outputs'][self._prefix + 'MediumPriorityAlarmArn']['Export']['Name'])
        self.assertTrue('Fn::Join' in tdata['Outputs'][self._prefix + 'LowPriorityAlarmArn']['Export']['Name'])

        self.assertEqual(
            tdata['Outputs'][self._prefix + 'UrgentPriorityAlarmArn']['Export']['Name']['Fn::Join'], 
            ['-', [self._prefix, {'Fn::Join': ["",[{"Ref": "AWS::StackName"},'-urgent-prod']]}]]
        )

        self.assertEqual(
            tdata['Outputs'][self._prefix + 'HighPriorityAlarmArn']['Export']['Name']['Fn::Join'],
            ['-', [self._prefix, {'Fn::Join': ["",[{"Ref": "AWS::StackName"},'-high-prod']]}]]
        )

        self.assertEqual(
            tdata['Outputs'][self._prefix + 'MediumPriorityAlarmArn']['Export']['Name']['Fn::Join'],
            ['-', [self._prefix, {'Fn::Join': ["",[{"Ref": "AWS::StackName"},'-medium-prod']]}]]
        )

        self.assertEqual(
            tdata['Outputs'][self._prefix + 'LowPriorityAlarmArn']['Export']['Name']['Fn::Join'],
            ['-', [self._prefix, {'Fn::Join': ["",[{"Ref": "AWS::StackName"},'-low-prod']]}]]
        )

        self.assertTrue(self._prefix + 'UrgentPriorityAlarm' in tdata['Resources'])
        self.assertTrue(self._prefix + 'HighPriorityAlarm' in tdata['Resources'])
        self.assertTrue(self._prefix + 'MediumPriorityAlarm' in tdata['Resources'])
        self.assertTrue(self._prefix + 'LowPriorityAlarm' in tdata['Resources'])       
        self.assertTrue(self._prefix + 'SNSTopiInlineCondition' in tdata['Resources'])
        self.assertTrue(self._prefix + 'SNSTopicNestedDefault' in tdata['Resources'])

        self.assertEqual(
            tdata['Resources'][self._prefix + 'SNSTopicNestedDefault']['Properties']['NotificationARNs'][1]['Ref'],
            self._prefix + 'HighPriorityAlarm'
        )

        self.assertEqual(
            tdata['Resources'][self._prefix + 'SNSTopicNestedDefault']['Properties']['NotificationARNs'][0]['Ref'], 
            'Template::{}::SNSTopiInlineCondition::UrgentPriorityAlarm'.format(self._prefix)
        )

        self.assertEqual(
            tdata['Resources'][self._prefix + 'SNSTopicNestedDefault']['Properties']['Tags'][1]['Value']['Fn::GetAtt'],
            [ 'Template::{}::SNSTopiInlineCondition::UrgentPriorityAlarm'.format(self._prefix), 'TopicName' ]
        )


class TestAttrsMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        SNSTopiInlineCondition = Simulator(import_template_dict, import_template_dict_params)
        SNSTopiInlineCondition = SNSTopiInlineCondition.simulate()
        SNSTopiInlineCondition = TemplateLoader.loads(SNSTopiInlineCondition)
        cls.SNSTopiInlineCondition = SNSTopiInlineCondition.translate(prefix='SNSTopiInlineCondition')

        SNSTopicNested = Simulator(import_template_dict, import_template_dict_params)
        SNSTopicNested = SNSTopicNested.simulate()
        SNSTopicNested = TemplateLoader.loads(SNSTopicNested)
        cls.SNSTopicNested = SNSTopicNested.translate(prefix='SNSTopicNested')

        SNSTopicS3 = Simulator(import_template_dict, import_template_dict_params)
        SNSTopicS3 = SNSTopicS3.simulate()
        SNSTopicS3 = TemplateLoader.loads(SNSTopicS3)
        cls.SNSTopicS3 = SNSTopicS3.translate(prefix='SNSTopicS3')

        DoubleSNSTopicS3 = Simulator(import_template_dict, import_template_dict_params)
        DoubleSNSTopicS3 = DoubleSNSTopicS3.simulate()
        DoubleSNSTopicS3 = TemplateLoader.loads(DoubleSNSTopicS3)
        cls.DoubleSNSTopicS3 = DoubleSNSTopicS3.translate(prefix='DoubleSNSTopicS3')

        Nested2InlineTarget = Simulator(import_template_dict, import_template_dict_params)
        Nested2InlineTarget = Nested2InlineTarget.simulate()
        Nested2InlineTarget = TemplateLoader.loads(Nested2InlineTarget)
        cls.Nested2InlineTarget = Nested2InlineTarget.translate(prefix='Nested2InlineTarget')

        SNSTopicNested = Simulator(import_template_dict, import_template_dict_params)
        SNSTopicNested = SNSTopicNested.simulate()
        SNSTopicNested = TemplateLoader.loads(SNSTopicNested)
        cls.SNSTopicNested = SNSTopicNested.translate(prefix='SNSTopicNested')

        main_template = Simulator(main_template_dict, main_template_dict_params)
        main_template = main_template.simulate(excude_clean=['Parameters'])
        cls.main_template = TemplateLoader.loads(main_template)


        cls.import_templates = {
            'SNSTopiInlineCondition' : (cls.main_template.resources['SNSTopiInlineCondition'], cls.SNSTopiInlineCondition),
            'SNSTopicS3' : (cls.main_template.resources['SNSTopicS3'], cls.SNSTopicS3),
            'DoubleSNSTopicS3' : (cls.main_template.resources['DoubleSNSTopicS3'], cls.DoubleSNSTopicS3),
            'Nested2InlineTarget' : (cls.main_template.resources['Nested2InlineTarget'], cls.Nested2InlineTarget),
        }

    def test_set_attrs_inline_dependson_nested(self):
        # Inline DependsOn Nested
        top_level_resource_id = 'SNSTopicS3'
        top_level_resource, inline_template = self.import_templates[top_level_resource_id]
        inline_template.set_attrs(top_level_resource, self.import_templates)
        inline_template_json = json.loads(inline_template.to_json())

        self.assertEqual(
            inline_template_json['Resources'][top_level_resource_id + 'UrgentPriorityAlarm']['DependsOn'], 
            ['SNSTopicNested']
        )

        self.assertEqual(
            inline_template_json['Resources'][top_level_resource_id + 'HighPriorityAlarm']['DependsOn'], 
            ['SNSTopicNested']
        )

        self.assertEqual(
            inline_template_json['Resources'][top_level_resource_id + 'MediumPriorityAlarm']['DependsOn'], 
            ['SNSTopicNested']
        )

        self.assertEqual(
            inline_template_json['Resources'][top_level_resource_id + 'LowPriorityAlarm']['DependsOn'], 
            ['SNSTopicNested']
        )
        
        self.assertEqual(
            sorted(inline_template_json['Resources'][top_level_resource_id + 'SNSTopicNestedDefault']['DependsOn']), 
            sorted([
                'SNSTopicNested', 
                'Template::{}::SNSTopiInlineCondition'.format(top_level_resource_id)
            ])
        )

        self.assertEqual(inline_template_json['Resources'][top_level_resource_id + 'SNSTopiInlineDependsOn']['DependsOn'], [
            'SNSTopicNested', 
            'Template::{}::SNSTopiInlineCondition'.format(top_level_resource_id)]
        )     

    def test_set_attrs_inline_dependson_nested_or_aws(self):
        # Inline DependsOn Inline & Inline DependsOn AWS
        top_level_resource_id = 'DoubleSNSTopicS3'
        dependson_resource_id = 'SNSTopicS3'
        top_level_resource, inline_template = self.import_templates[top_level_resource_id]
        inline_template.set_attrs(top_level_resource, self.import_templates)
        inline_template_json = json.loads(inline_template.to_json())

        self.assertEqual(
            sorted(inline_template_json['Resources'][top_level_resource_id + 'UrgentPriorityAlarm']['DependsOn']), 
            sorted([
                'HighPriorityAlarm',
                '{}UrgentPriorityAlarm'.format(dependson_resource_id),
                '{}HighPriorityAlarm'.format(dependson_resource_id),
                '{}MediumPriorityAlarm'.format(dependson_resource_id),
                '{}LowPriorityAlarm'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineCondition'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineDependsOn'.format(dependson_resource_id),
                'Template::{}SNSTopicNestedDefault'.format(dependson_resource_id)
            ])
        )

        self.assertEqual(
            sorted(inline_template_json['Resources'][top_level_resource_id + 'HighPriorityAlarm']['DependsOn']), 
            sorted([
                'HighPriorityAlarm',
                '{}UrgentPriorityAlarm'.format(dependson_resource_id),
                '{}HighPriorityAlarm'.format(dependson_resource_id),
                '{}MediumPriorityAlarm'.format(dependson_resource_id),
                '{}LowPriorityAlarm'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineCondition'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineDependsOn'.format(dependson_resource_id),
                'Template::{}SNSTopicNestedDefault'.format(dependson_resource_id)
            ])
        )

        self.assertEqual(
            sorted(inline_template_json['Resources'][top_level_resource_id + 'MediumPriorityAlarm']['DependsOn']), 
            sorted([
                'HighPriorityAlarm',
                '{}UrgentPriorityAlarm'.format(dependson_resource_id),
                '{}HighPriorityAlarm'.format(dependson_resource_id),
                '{}MediumPriorityAlarm'.format(dependson_resource_id),
                '{}LowPriorityAlarm'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineCondition'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineDependsOn'.format(dependson_resource_id),
                'Template::{}SNSTopicNestedDefault'.format(dependson_resource_id)
            ])
        )

        self.assertEqual(
            sorted(inline_template_json['Resources'][top_level_resource_id + 'LowPriorityAlarm']['DependsOn']), 
            sorted([
                'HighPriorityAlarm',
                '{}UrgentPriorityAlarm'.format(dependson_resource_id),
                '{}HighPriorityAlarm'.format(dependson_resource_id),
                '{}MediumPriorityAlarm'.format(dependson_resource_id),
                '{}LowPriorityAlarm'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineCondition'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineDependsOn'.format(dependson_resource_id),
                'Template::{}SNSTopicNestedDefault'.format(dependson_resource_id)
            ])
        )

        self.assertEqual(
            sorted(inline_template_json['Resources'][top_level_resource_id + 'SNSTopicNestedDefault']['DependsOn']), 
            sorted([
                'Template::{}::SNSTopiInlineCondition'.format(top_level_resource_id),
                'HighPriorityAlarm',
                '{}UrgentPriorityAlarm'.format(dependson_resource_id),
                '{}HighPriorityAlarm'.format(dependson_resource_id),
                '{}MediumPriorityAlarm'.format(dependson_resource_id),
                '{}LowPriorityAlarm'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineCondition'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineDependsOn'.format(dependson_resource_id),
                'Template::{}SNSTopicNestedDefault'.format(dependson_resource_id)
            ])
        )

        self.assertEqual(
            sorted(inline_template_json['Resources'][top_level_resource_id + 'SNSTopiInlineDependsOn']['DependsOn']), 
            sorted([
                'Template::{}::SNSTopiInlineCondition'.format(top_level_resource_id),
                'HighPriorityAlarm',
                '{}UrgentPriorityAlarm'.format(dependson_resource_id),
                '{}HighPriorityAlarm'.format(dependson_resource_id),
                '{}MediumPriorityAlarm'.format(dependson_resource_id),
                '{}LowPriorityAlarm'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineCondition'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineDependsOn'.format(dependson_resource_id),
                'Template::{}SNSTopicNestedDefault'.format(dependson_resource_id)
            ])
        )

    def test_resolve_attrs_nested_dependson_inline(self):
        # Nested DependsOn Inline
        dependson_resource_id = 'Nested2InlineTarget'
        merge_template = TemplateLoader.init(self.main_template.parameters)

        merge_template.add_resource(self.main_template.resources['Nested2InlineSource'])

        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())

        self.assertEqual(
            sorted(merge_template_json['Resources']['Nested2InlineSource']['DependsOn']), 
            sorted([
                '{}UrgentPriorityAlarm'.format(dependson_resource_id),
                '{}HighPriorityAlarm'.format(dependson_resource_id),
                '{}MediumPriorityAlarm'.format(dependson_resource_id),
                '{}LowPriorityAlarm'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineCondition'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineDependsOn'.format(dependson_resource_id),
                'Template::{}SNSTopicNestedDefault'.format(dependson_resource_id)
            ])
        )

    def test_resolve_attrs_nested_dependson_nested(self):
        # Nested DependsOn Nested
        merge_template = TemplateLoader.init(self.main_template.parameters)

        merge_template.add_resource(self.main_template.resources['Nested2NestedTarget'])
        merge_template.add_resource(self.main_template.resources['Nested2NestedSource'])

        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())

        self.assertEqual(
            merge_template_json['Resources']['Nested2NestedSource']['DependsOn'], 
            ['Template::Nested2NestedTarget']
        )

    def test_resolve_attrs_aws_dependson_inline(self):
        # AWS DependsOn Inline
        dependson_resource_id = 'SNSTopiInlineCondition'
        merge_template = TemplateLoader.init(self.main_template.parameters)

        merge_template.add_resource(self.main_template.resources['HighPriorityAlarm'])
        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())

        self.assertEqual(
            sorted(merge_template_json['Resources']['HighPriorityAlarm']['DependsOn']), 
            sorted([
                '{}UrgentPriorityAlarm'.format(dependson_resource_id),
                '{}HighPriorityAlarm'.format(dependson_resource_id),
                '{}MediumPriorityAlarm'.format(dependson_resource_id),
                '{}LowPriorityAlarm'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineCondition'.format(dependson_resource_id),
                'Template::{}SNSTopiInlineDependsOn'.format(dependson_resource_id),
                'Template::{}SNSTopicNestedDefault'.format(dependson_resource_id)
            ])
        )

    def test_resolve_attrs_aws_dependson_nested(self):
        # AWS DependsOn Nested
        dependson_resource_id = 'SNSTopicNested'
        merge_template = TemplateLoader.init(self.main_template.parameters)

        merge_template.add_resource(self.main_template.resources['HighPriorityAlarmDependsOnNested'])
        merge_template.add_resource(self.main_template.resources['SNSTopicNested'])
        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())

        self.assertEqual(
            merge_template_json['Resources']['HighPriorityAlarmDependsOnNested']['DependsOn'], 
            ['Template::SNSTopicNested']
        )

    def test_resolve_attrs_nested_dependson_aws(self):
        # Nested DependsOn AWS
        dependson_resource_id = 'HighPriorityAlarm'
        merge_template = TemplateLoader.init(self.main_template.parameters)

        merge_template.add_resource(self.main_template.resources['HighPriorityAlarm'])
        merge_template.add_resource(self.main_template.resources['SNSTopicNestedDefault'])
        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())

        self.assertEqual(
            merge_template_json['Resources']['SNSTopicNestedDefault']['DependsOn'],
            ['HighPriorityAlarm']
        )

    def test_is_custom(self):
        template = TemplateLoader.init({})      
        template.add_resource(self.main_template.resources['HighPriorityAlarm'])
        self.assertFalse(template.contains_custom_resources())
        template.add_resource(self.main_template.resources['SNSTopicNestedDefault'])
        self.assertTrue(template.contains_custom_resources())


    def test_evaluate_custom_expression(self):
        snippet = {
            "test1": {
                "Fn::GetAtt": [
                    "LambdaShutdownInstanceStartEC2Instances",
                    "Arn"
                ]
            },
            "test2": {
                "Fn::GetAtt": [
                    "LambdaShutdownInstanceLambdaExecutionRole",
                    "Arn"
                ]
            },
            "test3": {
                "Fn::GetAtt": [
                    "LambdaShutdownInstanceStartEC2InstancesEventRule",
                    "Arn"
                ]
            },
            "test4":{
                "Fn::GetAtt": [
                    "LambdaRebootInstanceLambdaFunction",
                    "Arn"
                ]
            },
            "test5": {
                "Ref": "Template::SNSTopiInlineCondition::UrgentPriorityAlarm"
            },
            "test6": {
                "Fn::GetAtt": [
                    "Template::SNSTopiInlineCondition::UrgentPriorityAlarm",
                    "TopicName"
                ]
            },
            "test7": {
                "Fn::Join": ["-", [
                    {
                        "Fn::GetAtt": [
                            "LambdaShutdownInstanceStartEC2Instances",
                            "Arn"
                        ]
                    },{
                        "Ref": "Template::SNSTopiInlineCondition::UrgentPriorityAlarm"
                    },
                    {
                        "Fn::GetAtt": [{
                                "Fn::Join": ["+", [{
                                    "Fn::GetAtt": [
                                        "Template::SNSTopiInlineCondition::UrgentPriorityAlarm",
                                        "TopicName"
                                    ]
                                }, {
                                    "Ref": "Template::SNSTopiInlineCondition::UrgentPriorityAlarm"
                                }]]
                            },
                            "TopicName"
                        ]
                    }
                ]]
            }
        }
        template = TemplateLoader.init({})
        template = template._evaluate_custom_expression(snippet)

        self.assertEqual(template["test1"], snippet["test1"])
        self.assertEqual(template["test2"], snippet["test2"])
        self.assertEqual(template["test3"], snippet["test3"])
        self.assertEqual(template["test4"], snippet["test4"])
        self.assertEqual(template["test5"], {"Ref": "SNSTopiInlineConditionUrgentPriorityAlarm"})
        self.assertEqual(template["test6"], {"Fn::GetAtt": ["SNSTopiInlineConditionUrgentPriorityAlarm","TopicName"]})
        self.assertEqual(template["test7"], {
            "Fn::Join": ["-", [
                {
                    "Fn::GetAtt": [
                        "LambdaShutdownInstanceStartEC2Instances",
                        "Arn"
                    ]
                },{
                    "Ref": "SNSTopiInlineConditionUrgentPriorityAlarm"
                },
                {
                    "Fn::GetAtt": [{
                            "Fn::Join": ["+", [{
                                "Fn::GetAtt": [
                                    "SNSTopiInlineConditionUrgentPriorityAlarm",
                                    "TopicName"
                                ]
                            }, {
                                "Ref": "SNSTopiInlineConditionUrgentPriorityAlarm"
                            }]]
                        },
                        "TopicName"
                    ]
                }
            ]]
        })

if __name__ == '__main__':
    unittest.main()