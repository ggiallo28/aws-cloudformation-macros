import sys
sys.path.insert(1, '../source/libs')
sys.path.insert(1, '../source')

import json
import unittest
from cfn_flip import to_json
from unittest.mock import MagicMock

from simulator import *
from resources import *
from utils import *

from troposphere import Join

with open('utils_resources_1st_test.yaml') as f:
    content = f.readlines()

import_template_dict = json.loads(to_json(''.join(content)))

with open('utils_resources_top_test.yaml') as f:
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

class TestUtilsMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Template.aws_cfn_request_id  = 'test_get_stack_template'
        Template.template_params = {}
        Template.aws_region = 'us-west-1'

        bucket_name = 'mock-bucket-name'
        object_key = 'mock-object-key'

        import_template = Simulator(import_template_dict, import_template_dict_params)
        import_template = import_template.simulate()

        Template.get_template = MagicMock(return_value=import_template)
        Template.s3_export = MagicMock(return_value=Join('',['https://', bucket_name, '.s3.amazonaws.com/', object_key]))

        
        main_template = Simulator(main_template_dict, main_template_dict_params)
        main_template = main_template.simulate(excude_clean=['Parameters'])
        cls.main_template = TemplateLoader.loads(main_template)

    def test_get_stack_template(self):
        resource_obj = self.main_template.resources['SNSTopicNested']
        nested_stack = resource_obj.get_stack_template()

        self.assertEqual(nested_stack.resource['DependsOn'], ['Template::SNSTopiInlineCondition'])

