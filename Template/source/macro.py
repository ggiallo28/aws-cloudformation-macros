import os, io
import json
import boto3
from cfn_flip import flip
import json
import git
import traceback
from troposphere import cloudformation, Tags, Join, Ref
from utils import *

PREFIX = "Template::"
BRANCH_DEFAULT = 'master'
TEMPLATE_NAME_DEFAULT = 'template.yaml'

LAMBDA_ARN = os.environ["LAMBDA_ARN"] if "LAMBDA_ARN" in os.environ else "__main__"
s3 = boto3.client('s3')
cm = boto3.client('codecommit')

def get_param(name, properties, params):
    value = properties.get(name)
    return params[value["Ref"]] if type(value) == dict else value  

def s3_import(request_id, name, properties, params, region):
    bucket = get_param('Bucket', properties, params)
    if bucket is None:
      raise Exception('Bucket property must be provied when provider is S3.')
    key = get_param('Key', properties, params)
    if owner is None:
      raise Exception('Key property must be provied when provider is S3.')

    file = "/tmp/" + request_id + "/" + key.replace("/", "_") 

    with open(file, 'wb') as f:
        s3.download_fileobj(bucket, key, f)

    with open(file) as f:
        document = json.loads(flip(f.read()))

    return document

def github_import(request_id, name, properties, params, region):
    repo = get_param('Repo', properties, params)
    branch = get_param('Branch', properties, params)
    branch = BRANCH_DEFAULT if branch is None else branch
    owner = get_param('Owner', properties, params)
    if owner is None:
      raise Exception('Owner property must be provied when provider is GitHub.')
    token = get_param('OAuthToken', properties, params)
    token = "" if token is None else '{}@'.format(token)
    path = get_param('Path', properties, params)
    path = TEMPLATE_NAME_DEFAULT if token is None else path

    clone_dir = "/tmp/" + request_id  + "/github"
    if not os.path.exists(clone_dir + "/" + repo):
        repo_url =  "https://{}github.com/{}/{}.git".format(token, owner, repo)
        git.Git(clone_dir).clone(repo_url)

    file = clone_dir + "/" + repo + "/" + path
    with open(file) as f:
        document = json.loads(flip(f.read()))   

    return document
    
def codecommit_import(request_id, name, properties, params, region):
    repo = get_param('Repo', properties, params)
    branch = get_param('Branch', properties, params)
    branch = BRANCH_DEFAULT if branch is None else branch
    path = get_param('Path', properties, params)
    path = TEMPLATE_NAME_DEFAULT if token is None else path

    response = cm.get_file(repositoryName=repo, commitSpecifier = branch,  filePath=path)

    try:
      document = json.loads(response['fileContent'])
    except:
      document = json.loads(flip(response['fileContent']))  

    return document

def upload_to_s3(bucket, key, tp_model, params):
    value_bucket = params[bucket.data['Ref']] if isinstance(bucket, Ref) else bucket
    value_key = params[key.data['Ref']] if isinstance(key, Ref) else key

    try:
      template = tp_model.to_json()
      s3.upload_fileobj(io.BytesIO(template.encode()), value_bucket, value_key) 
    except:
      print("Unable to upload Template to S3 Bucket.")       

def get_stack_resource(tp_main_template, name, params, tp_model):
    bucket = tp_main_template.resources[name].properties['TemplateBucket']
    if 'TemplateKey' in tp_main_template.resources[name].properties:
        key = tp_main_template.resources[name].properties['TemplateKey']
    else:
        key = tp_main_template.resources[name].properties['Path']

    upload_to_s3(bucket, key, tp_model, params)

    nested_stack = cloudformation.Stack(title='NestedStack'+name)

    if 'NotificationARNs' in tp_main_template.resources[name].properties:
        nested_stack.NotificationARNs = tp_main_template.resources[name].properties['NotificationARNs']
    if 'Parameters' in tp_main_template.resources[name].properties:
        nested_stack.Parameters = tp_main_template.resources[name].properties['Parameters']
    if 'Tags' in tp_main_template.resources[name].properties:
        nested_stack.Tags = tp_main_template.resources[name].properties['Tags']
    if 'TimeoutInMinutes' in tp_main_template.resources[name].properties:
        nested_stack.TimeoutInMinutes = tp_main_template.resources[name].properties['TimeoutInMinutes']
    nested_stack.TemplateURL = Join("",['https://', bucket, '.s3.amazonaws.com/', key])

    return nested_stack

def get_inline_resource(properties, tp_model, name, rule):
    if 'Parameters' in properties:
        parameters = properties['Parameters']
        tp_model.set_default_parameters(parameters)
    tp_model.find_relations(to_replace=True, prefix=name, condition=rule)
    tp_model.del_parameters()

    return tp_model

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
                new_template += get_inline_resource(properties, tp_model, name, rule)
            if mode.lower() == "nested":
                nested_stack = get_stack_resource(tp_main_template, name, params, tp_model)
                new_template.add_resource(nested_stack)

        else:
            new_template.add_resource(tp_main_template.resources[name])

    return json.loads(new_template.to_json())

def handler(event, context):
    print(json.dumps(event))
    macro_response = {
        "fragment": event["fragment"],
        "status": "success",
        "requestId": event["requestId"]
    }    

    path = "/tmp/" + event["requestId"]

    try:
        os.mkdir(path)
        os.mkdir(path + "/github")
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)

    try:
        macro_response["fragment"] = handle_template(event["requestId"], event["fragment"], event["templateParameterValues"], event["region"])
    except Exception as e:
        traceback.print_exc()
        macro_response["status"] = "failure"
        macro_response["errorMessage"] = str(e)

    return macro_response

if __name__ == "__main__":
    handler({
  "accountId": "831650818513",
  "fragment": {
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
        "Default": "audioposts-site"
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
    "Resources": {
      "HighPriorityAlarm": {
        "Type": "AWS::SNS::Topic",
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
              "Ref": "HighPriorityAlarm"
            }
          ],
          "Tags": [
            {
              "Key": "Environment",
              "Value": {
                "Ref": "Environment"
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
    "Conditions": {
      "CreateResources": {
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
  "requestId": "c13c32e3-ef01-4c2d-b980-00ff99b76913",
  "region": "us-east-1",
  "params": {},
  "templateParameterValues": {
    "GitHubUser": "ggiallo28",
    "BucketName": "audioposts-site",
    "TemplateKey": "Template/sns-topics-template.yaml",
    "Environment": "prod",
    "RepositoryName": "aws-cloudformation-macros",
    "BranchName": "master"
  }
}, None)
