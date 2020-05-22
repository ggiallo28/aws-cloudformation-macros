import sys
sys.path.insert(1, 'source/libs')
sys.path.insert(1, 'source')

import json
import unittest

from simulator import *
from loader import *
from macro import *
from cfn_flip import to_json
from unittest.mock import MagicMock

with open('test/macro_top_test.yaml') as f:
    content = f.readlines()
main_template_dict = json.loads(to_json(''.join(content)))

with open('test/macro_1st_import_test.yaml') as f:
    content = f.readlines()
fir_template_dict = json.loads(to_json(''.join(content)))

with open('test/macro_2nd_import_test.yaml') as f:
    content = f.readlines()
sec_template_dict = json.loads(to_json(''.join(content)))

import_template_dict_params = {"Name": "user-name", "Environment": "prod"}

main_template_dict_params = {
    "GitHubUser": "ggiallo28",
    "BucketName": "macro-template-default-831650818513-us-east-1",
    "TemplateKey": "Template/sns-topics-template.yaml",
    "Environment": "prod",
    "RepositoryName": "aws-cloudformation-macros",
    "BranchName": "master"
}

import logging
logging.basicConfig(level=logging.INFO)


class TestUtilsMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Template.aws_cfn_request_id = 'mock-test'
        Template.template_params = {}
        Template.aws_region = 'eu-west-1'
        cls.bucket_name = 'mock-bucket-name'
        cls.object_key = 'mock-object-key'

        fir_template = Simulator(fir_template_dict,
                                 import_template_dict_params)
        fir_template = fir_template.simulate()

        sec_template = Simulator(sec_template_dict,
                                 import_template_dict_params)
        sec_template = sec_template.simulate()

        def mock_get_template(obj):
            if 'LastRecursiveCall' in obj.title:
                return sec_template
            else:
                return fir_template

        Template.get_template = mock_get_template
        Template.s3_export = MagicMock(
            return_value=Join('', [
                'https://', cls.bucket_name, '.s3.amazonaws.com/',
                cls.object_key
            ]))

        cfn = Simulator(main_template_dict, main_template_dict_params)
        template = cfn.simulate(excude_clean=['Parameters'])

        template = TemplateLoader.loads(template)
        cls.template = handle_template(template)

    def test_parameters(self):
        self.assertEqual(
            sorted(list(self.template.parameters.keys())),
            sorted([
                'GitHubUser', 'RepositoryName', 'BranchName', 'BucketName',
                'TemplateKey', 'Environment'
            ]))

    def test_count_resouces(self):
        self.assertEqual(len(list(self.template.resources.keys())), 9)

    def test_top_level_ref(self):
        self.assertEqual(self.template.resources['SNSTopicNested'].properties['NotificationARNs'][0].data['Ref'],'Template::SNSTopiInlineCondition::UrgentPriorityAlarm')
        self.assertTrue('SNSTopiInlineConditionUrgentPriorityAlarm' in self.template.resources)
        self.assertEqual(self.template.resources['SNSTopicNested'].properties['NotificationARNs'][1].data['Ref'], 'HighPriorityAlarm')
        self.assertTrue('HighPriorityAlarm' in self.template.resources)

    def test_top_level_gett(self):
        self.assertEqual(
            self.template.resources['SNSTopicNested'].properties['Tags'][1]
            ['Value'].data, {
                'Fn::GetAtt':
                ['Template::SNSTopiInlineCondition::UrgentPriorityAlarm', 'TopicName']
            })
        self.assertTrue('SNSTopiInlineConditionUrgentPriorityAlarm' in self.template.resources)

    def test_second_level_ref(self):
        prefix = 'SNSTopicS3'
        self.assertEqual(
            self.template.resources[prefix +
                               'LowPriorityAlarm'].properties['Tags'].tags[1]['Value']['Ref'], 'Template::'+prefix+'::LastRecursiveCall::UrgentPriorityAlarm')

    def test_second_level_gett(self):
        prefix = 'SNSTopiInlineCondition'
        self.assertEqual(
            self.template.resources[prefix +
                               'LowPriorityAlarm'].properties['Tags'].tags[0]['Value']['Fn::GetAtt'], ['Template::'+prefix+'::LastRecursiveCall::UrgentPriorityAlarm', 'TopicName'])

    def test_macro_name_in_export(self):
        for key in self.template.outputs:
            export = self.template.outputs[key].resource.get('Export')
            if export:
                self.assertFalse(Template.macro_prefix in json.dumps(export.data['Name']))

    def test_depends_on(self):
        self.assertEqual(
            self.template.resources['SNSTopicNestedDefault'].DependsOn, ["SNSTopicNested"])

        SNSTopiInlineConditionResources = [res for res in self.template.resources if res.startswith("SNSTopiInlineCondition")]
        SNSTopicS3Resources = [res for res in self.template.resources if res.startswith("SNSTopicS3")]

        for res in SNSTopicS3Resources:
            self.assertEqual(
                sorted(self.template.resources[res].DependsOn), sorted(SNSTopiInlineConditionResources))

    def test_custom_expression_no_macro_name(self):
        template = self.template.evaluate_custom_expression()
        self.assertFalse(Template.macro_prefix in template)

if __name__ == '__main__':
    unittest.main()
