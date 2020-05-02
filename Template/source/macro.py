# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import os
import json
import boto3
from cfn_flip import flip
import json
import git
#import traceback
from troposphere import cloudformation, Tags, Join, Ref
from utils import *

PREFIX = "Template::"

LAMBDA_ARN = os.environ["LAMBDA_ARN"] if "LAMBDA_ARN" in os.environ else "__main__"
s3 = boto3.client('s3')
cm = boto3.client('codecommit')

def get_param(name, properties, params):
    value = properties.get(name)
    return params[value["Ref"]] if type(value) == dict else value  

def s3_import(request_id, name, properties, params, region):
    bucket = get_param('Bucket', properties, params)
    key = get_param('Key', properties, params)

    file = "/tmp/" + request_id + "/" + key.replace("/", "_") 

    with open(file, 'wb') as f:
        s3.download_fileobj(bucket, key, f)

    with open(file) as f:
        document = json.loads(flip(f.read()))

    return document

def github_import(request_id, name, properties, params, region):
    repo = get_param('Repo', properties, params)
    branch = get_param('Branch', properties, params)
    owner = get_param('Owner', properties, params)
    token = get_param('OAuthToken', properties, params)
    path = get_param('Path', properties, params)

    clone_dir = "/tmp/" + request_id  + "/github"
    if not os.path.exists(clone_dir + "/" + repo):
        repo_url =  "https://{}@github.com/{}/{}.git".format(token, owner, repo)
        git.Git(clone_dir).clone(repo_url)

    file = clone_dir + "/" + repo + "/" + path
    with open(file) as f:
        document = json.loads(flip(f.read()))   

    return document
    
def codecommit_import(request_id, name, properties, params, region):
    repo = get_param('Repo', properties, params)
    branch = get_param('Branch', properties, params)
    branch = 'master' if branch is None else branch
    path = get_param('Path', properties, params)

    response = cm.get_file(repositoryName=repo, commitSpecifier = branch,  filePath=path)
    document = json.loads(flip(response['fileContent']))  

    return document

switcher = {
    'codecommit' : codecommit_import,
    's3' : s3_import,
    'github' : github_import
}

def handle_template(request_id, template, params, region):
    tp_main_template = TemplateLoader.loads(template)
    new_template = TemplateLoader.init()
    new_template.parameters = tp_main_template.parameters
    new_template.conditions = tp_main_template.conditions

    for name, resource in template.get("Resources", {}).items():
        if resource["Type"].startswith(PREFIX):
            properties = resource.get("Properties", {})

            if 's3' in resource["Type"].lower():
                model = switcher['s3'](request_id, name, properties, params, region)
            if 'git' in resource["Type"].lower():
                if "github" in properties["Provider"].lower():
                    model = switcher['github'](request_id, name, properties, params, region)
            if 'git' in resource["Type"].lower():
                if "codecommit" in properties["Provider"].lower():
                    model = switcher['codecommit'](request_id, name, properties, params, region) 
          
            tp_model = TemplateLoader.loads(model)
            mode = properties.get("Mode", "Inline")
            parameters = properties.get("Parameters", {})

            rule = None
            if  hasattr(tp_main_template.resources[name], 'Condition'):
                key = tp_main_template.resources[name].Condition
                rule = {
                    "key": key,
                    "value" : tp_main_template.conditions[key]
                }

            if mode.lower() == "inline":
                if 'Parameters' in properties:
                    parameners = properties['Parameters']
                    tp_model.set_default_parameters(parameters)
                tp_model.find_relations(to_replace=True, prefix=name, condition=rule)
                tp_model.del_parameters()

                new_template += tp_model
            if mode.lower() == "nested":
                bucket = tp_main_template.resources[name].properties['TemplateBucket']
                if 'TemplateKey' in tp_main_template.resources[name].properties:
                    key = tp_main_template.resources[name].properties['TemplateKey']
                else:
                    key = tp_main_template.resources[name].properties['Path']
                nested_stack = cloudformation.Stack(title='NestedStack'+name)
                if 'NotificationARNs' in tp_main_template.resources[name].properties:
                    nested_stack.NotificationARNs = tp_main_template.resources[name].properties['NotificationARNs']
                if 'Parameters' in tp_main_template.resources[name].properties:
                    nested_stack.Parameters = tp_main_template.resources[name].properties['Parameters']
                if 'Tags' in tp_main_template.resources[name].properties:
                    nested_stack.Tags = tp_main_template.resources[name].properties['Tags']
                if 'TimeoutInMinutes' in tp_main_template.resources[name].properties:
                    nested_stack.TimeoutInMinutes = tp_main_template.resources[name].properties['TimeoutInMinutes']
                nested_stack.TemplateURL = Join("",["https://s3-", Ref("AWS::Region"), ".amazonaws.com/", bucket, "/", key])

                new_template.add_resource(nested_stack)
        else:
            new_template.add_resource(tp_main_template.resources[name])

    return json.loads(new_template.to_json())

def handler(event, context):
    print(json.dumps(event))
    fragment = event["fragment"]
    status = "success"

    path = "/tmp/" + event["requestId"]

    try:
        os.mkdir(path)
        os.mkdir(path + "/github")
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)

    #try:
    fragment = handle_template(event["requestId"], event["fragment"], event["templateParameterValues"], event["region"])
    print(json.dumps(fragment))
    #except Exception as e:
    #    status = "failure"

    return {
        "requestId": event["requestId"],
        "status": status,
        "fragment": fragment
    }

if __name__ == "__main__":
    handler({
    "accountId": "831650818513",
    "fragment": {
        "Parameters": {
            "RepositoryName": {
                "Type": "String",
                "Default": "template-macro"
            },
            "BranchName": {
                "Type": "String",
                "Default": "master"
            },
            "BucketName": {
                "Type": "String",
                "Default": "audioposts-site"
            },
            "TemplateKey": {
                "Type": "String",
                "Default": "test/sns-topics.yaml"
            },
            "Environment": {
                "Type": "String",
                "Default": "dev"
            }
        },
        "Resources": {
            "SNSTopiInlineCondition": {
                "Type": "Template::Git",
                "Condition": "CreateProdResources",
                "Properties": {
                    "Mode": "Inline",
                    "Provider": "Codecommit",
                    "Repo": {
                        "Ref": "RepositoryName"
                    },
                    "Branch": {
                        "Ref": "BranchName"
                    },
                    "Path": {
                        "Ref": "TemplateKey"
                    },
                    "Parameters": {
                        "Name": "sns-topic-template-codecommit-inline-stack-condition",
                        "Environment": {
                            "Ref": "Environment"
                        }
                    }
                }
            },
            "SNSTopiInline": {
                "Type": "Template::Git",
                "Properties": {
                    "Mode": "Inline",
                    "Provider": "Codecommit",
                    "Repo": {
                        "Ref": "RepositoryName"
                    },
                    "Branch": {
                        "Ref": "BranchName"
                    },
                    "Path": {
                        "Ref": "TemplateKey"
                    },
                    "Parameters": {
                        "Name": "sns-topic-template-codecommit-inline-stack",
                        "Environment": {
                            "Ref": "Environment"
                        }
                    }
                }
            },
            "SNSTopicS3": {
                "Type": "Template::S3",
                "Properties": {
                    "Mode": "Inline",
                    "Provider": "S3",
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
        },
        "Conditions": {
            "CreateProdResources": {
                "Fn::Equals": [
                    {
                        "Ref": "Environment"
                    },
                    "prod"
                ]
            }
        }
    },
    "transformId": "831650818513::Template",
    "requestId": "38307b43-4854-4423-a332-0e9b587bc87b",
    "region": "us-east-1",
    "params": {},
    "templateParameterValues": {
        "BucketName": "audioposts-site",
        "TemplateKey": "test/sns-topics.yaml",
        "Environment": "dev",
        "RepositoryName": "template-macro",
        "BranchName": "master"
    }
}, None)
