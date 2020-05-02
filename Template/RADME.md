# How to install and use the Template macro in your AWS account

The `Template` macro adds the ability to create CloudFormation resources from existing Cloudformation Templates.

## Deploying

1. You will need an S3 bucket to store the CloudFormation artifacts:
    * If you don't have one already, create one with `aws s3 mb s3://<bucket name>`

2. Package the CloudFormation template. The provided template uses [the AWS Serverless Application Model](https://aws.amazon.com/about-aws/whats-new/2016/11/introducing-the-aws-serverless-application-model/) so must be transformed before you can deploy it.

    ```shell
    aws cloudformation package \
        --template-file template.yaml \
        --s3-bucket <your bucket name here> \
        --output-template-file template.output
    ```

3. Deploy the packaged CloudFormation template to a CloudFormation stack:

    ```shell
    aws cloudformation deploy \
        --stack-name template-macro \
        --template-file template.output \
        --capabilities CAPABILITY_IAM
    ```

4. To test out the macro's capabilities, try launching the provided example template:

    ```shell
    aws cloudformation deploy \
        --stack-name template-macro-example \
        --template-file example.yaml
    ```

# Custom Resources

## Template::Git

This Macro uses two Custom Resources.

The Template::Git imports Cloudformation Template from Git Repository.

### Syntax

To declare this entity in your AWS CloudFormation template, use the following syntax:

#### JSON
```
{
  "firstName": "John",
  "lastName": "Smith",
  "age": 25
}
```

#### YAML
```
Type: AWS::SNS::Topic
Properties: 
  DisplayName: String
  KmsMasterKeyId: String
  Subscription: 
    - Subscription
  Tags: 
    - Tag
  TopicName: String
`````

### Properties

`DisplayName`

The display name to use for an Amazon SNS topic with SMS subscriptions.

_Required_: No

_Type_: String

### Return Values

[WIP]

### Examples

#### Import Template Inline From Codecommit

#### JSON
```
{
   "Transform": [
      "Template"
   ],
   "Description": "Example Macro Template.",
   "Parameters": {
      "RepositoryName": {
         "Type": "String",
         "Default": "template-macro"
      },
      "BranchName": {
         "Type": "String",
         "Default": "master"
      },
      "TemplateKey": {
         "Type": "String",
         "Default": "test/remote-template.yaml"
      },
      "Environment": {
         "Type": "String",
         "Default": "dev"
      }
   },
   "Resources": {
      "Template": {
         "Type": "Template::Git",
         "Properties": {
            "Mode": "Inline",
            "Provider": "Codecommit",
            "Repo": { 
	       	  "Ref" : "RepositoryName" 
	        },
            "Branch": { 
	       	  "Ref" : "BranchName" 
	        },
            "Path": { 
	       	  "Ref" : "TemplateKey" 
	        },
            "Parameters": {
               "Name": "codecommit-example",
               "Environment": { 
	       	      "Ref" : "Environment" 
	            }
            }
         }
      }
   }
}
```

#### YAML
```
Transform: [Template]

Description: Example Macro Template.

Parameters:
  RepositoryName:
    Type: String
    Default: template-macro
  BranchName:
    Type: String
    Default: master
  TemplateKey:
    Type: String
    Default: test/remote-template.yaml
  Environment:
    Type: String
    Default: dev

Resources:
  Template:
    Type: "Template::Git"
    Properties:
      Mode: Inline
      Provider: Codecommit
      Repo: !Ref RepositoryName
      Branch: !Ref BranchName
      Path: !Ref TemplateKey
      Parameters:
        Name: "codecommit-example"
        Environment: !Ref Environment
```

#### Import Template Inline From Github

#### JSON
```
{
   "Transform": [
      "Template"
   ],
   "Description": "Example Macro Template.",
   "Parameters": {
      "RepositoryName": {
         "Type": "String",
         "Default": "template-macro"
      },
      "BranchName": {
         "Type": "String",
         "Default": "master"
      },
      "GitHubUser": {
         "Type": "String",
         "Default": "user"
      },
      "GitHubToken": {
         "Type": "String",
         "Default": "OAuthToken"
      },
      "TemplateKey": {
         "Type": "String",
         "Default": "test/remote-template.yaml"
      },
      "Environment": {
         "Type": "String",
         "Default": "dev"
      }
   },
   "Resources": {
      "Template": {
         "Type": "Template::Git",
         "Properties": {
            "Mode": "Inline",
            "Provider": "Github",
            "Repo": { 
	       	   "Ref" : "RepositoryName" 
	        },
            "Branch": { 
	       	   "Ref" : "BranchName" 
	        },
            "Owner": { 
	       	   "Ref" : "GitHubUser" 
	        },
            "OAuthToken": { 
	       	   "Ref" : "GitHubToken" 
	        },
            "Path": { 
	       	   "Ref" : "TemplateKey" 
	        },
            "Parameters": {
               "Name": "github-example",
               "Environment": { 
	       	      "Ref" : "Environment" 
	            }
            }
         }
      }
   }
}
```

#### YAML
```
Transform: [Template]

Description: Example Macro Template.

Parameters:
  RepositoryName:
    Type: String
    Default: template-macro
  BranchName:
    Type: String
    Default: master
  GitHubUser:
    Type: String
    Default: user
  GitHubToken:
    Type: String
    Default: OAuthToken
  TemplateKey:
    Type: String
    Default: test/remote-template.yaml
  Environment:
    Type: String
    Default: dev

Resources:
  Template:
    Type: "Template::Git"
    Properties:
      Mode: Inline
      Provider: Github
      Repo: !Ref RepositoryName
      Branch: !Ref BranchName
      Owner: !Ref GitHubUser
      OAuthToken: !Ref GitHubToken
      Path: !Ref TemplateKey
      Parameters:
        Name: "github-example"
        Environment: !Ref Environment
```

#### Import Template Nested

#### JSON
```
{
   "Transform": [
      "Template"
   ],
   "Description": "Example Macro Template.",
   "Parameters": {
      "RepositoryName": {
         "Type": "String",
         "Default": "template-macro"
      },
      "BranchName": {
         "Type": "String",
         "Default": "master"
      },
      "GitHubUser": {
         "Type": "String",
         "Default": "user"
      },
      "GitHubToken": {
         "Type": "String",
         "Default": "OAuthToken"
      },
      "TemplateKey": {
         "Type": "String",
         "Default": "test/remote-template.yaml"
      },
      "TemplateBucket": {
         "Type": "String",
         "Default": "example-bucket"
      },
      "Environment": {
         "Type": "String",
         "Default": "dev"
      }
   },
   "Resources": null,
   "Notification": {
      "Type": "AWS::SNS::Topic",
      "Properties": {
         "TopicName": "topic-name"
      }
   },
   "Template": {
      "Type": "Template::Git",
      "Properties": {
         "Mode": "Nested",
         "Provider": "Github",
         "Repo": { 
	       "Ref" : "RepositoryName" 
	     },
         "Branch": { 
	       	"Ref" : "BranchName" 
	     },
         "Owner": { 
	       	"Ref" : "GitHubUser" 
	     },
         "OAuthToken": { 
	       	"Ref" : "GitHubToken" 
	     },
         "Path": { 
	       	"Ref" : "TemplateKey" 
	     },
         "Parameters": {
            "Name": "github-example",
            "Environment": { 
	       	    "Ref" : "Environment" 
	        }
         },
         "NotificationARNs": [
            { 
            	"Fn::GetAtt" : [ "Notification", "Arn" ] 
            }
         ],
         "Tags": [
            {
               "Key": "Environment",
               "Value": { 
	       	      "Ref" : "Environment" 
	            }
            }
         ],
         "TimeoutInMinutes": 1,
         "TemplateBucket": { 
	       	"Ref" : "TemplateBucket" 
	     },
         "TemplateKey": { 
	       	"Ref" : "TemplateKey" 
	     }
      }
   }
}
```

#### YAML
```
Transform: [Template]

Description: Example Macro Template.

Parameters:
  RepositoryName:
    Type: String
    Default: template-macro
  BranchName:
    Type: String
    Default: master
  GitHubUser:
    Type: String
    Default: user
  GitHubToken:
    Type: String
    Default: OAuthToken
  TemplateKey:
    Type: String
    Default: test/remote-template.yaml
  BucketName:
    Type: String
    Default: example-bucket
  Environment:
    Type: String
    Default: dev

Resources:

Notification:
  Type: "AWS::SNS::Topic"
  Properties: 
    TopicName: 'topic-name'

Template:
  Type: "Template::Git"
  Properties:
    Mode: Nested
    Provider: Github
    Repo: !Ref RepositoryName
    Branch: !Ref BranchName
    Owner: !Ref GitHubUser
    OAuthToken: !Ref GitHubToken
    Path: !Ref TemplateKey
    Parameters:
      Name: "github-example"
      Environment: !Ref Environment
    NotificationARNs:
      - !GetAtt Notification.Arn
    Tags: 
      - Key: Environment
        Value: !Ref Environment
    TimeoutInMinutes: 1
    TemplateBucket: !Ref BucketName
    TemplateKey: !Ref TemplateKey
```

#### Import Multiple Template

#### JSON
```
{
   "Transform": [
      "Template"
   ],
   "Description": "Example Macro Template.",
   "Parameters": {
      "RepositoryName": {
         "Type": "String",
         "Default": "template-macro"
      },
      "BranchName": {
         "Type": "String",
         "Default": "master"
      },
      "GitHubUser": {
         "Type": "String",
         "Default": "user"
      },
      "GitHubToken": {
         "Type": "String",
         "Default": "OAuthToken"
      },
      "TemplateKey": {
         "Type": "String",
         "Default": "test/remote-template.yaml"
      },
      "BucketName": {
         "Type": "String",
         "Default": "example-bucket"
      },
      "Environment": {
         "Type": "String",
         "Default": "dev"
      }
   },
   "Resources": {
      "TemplateGit": {
         "Type": "Template::Git",
         "Properties": {
            "Mode": "Inline",
            "Provider": "Github",
            "Repo": { 
	       	  "Ref" : "RepositoryName" 
	        },
            "Branch": { 
	       	   "Ref" : "BranchName" 
	        },
            "Owner": { 
	       	   "Ref" : "GitHubUser" 
	        },
            "OAuthToken": { 
	       	   "Ref" : "GitHubToken" 
	        },
            "Path": { 
	       	   "Ref" : "TemplateKey" 
	        },
            "Parameters": {
               "Name": "github-example",
               "Environment": { 
	       	      "Ref" : "Environment" 
	            }
            }
         }
      },
      "TemplateS3": {
         "Type": "Template::S3",
         "Properties": {
            "Mode": "Inline",
            "Provider": "S3",
            "Bucket": { 
	       	  "Ref" : "BucketName" 
	        },
            "Key": { 
	       	  "Ref" : "TemplateKey" 
	        },
            "Parameters": {
               "Name": "s3-example",
               "Environment": { 
	       	      "Ref" : "Environment" 
	            }
            }
         }
      }
   }
}
```

#### YAML
```
Transform: [Template]

Description: Example Macro Template.

Parameters:
  RepositoryName:
    Type: String
    Default: template-macro
  BranchName:
    Type: String
    Default: master
  GitHubUser:
    Type: String
    Default: user
  GitHubToken:
    Type: String
    Default: OAuthToken
  TemplateKey:
    Type: String
    Default: test/remote-template.yaml
  BucketName:
    Type: String
    Default: example-bucket
  Environment:
    Type: String
    Default: dev

Resources:
  TemplateGit:
    Type: "Template::Git"
    Properties:
      Mode: Inline
      Provider: Github
      Repo: !Ref RepositoryName
      Branch: !Ref BranchName
      Owner: !Ref GitHubUser
      OAuthToken: !Ref GitHubToken
      Path: !Ref TemplateKey
      Parameters:
        Name: "github-example"
        Environment: !Ref Environment


  TemplateS3:
    Type: "Template::S3"
    Properties:
      Mode: Inline
      Provider: S3
      Bucket: !Ref BucketName
      Key: !Ref TemplateKey
      Parameters:
        Name: 's3-example'
        Environment: !Ref Environment
```




