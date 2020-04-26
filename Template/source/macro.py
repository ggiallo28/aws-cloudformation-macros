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
from utils import *

PREFIX = "Template::"

LAMBDA_ARN = os.environ["LAMBDA_ARN"] if "LAMBDA_ARN" in os.environ else "__main__"
s3 = boto3.client('s3')

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
    path = get_param('Path', properties, params)

    clone_dir = "/tmp/" + request_id + "/codecommit"
    if not os.path.exists(clone_dir + "/" + repo):
        repo_url =  "https://git-codecommit.{}.amazonaws.com/v1/repos/{}".format(region, repo)
        git.Git(clone_dir).clone(repo_url)

    file = clone_dir + "/" + repo + "/" + path
    with open(file) as f:
        document = json.loads(flip(f.read()))   

    return document

switcher = {
    'codecommit' : codecommit_import,
    's3' : s3_import,
    'github' : github_import
}

def load_json(document):
    pass

def handle_template(request_id, template, params, region):
  tp_template = TemplateLoader.loads(template)
  new_template = TemplateLoader.init()

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
          
          tp_model = TemplateLoader.loads(model, prefix=name)
          
          mode = properties.get("Mode", "Inline")
          if mode == "Inline":
            new_template += tp_model


          #parameters = properties.get("Parameters")    
          #values = {'Values': properties.get("Static", []) + properties.get("Dynamic", [])}
          #resource.update({
          #    "Type": "Custom::Template",
          #    "Version": "1.0",
          #    "Properties": {
          #        "ServiceToken": LAMBDA_ARN,
#         #           "Mode": resource.get("Mode", ["Create", "Update"]),
          #        "Action": resource["Type"][len(PREFIX):],
          #        "Properties": values,
          #    },
          #})
          #print("after", name, resource)

          if "Mode" in resource:
              del resource["Mode"]
              
  print(new_template.to_yaml())

  return template

def handler(event, context):
    fragment = event["fragment"]
    status = "success"

    path = "/tmp/" + event["requestId"]

    try:
        os.mkdir(path)
        os.mkdir(path + "/github")
        os.mkdir(path + "/codecommit")
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)

    #try:
    fragment = handle_template(event["requestId"], event["fragment"], event["templateParameterValues"], event["region"])
    #except Exception as e:
    #    status = "failure"

    return {
        "requestId": event["requestId"],
        "status": status,
        "fragment": fragment,
    }

if __name__ == "__main__":
    handler({
  "accountId": "831650818513",
  "fragment": {
    "Parameters": {
      "GitHubUser": {
        "Type": "String",
        "Default": "ggiallo28"
      },
      "RepositoryName": {
        "Type": "String",
        "Default": "template-macro"
      },
      "BranchName": {
        "Type": "String",
        "Default": "master"
      },
      "GitHubToken": {
        "Type": "String",
        "Default": "3323ce281edb2c489c31aa7a2366b7d5045ac9aa"
      },
      "BucketName": {
        "Type": "String",
        "Default": "audioposts-site"
      },
      "TemplateKey": {
        "Type": "String",
        "Default": "test/sns-topics.yaml"
      }
    },
    "Resources": {
      "SNSTopicNested": {
        "Type": "Template::Git",
        "Properties": {
          "Mode": "Nested",
          "Provider": "GitHub",
          "Owner": {
            "Ref": "GitHubUser"
          },
          "Repo": {
            "Ref": "RepositoryName"
          },
          "Branch": {
            "Ref": "BranchName"
          },
          "OAuthToken": {
            "Ref": "GitHubToken"
          },
          "Path": {
            "Ref": "TemplateKey"
          },
          "Parameters": {
            "Name": "sns-topic-template-github-nested-stack"
          }
        }
      },
      "SNSTopicInline": {
        "Type": "Template::Git",
        "Properties": {
          "Mode": "Inline",
          "Repo": {
            "Ref": "RepositoryName"
          },
          "Branch": {
            "Ref": "BranchName"
          },
          "Provider": "Codecommit",
          "Parameters": {
            "Name": "sns-topic-template-codecommit-inline-stack"
          },
          "Path": {
            "Ref": "TemplateKey"
          }
        }
      },
      "SNSTopicS3": {
        "Type": "Template::S3",
        "Properties": {
          "Mode": "Inline",
          "Bucket": {
            "Ref": "BucketName"
          },
          "Key": {
            "Ref": "TemplateKey"
          },
          "Provider": "S3",
          "Parameters": {
            "Name": "sns-topic-template-s3-inline-stack"
          }
        }
      }
    }
  },
  "transformId": "831650818513::Template",
  "requestId": "zcca5cb0f0-78e6-4834-8198-398961421233",
  "region": "us-east-1",
  "params": {},
  "templateParameterValues": {
    "GitHubUser": "ggiallo28",
    "BucketName": "audioposts-site",
    "TemplateKey": "test/sns-topics.yaml",
    "RepositoryName": "template-macro",
    "BranchName": "master",
    "GitHubToken": "3323ce281edb2c489c31aa7a2366b7d5045ac9aa"
  }
}, None)
