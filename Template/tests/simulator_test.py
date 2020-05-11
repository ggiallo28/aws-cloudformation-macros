import sys
sys.path.insert(1, '../source/libs')
sys.path.insert(1, '../source')

import json
import unittest

from simulator import *
from cfn_flip import to_json

with open('simulator_test.yaml') as f:
    content = f.readlines()

data = json.loads(to_json(''.join(content)))

params = { 
    'EnvType': 'prod',
    'NameIndex' : '1'
}

class TestSimulatorMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.obj = Simulator(data, params).simulate(excude_clean=['Conditions'])

    def test_obj(self):
        self.assertTrue(self.obj)

    def test_conditions(self):
        self.assertTrue(self.obj['Conditions']['CreateProdResources'])
        self.assertFalse(self.obj['Conditions']['CreateDevResources'])
        self.assertTrue(self.obj['Conditions']['OrTest'])
        self.assertFalse(self.obj['Conditions']['AndTest'])
        self.assertFalse(self.obj['Conditions']['NonProd'])

    def test_resources_condition(self): 
        self.assertTrue('ProdInstance' in self.obj['Resources'])
        self.assertFalse('NonProdInstance' in self.obj['Resources'])

    def test_find(self):
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['FindInMapTest'], 'ami-use1')

    def test_if(self):
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['NestedIfTest'], 'c1.forprod')

    def test_pseudo_param(self):
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['PseudoParam'], 'us-east-1')

    def test_select(self):
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['SelectTest'], 'grapes')

    def test_sub(self):
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['SubTest'], 'arn:aws:ec2:us-east-1:1234567890:vpc/1')
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['SubTestArray'], 'www.1prod')
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['SubStackNameRegion']['Fn::Sub'], 'arn:aws:ec2:us-east-1:1234567890:vpc/${AWS::StackName}')
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['SubStackName']['Fn::Sub'], '${AWS::StackName}-low-prod')

    def test_userdata(self):
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['UserData']['Fn::Base64']['Fn::Join'][1][2]['Fn::Sub'], '/opt/aws/bin/cfn-init -v --stack ${AWS::StackName} --resource LaunchConfig --configsets wordpress_install --region us-east-1 prod')
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['UserData']['Fn::Base64']['Fn::Join'][1][3]['Fn::Sub'], '/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource WebServerGroup --region us-east-1 1')

    def test_evaluate_custom_expression(self):
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['CustomRef']['Ref'], 'TemplateNameResourceName')
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['CustomGetAtt']['Fn::GetAtt'], [ 'TemplateNameResourceName', 'Arn' ])
      
    def test_split(self):
        self.assertEqual(self.obj['Resources']['EC2Instance']['Properties']['SplitTest'], ['a', 'b', 'c'])

    def test_arrayfy_depends_on(self):
        self.assertTrue(type(self.obj['Resources']['ProdInstance']['DependsOn']) == list)
        self.assertTrue(type(self.obj['Resources']['DependsOnResource']['DependsOn']) == list)

if __name__ == '__main__':
    unittest.main()




