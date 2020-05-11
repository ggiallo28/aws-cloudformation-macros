import json
import unittest

from simulator import *
from utils import *
from troposphere import Join

import_template_dict = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "SNS Topics for alarms",
    "Parameters": {
        "Email": {
            "Type": "String",
            "Default": "nmsek@hi2.in"
        },
        "Name": {
            "Type": "String"
        },
        "Environment": {
            "Type": "String"
        }
    },
    "Conditions": {
        "CreateResources": {
            "Fn::Equals": [{
                    "Ref": "Environment"
                },
                "prod"
            ]
        }
    },
    "Resources": {
        "UrgentPriorityAlarm": {
            "Type": "AWS::SNS::Topic",
            "Properties": {
                "DisplayName": {
                    "Fn::Sub": "${Name}-Urgent-Priority-Alarm-${Environment}"
                },
                "Subscription": [{
                    "Endpoint": {
                        "Ref": "Email"
                    },
                    "Protocol": "email"
                }],
                "TopicName": {
                    "Fn::Sub": "${Name}-Urgent-Priority-Alarm-${Environment}"
                }
            }
        },
        "HighPriorityAlarm": {
            "Type": "AWS::SNS::Topic",
            "Properties": {
                "DisplayName": {
                    "Fn::Sub": "${Name}-High-Priority-Alarm-${Environment}"
                },
                "Subscription": [{
                    "Endpoint": {
                        "Ref": "Email"
                    },
                    "Protocol": "email"
                }],
                "TopicName": {
                    "Fn::Sub": "${Name}-High-Priority-Alarm-${Environment}"
                }
            }
        },
        "MediumPriorityAlarm": {
            "Type": "AWS::SNS::Topic",
            "Properties": {
                "DisplayName": {
                    "Fn::Sub": "${Name}-Medium-Priority-Alarm-${Environment}"
                },
                "Subscription": [{
                    "Endpoint": {
                        "Ref": "Email"
                    },
                    "Protocol": "email"
                }],
                "TopicName": {
                    "Fn::Sub": "${Name}-Medium-Priority-Alarm-${Environment}"
                }
            }
        },
        "LowPriorityAlarm": {
            "Type": "AWS::SNS::Topic",
            "Properties": {
                "DisplayName": {
                    "Fn::Sub": "${Name}-Low-Priority-Alarm-${Environment}"
                },
                "Subscription": [{
                    "Endpoint": {
                        "Ref": "Email"
                    },
                    "Protocol": "email"
                }],
                "TopicName": {
                    "Fn::Sub": "${Name}-Low-Priority-Alarm-${Environment}"
                }
            }
        },
        "SNSTopiInlineCondition": {
            "Type": "Template::Git",
            "Condition": "CreateResources",
            "Properties": {
                "Mode": "Inline",
                "Provider": "Github",
                "Repo": {
                    "Ref": "RepositoryName"
                },
                "Branch": {
                    "Ref": "BranchName"
                },
                "Path": {
                    "Ref": "TemplateKey"
                },
                "Owner": {
                    "Ref": "GitHubUser"
                },
                "Parameters": {
                    "Name": "sns-topic-template-codecommit-inline-stack-condition",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            } 
        },
        "SNSTopiInlineDependsOn": {
            "Type": "Template::Git",
            "Condition": "CreateResources",
            "DependsOn": "Template::SNSTopiInlineCondition",
            "Properties": {
                "Mode": "Inline",
                "Provider": "Github",
                "Repo": {
                    "Ref": "RepositoryName"
                },
                "Branch": {
                    "Ref": "BranchName"
                },
                "Path": {
                    "Ref": "TemplateKey"
                },
                "Owner": {
                    "Ref": "GitHubUser"
                },
                "Parameters": {
                    "Name": "sns-topic-template-codecommit-inline-stack-condition",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        }, 
        "SNSTopicNestedDefault": {
            "Type": "Template::Git",
            "Condition": "CreateResources",
            "DependsOn": "Template::SNSTopiInlineCondition",
            "Properties": {
                "Mode": "Nested",
                "Provider": "Github",
                "Repo": {
                    "Ref": "RepositoryName"
                },
                "Branch": {
                    "Ref": "BranchName"
                },
                "Path": {
                    "Ref": "TemplateKey"
                },
                "Owner": {
                    "Ref": "GitHubUser"
                },
                "Parameters": {
                    "Name": "sns-topic-template-github-nested-stack-default-bucket",
                    "Environment": {
                        "Ref": "Environment"
                    }
                },
                "NotificationARNs": [{
                        "Ref": "Template::SNSTopiInlineCondition::UrgentPriorityAlarm"
                    },
                    {
                        "Ref": "HighPriorityAlarm"
                    }
                ],
                "Tags": [{
                        "Key": "Environment",
                        "Value": {
                            "Ref": "Environment"
                        }
                    },
                    {
                        "Key": "TopicName",
                        "Value": {
                            "Fn::GetAtt": [
                                "Template::SNSTopiInlineCondition::UrgentPriorityAlarm",
                                "TopicName"
                            ]
                        }
                    }
                ],
                "TimeoutInMinutes": 1,
                "TemplateBucket": {
                    "Ref": "BucketName"
                },
                "TemplateKey": {
                    "Ref": "TemplateKey"
                }
            }
        }
    },
    "Outputs": {
        "UrgentPriorityAlarmArn": {
            "Description": "Urgent priority SNS topic ARN",
            "Value": {
                "Ref": "UrgentPriorityAlarm"
            },
            "Export": {
                "Name": {
                    "Fn::Sub": "${AWS::StackName}-urgent-${Environment}"
                }
            }
        },
        "HighPriorityAlarmArn": {
            "Description": "High priority SNS topic ARN",
            "Value": {
                "Ref": "HighPriorityAlarm"
            },
            "Export": {
                "Name": {
                    "Fn::Sub": "${AWS::StackName}-high-${Environment}"
                }
            }
        },
        "MediumPriorityAlarmArn": {
            "Description": "Medium priority SNS topic ARN",
            "Value": {
                "Ref": "MediumPriorityAlarm"
            },
            "Export": {
                "Name": {
                    "Fn::Sub": "${AWS::StackName}-medium-${Environment}"
                }
            }
        },
        "LowPriorityAlarmArn": {
            "Description": "Low priority SNS topic ARN",
            "Value": {
                "Ref": "LowPriorityAlarm"
            },
            "Export": {
                "Name": {
                    "Fn::Sub": "${AWS::StackName}-low-${Environment}"
                }
            }
        }
    }
}

main_template_dict = {
    "Transform": [
        "Template"
    ],
    "Description": "Example Macro Template.",
    "Parameters": {
        "GitHubUser": {
            "Type": "String",
            "Default": "ggiallo28"
        },
        "RepositoryName": {
            "Type": "String",
            "Default": "aws-cloudformation-macros"
        },
        "BranchName": {
            "Type": "String",
            "Default": "master"
        },
        "BucketName": {
            "Type": "String",
            "Default": "macro-template-default-831650818513-us-east-1"
        },
        "TemplateKey": {
            "Type": "String",
            "Default": "Template/sns-topics-template.yaml"
        },
        "Environment": {
            "Type": "String",
            "Default": "prod"
        }
    },
    "Conditions": {
        "CreateResources": {
            "Fn::Equals": [
                {
                    "Ref": "Environment"
                },
                "prod"
            ]
        }
    },
    "Resources": {
        "HighPriorityAlarm": {
            "Type": "AWS::SNS::Topic",
            "DependsOn" : "Template::SNSTopiInlineCondition",
            "Properties": {
                "TopicName": {
                    "Fn::Sub": "High-Priority-Alarm-${Environment}"
                }
            }
        },
        "HighPriorityAlarmDependsOnNested": {
            "Type": "AWS::SNS::Topic",
            "DependsOn" : "Template::SNSTopicNested",
            "Properties": {
                "TopicName": {
                    "Fn::Sub": "High-Priority-Alarm-${Environment}"
                }
            }
        },
        "SNSTopiInlineCondition": {
            "Type": "Template::Git",
            "Condition": "CreateResources",
            "Properties": {
                "Mode": "Inline",
                "Provider": "Github",
                "Repo": {
                    "Ref": "RepositoryName"
                },
                "Branch": {
                    "Ref": "BranchName"
                },
                "Path": {
                    "Ref": "TemplateKey"
                },
                "Owner": {
                    "Ref": "GitHubUser"
                },
                "Parameters": {
                    "Name": "sns-topic-template-codecommit-inline-stack-condition",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        },
        "SNSTopicNested": {
            "Type": "Template::Git",
            "Condition": "CreateResources",
            "DependsOn": "Template::SNSTopiInlineCondition",
            "Properties": {
                "Mode": "Nested",
                "Provider": "Github",
                "Repo": {
                    "Ref": "RepositoryName"
                },
                "Branch": {
                    "Ref": "BranchName"
                },
                "Path": {
                    "Ref": "TemplateKey"
                },
                "Owner": {
                    "Ref": "GitHubUser"
                },
                "Parameters": {
                    "Name": "sns-topic-template-github-nested-stack",
                    "Environment": {
                        "Ref": "Environment"
                    }
                },
                "NotificationARNs": [
                    {
                        "Ref": "Template::SNSTopiInlineCondition::UrgentPriorityAlarm"
                    },
                    {
                        "Ref": "HighPriorityAlarm"
                    }
                ],
                "Tags": [
                    {
                        "Key": "Environment",
                        "Value": {
                            "Ref": "Environment"
                        }
                    },
                    {
                        "Key": "TopicName",
                        "Value": {
                            "Fn::GetAtt": [
                                "Template::SNSTopiInlineCondition::UrgentPriorityAlarm",
                                "TopicName"
                            ]
                        }
                    }
                ],
                "TimeoutInMinutes": 1,
                "TemplateBucket": {
                    "Ref": "BucketName"
                },
                "TemplateKey": {
                    "Ref": "TemplateKey"
                }
            }
        },
        "SNSTopicNestedDefault": {
            "Type": "Template::Git",
            "Condition": "CreateResources",
            "DependsOn": ["HighPriorityAlarm"],
            "Properties": {
                "Mode": "Nested",
                "Provider": "Github",
                "Repo": {
                    "Ref": "RepositoryName"
                },
                "Branch": {
                    "Ref": "BranchName"
                },
                "Path": {
                    "Ref": "TemplateKey"
                },
                "Owner": {
                    "Ref": "GitHubUser"
                },
                "Parameters": {
                    "Name": "sns-topic-template-github-nested-stack-default-bucket",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        },
        "SNSTopicS3": {
            "Type": "Template::S3",
            "DependsOn": "Template::SNSTopicNested",
            "Properties": {
                "Mode": "Inline",
                "Bucket": {
                    "Ref": "BucketName"
                },
                "Key": {
                    "Ref": "TemplateKey"
                },
                "Parameters": {
                    "Name": "sns-topic-template-s3-inline-stack",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        },
        "DoubleSNSTopicS3": {
            "Type": "Template::S3",
            "DependsOn": ["Template::SNSTopicS3", "HighPriorityAlarm"],
            "Properties": {
                "Mode": "Inline",
                "Bucket": {
                    "Ref": "BucketName"
                },
                "Key": {
                    "Ref": "TemplateKey"
                },
                "Parameters": {
                    "Name": "sns-topic-template-s3-inline-stack",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        },
        "Nested2InlineTarget": {
            "Type": "Template::S3",
            "Properties": {
                "Mode": "Inline",
                "Bucket": {
                    "Ref": "BucketName"
                },
                "Key": {
                    "Ref": "TemplateKey"
                },
                "Parameters": {
                    "Name": "sns-topic-template-s3-inline-stack",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        },
        "Nested2InlineSource": {
            "Type": "Template::S3",
            "DependsOn": "Template::Nested2InlineTarget",
            "Properties": {
                "Mode": "Nested",
                "Bucket": {
                    "Ref": "BucketName"
                },
                "Key": {
                    "Ref": "TemplateKey"
                },
                "Parameters": {
                    "Name": "sns-topic-template-s3-inline-stack",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        },
        "Nested2NestedTarget": {
            "Type": "Template::S3",
            "DependsOn": ["Template::SNSTopicS3", "HighPriorityAlarm"],
            "Properties": {
                "Mode": "Inline",
                "Bucket": {
                    "Ref": "BucketName"
                },
                "Key": {
                    "Ref": "TemplateKey"
                },
                "Parameters": {
                    "Name": "sns-topic-template-s3-inline-stack",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        },
        "Nested2NestedSource": {
            "Type": "Template::S3",
            "DependsOn": "Template::Nested2NestedTarget",
            "Properties": {
                "Mode": "Nested",
                "Bucket": {
                    "Ref": "BucketName"
                },
                "Key": {
                    "Ref": "TemplateKey"
                },
                "Parameters": {
                    "Name": "sns-topic-template-s3-inline-stack",
                    "Environment": {
                        "Ref": "Environment"
                    }
                }
            }
        }
    }
}

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
        import_template = Simulator(import_template_dict, import_template_dict_params)
        import_template = import_template.simulate()
        cls.import_template = TemplateLoader.loads(import_template)

        cls._prefix = 'PREFIX'

    def test_obj(self):
        self.assertTrue(self.import_template)

    def test_evaluate_custom_expression(self):
        tdata = json.loads(self.import_template.to_json())

        self.assertEqual(tdata['Resources']['SNSTopicNestedDefault']['Properties']['NotificationARNs'][0]['Ref'], 'SNSTopiInlineConditionUrgentPriorityAlarm')
        self.assertEqual(tdata['Resources']['SNSTopicNestedDefault']['Properties']['Tags'][1]['Value']['Fn::GetAtt'], [ 'SNSTopiInlineConditionUrgentPriorityAlarm', 'TopicName' ])
      
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

        self.assertEqual(tdata['Outputs'][self._prefix + 'UrgentPriorityAlarmArn']['Export']['Name']['Fn::Join'], ['-', [self._prefix, {'Fn::Sub': '${AWS::StackName}-urgent-prod'}]])
        self.assertEqual(tdata['Outputs'][self._prefix + 'HighPriorityAlarmArn']['Export']['Name']['Fn::Join'], ['-', [self._prefix, {'Fn::Sub': '${AWS::StackName}-high-prod'}]])
        self.assertEqual(tdata['Outputs'][self._prefix + 'MediumPriorityAlarmArn']['Export']['Name']['Fn::Join'], ['-', [self._prefix, {'Fn::Sub': '${AWS::StackName}-medium-prod'}]])
        self.assertEqual(tdata['Outputs'][self._prefix + 'LowPriorityAlarmArn']['Export']['Name']['Fn::Join'], ['-', [self._prefix, {'Fn::Sub': '${AWS::StackName}-low-prod'}]])

        self.assertTrue(self._prefix + 'UrgentPriorityAlarm' in tdata['Resources'])
        self.assertTrue(self._prefix + 'HighPriorityAlarm' in tdata['Resources'])
        self.assertTrue(self._prefix + 'MediumPriorityAlarm' in tdata['Resources'])
        self.assertTrue(self._prefix + 'LowPriorityAlarm' in tdata['Resources'])       
        self.assertTrue(self._prefix + 'SNSTopiInlineCondition' in tdata['Resources'])
        self.assertTrue(self._prefix + 'SNSTopicNestedDefault' in tdata['Resources'])

        self.assertEqual(tdata['Resources'][self._prefix + 'SNSTopicNestedDefault']['Properties']['NotificationARNs'][1]['Ref'], self._prefix + 'HighPriorityAlarm')
        self.assertEqual(tdata['Resources'][self._prefix + 'SNSTopicNestedDefault']['Properties']['NotificationARNs'][0]['Ref'], 'SNSTopiInlineConditionUrgentPriorityAlarm')
        self.assertEqual(tdata['Resources'][self._prefix + 'SNSTopicNestedDefault']['Properties']['Tags'][1]['Value']['Fn::GetAtt'], [ 'SNSTopiInlineConditionUrgentPriorityAlarm', 'TopicName' ])


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
        cls.resources_list = ['UrgentPriorityAlarm', 'HighPriorityAlarm', 'MediumPriorityAlarm', 'LowPriorityAlarm', 'SNSTopiInlineCondition', 'SNSTopiInlineDependsOn', 'SNSTopicNestedDefault']


    def test_set_attrs_inline_dependson_nested(self):
        # Inline DependsOn Nested
        top_level_resource_id = 'SNSTopicS3'
        top_level_resource, inline_template = self.import_templates[top_level_resource_id]
        inline_template.set_attrs(top_level_resource, self.import_templates)
        inline_template_json = json.loads(inline_template.to_json())

        self.assertEqual(inline_template_json['Resources'][top_level_resource_id + 'UrgentPriorityAlarm']['DependsOn'], ['SNSTopicNested'])
        self.assertEqual(inline_template_json['Resources'][top_level_resource_id + 'HighPriorityAlarm']['DependsOn'], ['SNSTopicNested'])
        self.assertEqual(inline_template_json['Resources'][top_level_resource_id + 'MediumPriorityAlarm']['DependsOn'], ['SNSTopicNested'])
        self.assertEqual(inline_template_json['Resources'][top_level_resource_id + 'LowPriorityAlarm']['DependsOn'], ['SNSTopicNested'])
        self.assertEqual(inline_template_json['Resources'][top_level_resource_id + 'SNSTopicNestedDefault']['DependsOn'], ['SNSTopicNested', 'Template::{}SNSTopiInlineCondition'.format(top_level_resource_id)])
        self.assertEqual(inline_template_json['Resources'][top_level_resource_id + 'SNSTopiInlineDependsOn']['DependsOn'], ['SNSTopicNested', 'Template::{}SNSTopiInlineCondition'.format(top_level_resource_id)])     

    def test_set_attrs_inline_dependson_nested_or_aws(self):
        # Inline DependsOn Inline & Inline DependsOn AWS
        top_level_resource_id = 'DoubleSNSTopicS3'
        dependson_resource_id = 'SNSTopicS3'
        top_level_resource, inline_template = self.import_templates[top_level_resource_id]
        inline_template.set_attrs(top_level_resource, self.import_templates)
        inline_template_json = json.loads(inline_template.to_json())


        self.assertEqual(sorted(inline_template_json['Resources'][top_level_resource_id + 'UrgentPriorityAlarm']['DependsOn']), sorted(['{}{}'.format(dependson_resource_id, value) for value in self.resources_list] + ['HighPriorityAlarm']))
        self.assertEqual(sorted(inline_template_json['Resources'][top_level_resource_id + 'HighPriorityAlarm']['DependsOn']), sorted(['{}{}'.format(dependson_resource_id, value) for value in self.resources_list] + ['HighPriorityAlarm']))
        self.assertEqual(sorted(inline_template_json['Resources'][top_level_resource_id + 'MediumPriorityAlarm']['DependsOn']), sorted(['{}{}'.format(dependson_resource_id, value) for value in self.resources_list] + ['HighPriorityAlarm']))
        self.assertEqual(sorted(inline_template_json['Resources'][top_level_resource_id + 'LowPriorityAlarm']['DependsOn']), sorted(['{}{}'.format(dependson_resource_id, value) for value in self.resources_list] + ['HighPriorityAlarm']))
        self.assertEqual(sorted(inline_template_json['Resources'][top_level_resource_id + 'SNSTopicNestedDefault']['DependsOn']), sorted(['{}{}'.format(dependson_resource_id, value) for value in self.resources_list] + ['Template::{}SNSTopiInlineCondition'.format(top_level_resource_id)] + ['HighPriorityAlarm']))
        self.assertEqual(sorted(inline_template_json['Resources'][top_level_resource_id + 'SNSTopiInlineDependsOn']['DependsOn']), sorted(['{}{}'.format(dependson_resource_id, value) for value in self.resources_list] + ['Template::{}SNSTopiInlineCondition'.format(top_level_resource_id)] + ['HighPriorityAlarm']))

    def test_resolve_attrs_nested_dependson_inline(self):
        # Nested DependsOn Inline
        dependson_resource_id = 'Nested2InlineTarget'
        merge_template = TemplateLoader.init()
        merge_template.parameters = self.main_template.parameters
        merge_template.set_version()
        merge_template.add_resource(self.main_template.resources['Nested2InlineSource'])

        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())
        self.assertEqual(sorted(merge_template_json['Resources']['Nested2InlineSource']['DependsOn']), sorted(['{}{}'.format(dependson_resource_id, value) for value in self.resources_list]))

    def test_resolve_attrs_nested_dependson_nested(self):
        # Nested DependsOn Nested
        merge_template = TemplateLoader.init()
        merge_template.parameters = self.main_template.parameters
        merge_template.set_version()
        merge_template.add_resource(self.main_template.resources['Nested2NestedTarget'])
        merge_template.add_resource(self.main_template.resources['Nested2NestedSource'])

        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())
        self.assertEqual(merge_template_json['Resources']['Nested2NestedSource']['DependsOn'], ['Nested2NestedTarget'])

    def test_resolve_attrs_aws_dependson_inline(self):
        # AWS DependsOn Inline
        dependson_resource_id = 'SNSTopiInlineCondition'
        merge_template = TemplateLoader.init()
        merge_template.parameters = self.main_template.parameters
        merge_template.set_version()

        merge_template.add_resource(self.main_template.resources['HighPriorityAlarm'])
        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())
        self.assertEqual(sorted(merge_template_json['Resources']['HighPriorityAlarm']['DependsOn']), sorted(['{}{}'.format(dependson_resource_id, value) for value in self.resources_list]))

    def test_resolve_attrs_aws_dependson_nested(self):
        # AWS DependsOn Nested
        dependson_resource_id = 'SNSTopicNested'
        merge_template = TemplateLoader.init()
        merge_template.parameters = self.main_template.parameters
        merge_template.set_version()

        merge_template.add_resource(self.main_template.resources['HighPriorityAlarmDependsOnNested'])
        merge_template.add_resource(self.main_template.resources['SNSTopicNested'])
        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())
        self.assertEqual(merge_template_json['Resources']['HighPriorityAlarmDependsOnNested']['DependsOn'], ['SNSTopicNested'])

    def test_resolve_attrs_nested_dependson_aws(self):
        # Nested DependsOn AWS
        dependson_resource_id = 'HighPriorityAlarm'
        merge_template = TemplateLoader.init()
        merge_template.parameters = self.main_template.parameters
        merge_template.set_version()

        merge_template.add_resource(self.main_template.resources['HighPriorityAlarm'])
        merge_template.add_resource(self.main_template.resources['SNSTopicNestedDefault'])
        merge_template.resolve_attrs(self.import_templates)
        merge_template_json = json.loads(merge_template.to_json())
        self.assertEqual(merge_template_json['Resources']['SNSTopicNestedDefault']['DependsOn'], ['HighPriorityAlarm'])

    def test_get_stack_template(self):
        request_id = 'test_get_stack_template'
        resource_obj = self.main_template.resources['SNSTopicNested']
        resource_id = 'SNSTopicNested'

        nested_stack = get_stack_template(request_id, resource_obj, resource_id, main_template_dict_params, self.SNSTopicNested)

        self.assertEqual(nested_stack.resource['DependsOn'], ['Template::SNSTopiInlineCondition'])

if __name__ == '__main__':
    unittest.main()