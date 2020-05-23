import sys
sys.path.insert(1, 'source/libs')
sys.path.insert(1, 'source')

import json
import unittest
from cfn_flip import to_json
from unittest.mock import MagicMock

from resources import *
from simulator import *
from loader import *

from troposphere import Join

with open('test/loader_resources_1st_test.yaml') as f:
    content = f.readlines()

import_template_dict = json.loads(to_json(''.join(content)))

with open('test/loader_resources_top_test.yaml') as f:
    content = f.readlines()

main_template_dict = json.loads(to_json(''.join(content)))

import_template_dict_params = {"Name": "user-name", "Environment": "prod"}

main_template_dict_params = {
    "GitHubUser": "ggiallo28",
    "BucketName": "macro-template-default-831650818513-us-east-1",
    "TemplateKey": "Template/sns-topics-template.yaml",
    "Environment": "prod",
    "RepositoryName": "aws-cloudformation-macros",
    "BranchName": "master"
}


class TestUtilsMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Macro.aws_cfn_request_id = 'test_get_stack_template'
        Macro.template_params = {}
        Macro.aws_region = 'us-west-1'

        bucket_name = 'mock-bucket-name'
        object_key = 'mock-object-key'

        import_template = Simulator(import_template_dict,
                                    import_template_dict_params)
        import_template = import_template.simulate()

        Macro._codecommit_import = MagicMock(return_value=import_template)
        Macro._github_import = MagicMock(return_value=import_template)
        Macro._s3_import = MagicMock(return_value=import_template)
        Macro._s3_export = MagicMock(return_value=Join(
            '', ['https://', bucket_name, '.s3.amazonaws.com/', object_key]))

        main_template = Simulator(main_template_dict,
                                  main_template_dict_params)
        main_template = main_template.simulate(excude_clean=['Parameters'])
        cls.main_template = TemplateLoader.loads(main_template)

    def test_get_stack_template(self):
        resource_obj = self.main_template.resources['SNSTopicNested']
        nested_stack = resource_obj.get_stack_template()

        self.assertEqual(nested_stack.resource['DependsOn'],
                         ['Template::SNSTopiInlineCondition'])

    def test_get_aws_cfn_request_id(self):
        self.assertEqual(self.main_template.resources['SNSTopicS3'].get_aws_cfn_request_id(), 'test_get_stack_template')

    def test_get_template_params(self):
        self.assertEqual(self.main_template.resources['SNSTopicS3'].get_template_params(), {})

    def test_get_aws_region(self):
        self.assertEqual(self.main_template.resources['SNSTopicS3'].get_aws_region(), 'us-west-1')

    def test_s3(self):
        resource_obj = self.main_template.resources['SNSTopicNested']
        try:
            json.dumps(resource_obj.get_template())
        except:
            self.assertTrue(False)

    def test_git(self):
        resource_obj = self.main_template.resources['SNSTopiInlineCondition']
        try:
            json.dumps(resource_obj.get_template())
        except:
            self.assertTrue(False)

