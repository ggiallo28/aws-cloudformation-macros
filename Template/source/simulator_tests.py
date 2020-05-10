import json
import unittest

from simulator import *

data = {
  'AWSTemplateFormatVersion' : '2010-09-09',

  'Mappings' : {
    'RegionMap' : {
      'us-east-1'      : { 'AMI' : 'ami-use1'},
      'us-west-1'      : { 'AMI' : 'ami-usw1'},
      'us-west-2'      : { 'AMI' : 'ami-usw2'}
    }
  },
  
  'Parameters' : {
    'EnvType' : {
      'Default' : 'test',
      'Type' : 'String',
      'AllowedValues' : ['prod', 'dev', 'test']
    },
    'NameIndex' : {
        'Default': 0,
        'Type' : 'Number'
    }
  },
  
  'Conditions' : {
    'CreateProdResources' : {'Fn::Equals' : [{'Ref' : 'EnvType'}, 'prod']},
    'CreateDevResources' : {'Fn::Equals' : [{'Ref' : 'EnvType'}, 'dev']},
    'OrTest' : {'Fn::Or': [ {'Condition':'CreateProdResources'}, {'Condition':'CreateDevResources'} ]},
    'NonProd' : {'Fn::Not': [{'Condition':'CreateProdResources'}]},
    'AndTest' : {'Fn::And': [ {'Condition':'CreateProdResources'}, {'Condition':'CreateDevResources'} ]}
  },
  
  'Resources' : {
    'EC2Instance' : {
      'Type' : 'AWS::EC2::Instance',
      'Properties' : {
        'FindInMapTest' : { 'Fn::FindInMap' : [ 'RegionMap', { 'Ref' : 'AWS::Region' }, 'AMI' ]},
        'NestedIfTest' : { 'Fn::If' : [
          'CreateProdResources',
          'c1.forprod',
          {'Fn::If' : [
            'CreateDevResources',
            'm1.forDevstuff',
            'm1.forOtherEnvs'
          ]}
        ]},
        'SelectTest': { 'Fn::Select' : [ {'Ref': 'NameIndex'}, [ 'apples', 'grapes', 'oranges', 'mangoes' ] ] },
        'JoinTest' : {'Fn::Join' : [ ':', [ 'a', 'b', 'c' ] ]},
        'SubTest' : { 'Fn::Sub': 'arn:aws:ec2:${AWS::Region}:${AWS::AccountId}:vpc/${NameIndex}' },
        'SubTestArray' : { 'Fn::Sub': [ 'www.${NameIndex}', {'Fn::Sub' : '${EnvType}' } ]},
        'SplitTest' : {'Fn::Split' : [ ':', 'a:b:c' ]},
        'SubStackName' : {'Fn::Sub': '${AWS::StackName}-low-${EnvType}'},
        'SubStackNameRegion' : { 'Fn::Sub': 'arn:aws:ec2:${AWS::Region}:${AWS::AccountId}:vpc/${AWS::StackName}' },
        'PseudoParam' : {'Ref': 'AWS::Region'},
        'CustomRef': { "Ref" : "Template::TemplateName::ResourceName" },
        'CustomGetAtt': { "Fn::GetAtt" : [ "Template::TemplateName::ResourceName", "Arn" ] },
        'UserData': { 'Fn::Base64': { 'Fn::Join': ['\n', [
          '#!/bin/bash -xe',
          'yum update -y aws-cfn-bootstrap',
          { 'Fn::Sub': '/opt/aws/bin/cfn-init -v --stack ${AWS::StackName} --resource LaunchConfig --configsets wordpress_install --region ${AWS::Region} ${EnvType}' },
          { 'Fn::Sub': '/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource WebServerGroup --region ${AWS::Region} ${NameIndex}' }]]
        }}
      }
    },
    'ProdInstance' : {
      'Type' : 'AWS::EC2::Instance',
      'DependsOn' : 'EC2Instance',
      'Properties' : {
        'Name': 'ProdOnly'
      },
      'Condition':'CreateProdResources'
    },
    'DependsOnResource' : {
      'Type' : 'AWS::EC2::Instance',
      'DependsOn' : ['ProdInstance'],
      'Properties' : {
        'Name': 'ProdOnly'
      },
      'Condition':'CreateProdResources'
    },
    'NonProdInstance' : {
      'Type' : 'AWS::EC2::Instance',
      'Properties' : {
        'Name': 'aNonProdInstance'
      },
      'Condition':'NonProd'
    }
  }
}

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




