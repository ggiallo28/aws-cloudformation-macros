import sys
sys.path.insert(1, 'source/libs')
sys.path.insert(1, 'source')

import json
import unittest
import logging

logging.basicConfig(level=logging.INFO)

from simulator import *
from cfn_flip import to_json

with open('test/simulator_test.yaml') as f:
    content = f.readlines()

data = json.loads(to_json(''.join(content)))

params = {'EnvType': 'prod', 'NameIndex': '1'}


class TestSimulatorMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfn = Simulator(data, params)
        cls.obj = cls.cfn.simulate(excude_clean=['Conditions'])

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
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']
            ['FindInMapTest'], 'ami-use1')

    def test_if(self):
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['NestedIfTest'],
            'c1.forprod')

    def test_pseudo_param(self):
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['PseudoParam'],
            'us-east-1')

    def test_select(self):
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['SelectTest'],
            'grapes')

    def test_sub(self): 
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['SubTest'],
            'arn:aws:ec2:us-east-1:1234567890:vpc/1')
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['SubTestArray'],
            'www.1prod')
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']
            ['SubStackNameRegion']['Fn::Join'][1],
            ['arn:aws:ec2:us-east-1:1234567890:vpc/',{"Ref": "AWS::StackName"}])
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['SubStackName']
            ['Fn::Join'][1], [{"Ref": "AWS::StackName"},'-low-prod'])

    def test_userdata(self):
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['UserData']
            ['Fn::Base64']['Fn::Join'][1][2]['Fn::Join'][1],
            ['/opt/aws/bin/cfn-init -v --stack ', {'Ref': 'AWS::StackName'},' --resource LaunchConfig --configsets wordpress_install --region us-east-1 prod']
        )
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['UserData']
            ['Fn::Base64']['Fn::Join'][1][3]['Fn::Join'][1],
            ['/opt/aws/bin/cfn-signal -e $? --stack ', {'Ref': 'AWS::StackName'} ,' --resource WebServerGroup --region us-east-1 1']
        )

    def test_split(self):
        self.assertEqual(
            self.obj['Resources']['EC2Instance']['Properties']['SplitTest'],
            ['a', 'b', 'c'])

    def test_arrayfy_depends_on(self):
        self.assertTrue(
            type(self.obj['Resources']['ProdInstance']['DependsOn']) == list)
        self.assertTrue(
            type(self.obj['Resources']['DependsOnResource']['DependsOn']) ==
            list)

    def test_sub_to_join(self):
        source = {
            "test1": { "Fn::Sub": [ "www.${Domain}", { "Domain": {"Ref" : "RootDomainName" }} ]},
            "test2": { "Fn::Sub": "arn:aws:ec2: ${AWS::Region}:${AWS::AccountId}:vpc/${vpc}" },
            "test3": { "Fn::Sub": [ "www.${Domain}", { "Domain": { "Fn::Sub": "arn:aws:ec2:${AWS::Region}:${AWS::AccountId}:vpc/${vpc}" }} ]}
        }
        target = {
            "test1": { "Fn::Join": ["",[ "www.", {"Ref" : "RootDomainName" } ]]},
            "test2": { "Fn::Join": ["",["arn:aws:ec2: ",{"Ref": "AWS::Region"},":",{"Ref" : "AWS::AccountId"},":vpc/",{"Ref":"vpc"}]]},
            "test3": { "Fn::Join": ["", ["www.", 
                    { "Fn::Join": ["", ["arn:aws:ec2:", { "Ref": "AWS::Region" }, ":", { "Ref": "AWS::AccountId" }, ":vpc/", { "Ref": "vpc" }]]} 
                ]] }
        }        

        result = self.cfn.sub_to_join(source)
        self.assertEqual(result['test1'], target['test1'])
        self.assertEqual(result['test2'], target['test2'])
        self.assertEqual(result['test3'], target['test3'])


if __name__ == '__main__':
    unittest.main()
