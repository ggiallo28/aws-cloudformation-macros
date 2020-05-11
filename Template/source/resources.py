import sys, os, json, io

sys.path.insert(1, 'libs')
sys.path.insert(1, 'source/libs')
from troposphere.validators import boolean, integer
from troposphere import AWSObject
from troposphere import Tags, Ref, Join
from troposphere import cloudformation
from cfn_flip import to_json
import logging
import boto3
import git

from simulator import *

s3 = boto3.client('s3')
cm = boto3.client('codecommit')

BRANCH_DEFAULT = 'master'
TEMPLATE_NAME_DEFAULT = 'template.yaml'
ASSERT_MESSAGE = 'Template format error: {} value is invalid. The value must not depend on any resources or imported values'

try:
    basestring
except NameError:
    basestring = str


class Template(AWSObject):
    resource_type = 'Template'

    global aws_cfn_request_id
    global template_params
    global aws_region

    def get_value(self, key, default=None):
        value = self.properties.get(key)
        if hasattr(value, 'Ref'):
            value = self.template_params[value['Ref']]
        return default if value in [None, ""] else value

    def s3_import(self):
        logging.info('Import {} from S3.'.format(self.title))

        bucket = self.get_value('Bucket')
        key = self.get_value('Key')

        assert type(bucket) == str, ASSERT_MESSAGE.format('Bucket')
        assert type(key) == str, ASSERT_MESSAGE.format('Key')

        file = '/tmp/' + self.aws_cfn_request_id + '/' + key.replace('/', '_')

        with open(file, 'wb') as f:
            s3.download_fileobj(bucket, key, f)

        with open(file) as f:
            template = json.loads(to_json(f.read()))

        return template

    def codecommit_import(self):
        logging.info('Import {} from Codecommit.'.format(self.title))

        repo = self.get_value('Repo')
        branch = self.get_value('Branch', default=BRANCH_DEFAULT)
        path = self.get_value('Path', default=TEMPLATE_NAME_DEFAULT)

        assert type(repo) == str, ASSERT_MESSAGE.format('Repo')
        assert type(branch) == str, ASSERT_MESSAGE.format('Branch')
        assert type(path) == str, ASSERT_MESSAGE.format('Path')

        response = cm.get_file(repositoryName=repo,
                               commitSpecifier=branch,
                               filePath=path)

        template = json.loads(to_json(response['fileContent']))

        return template

    def github_import(self):
        logging.info('Import {} from Github.'.format(self.title))

        repo = self.get_value('Repo')
        branch = self.get_value('Branch', default=BRANCH_DEFAULT)
        path = self.get_value('Path', default=TEMPLATE_NAME_DEFAULT)

        token = self.get_value('OAuthToken', default='')
        token = token if len(token) == 0 else '{}@'.format(token)

        owner = self.get_value('Owner')
        if owner is None:
            raise Exception(
                'Owner property must be provied when provider is GitHub.')

        assert type(repo) == str, ASSERT_MESSAGE.format('Repo')
        assert type(branch) == str, ASSERT_MESSAGE.format('Branch')
        assert type(path) == str, ASSERT_MESSAGE.format('Path')
        assert type(token) == str, ASSERT_MESSAGE.format('Token')
        assert type(owner) == str, ASSERT_MESSAGE.format('Owner')

        clone_dir = '/tmp/' + self.aws_cfn_request_id + '/github'
        if not os.path.exists(clone_dir + '/' + repo):
            repo_url = 'https://{}github.com/{}/{}.git'.format(
                token, owner, repo)
            git.Git(clone_dir).clone(repo_url)

        file = clone_dir + '/' + repo + '/' + path
        with open(file) as f:
            template = json.loads(to_json(f.read()))

        return template

    def get_template(self):
        switcher = {
            's3': self.s3_import,
            'codecommit': self.codecommit_import,
            'github': self.github_import
        }

        if isinstance(self, Git):
            provider = self.properties["Provider"].lower()

        if isinstance(self, S3):
            provider = 's3'

        template = switcher[provider]()

        cfn = Simulator(template, {
            **self.template_params,
            **self.get_value('Parameters', default={})
        })

        return cfn.simulate()

    def s3_export(self):
        bucket_name = self.get_value('TemplateBucket')
        object_key = self.get_value('TemplateKey',\
            self.get_value('Path',\
                self.get_value('Key')))
        logging.info('Upload {} in {}'.format(object_key, bucket_name))

        if isinstance(bucket_name, Ref):
            bucket_name = self.template_params[bucket_name.data['Ref']]

        if isinstance(object_key, Ref):
            object_key = self.template_params[object_key.data['Ref']]

        if bucket_name is None:
            bucket_name = DEFAULT_BUCKET
            object_key = '{}/{}'.format(self.aws_cfn_request_id, object_key)

        import_template = json.dumps(self.get_template())
        s3.upload_fileobj(io.BytesIO(import_template.encode()), bucket_name,
                          object_key)

        return Join(
            '', ['https://', bucket_name, '.s3.amazonaws.com/', object_key])

    def get_stack_template(self):
        nested_stack = cloudformation.Stack(title=self.title)
        for attr in nested_stack.attributes:
            if hasattr(self, attr):
                setattr(nested_stack, attr, getattr(self, attr))
        for prop in nested_stack.propnames:
            if prop in self.properties:
                setattr(nested_stack, prop, self.properties.get(prop))
        nested_stack.TemplateURL = self.s3_export()

        return nested_stack


class Git(Template):
    resource_type = 'Template::Git'

    props = {
        'Mode': (basestring, True),
        'Provider': (basestring, True),
        'Repo': (basestring, True),
        'Path': (basestring, True),
        'Branch': (basestring, False),
        'Owner': (basestring, False),
        'OAuthToken': (basestring, False),
        'Parameters': (dict, False),
        'NotificationARNs': ([basestring], False),
        'Tags': ((Tags, list), False),
        'TimeoutInMinutes': (integer, False),
        'TemplateBucket': (basestring, False),
        'TemplateKey': (basestring, False)
    }


class S3(Template):
    resource_type = 'Template::S3'

    props = {
        'Mode': (basestring, True),
        'Bucket': (basestring, True),
        'Key': (basestring, True),
        'Parameters': (dict, False),
        'NotificationARNs': ([basestring], False),
        'Tags': ((Tags, list), False),
        'TimeoutInMinutes': (integer, False),
        'TemplateBucket': (basestring, False)
    }
