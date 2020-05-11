import sys
sys.path.insert(1, '../source/libs')
sys.path.insert(1, '../source')

import json
import unittest

from simulator import *
from utils import *
from macro import *
from cfn_flip import to_json
from unittest.mock import MagicMock

with open('macro_top_test.yaml') as f:
    content = f.readlines()
main_template_dict = json.loads(to_json(''.join(content)))

with open('macro_1st_import_test.yaml') as f:
    content = f.readlines()
fir_template_dict = json.loads(to_json(''.join(content)))

with open('macro_2nd_import_test.yaml') as f:
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

        template = handle_template(template)
        cls.template = TemplateLoader.loads(template)

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
        self.assertEqual(self.template.resources['SNSTopicNested'].properties['NotificationARNs'][0].data['Ref'],'SNSTopiInlineConditionUrgentPriorityAlarm')
        self.assertTrue('SNSTopiInlineConditionUrgentPriorityAlarm' in self.template.resources)
        self.assertEqual(self.template.resources['SNSTopicNested'].properties['NotificationARNs'][1].data['Ref'], 'HighPriorityAlarm')
        self.assertTrue('HighPriorityAlarm' in self.template.resources)

    def test_top_level_gett(self):
        self.assertEqual(
            self.template.resources['SNSTopicNested'].properties['Tags'][1]
            ['Value'].data, {
                'Fn::GetAtt':
                ['SNSTopiInlineConditionUrgentPriorityAlarm', 'TopicName']
            })
        self.assertTrue('SNSTopiInlineConditionUrgentPriorityAlarm' in self.template.resources)

    def test_second_level_ref(self):
        self.assertTrue(False)

    def test_second_level_gett(self):
        self.assertTrue(False)

        #logging.info(template.resources.keys())

        prefix = 'SNSTopiInlineCondition'
        logging.info(
            template.resources[prefix +
                               'LowPriorityAlarm'].properties['Tags'].tags)

        prefix = 'SNSTopicS3'
        logging.info(
            template.resources[prefix +
                               'LowPriorityAlarm'].properties['Tags'].tags)
        ## Test value in Macro1::LowPriorityAlarm::Tags

    def test_macro_name_in_export(self):
        self.assertTrue(False)
        ## Test Template:: in Export name

    def test_top_level_depends_on(self):
        self.assertTrue(False)

    def test_top_second_depends_on(self):
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
