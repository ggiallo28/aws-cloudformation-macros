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

MAX_RECURSION_CALL = 4

class TestUtilsMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Template.aws_cfn_request_id  = 'mock-test'
        Template.template_params = {}
        Template.aws_region = 'eu-west-1'
        cls.bucket_name = 'mock-bucket-name'
        cls.object_key = 'mock-object-key'

        fir_template = Simulator(fir_template_dict, import_template_dict_params)
        fir_template = fir_template.simulate()

        sec_template = Simulator(sec_template_dict, import_template_dict_params)
        sec_template = sec_template.simulate()   

        def mock_get_template(obj):
            if obj.title == 'LastRecursiveCall':
                return sec_template
            else:
                return fir_template

        Template.get_template = mock_get_template
        Template.s3_export = MagicMock(return_value=Join('',['https://', cls.bucket_name, '.s3.amazonaws.com/', cls.object_key]))   

        cfn = Simulator(main_template_dict, main_template_dict_params)
        cls.template = cfn.simulate(excude_clean=['Parameters'])

    def test_handle_template(self):
        print(self.template)
        template = handle_template(self.template)
        template = TemplateLoader.loads(template)

        print(template.to_yaml())

        self.assertEqual(list(template.parameters.keys()), ['GitHubUser', 'RepositoryName', 'BranchName', 'BucketName', 'TemplateKey', 'Environment'])
        ## Test value in Macro1::LowPriorityAlarm::Tags

if __name__ == '__main__':
    unittest.main()