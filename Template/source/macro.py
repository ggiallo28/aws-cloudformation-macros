import sys, os, io, traceback

sys.path.insert(1, 'libs')
sys.path.insert(1, 'source/libs')
from cfn_flip import flip, to_json
from troposphere import cloudformation, Join, Ref

import json
import boto3
import json
import logging

from utils import *
from resources import *
from simulator import *

DEFAULT_BUCKET = os.environ.get('DEFAULT_BUCKET', 'macro-template-default-831650818513-us-east-1')
logging.basicConfig(level=logging.INFO)   

def handle_template(request_id, main_template, template_params, aws_region):
    main_template = TemplateLoader.loads(main_template)
    
    merge_template = TemplateLoader.init()
    merge_template.parameters = main_template.parameters
    merge_template.set_version()

    import_templates = {}

    for resource_id, resource_obj in main_template.resources.items():
      if not isinstance(resource_obj, Template):
        merge_template.add_resource(resource_obj)
        logging.info('Add AWS Resource {}'.format(resource_id))

      else:
        mode = resource_obj.properties.get('Mode', 'Inline')
        import_template = get_template(request_id, resource_id, resource_obj, template_params, aws_region)
        import_template = TemplateLoader.loads(import_template)

        if mode.lower() == 'nested':
          stack_template = get_stack_template(request_id, resource_obj, resource_id, template_params, import_template)
          merge_template.add_resource(stack_template)
          logging.info('Add Template Resource {}, Mode={}'.format(resource_id, mode))
        if mode.lower() == 'inline':
          import_template = import_template.translate(prefix=resource_id)
          import_templates = {**import_templates, **{ resource_id : (resource_obj, import_template) }}
          logging.info('Add Template Resource {}, Mode={}'.format(resource_id, mode))


    merge_template.resolve_attrs(import_templates)

    for key in import_templates:
        top_level_resource, inline_template = import_templates[key]
        inline_template.set_attrs(top_level_resource, import_templates)
        merge_template += inline_template

    if any([isinstance(res, S3) or isinstance(res, Git) for res in merge_template.resources.values()]):
        logging.info('Recursive Call.')
        return handle_template(request_id, json.loads(merge_template.to_json()), template_params, aws_region)
    return json.loads(merge_template.to_json())

def handler(event, context):
    logging.info(json.dumps(event))

    cfn = Simulator(event['fragment'], event['templateParameterValues'])
    template = cfn.simulate(excude_clean=['Parameters'])

    macro_response = {
        'fragment': template,
        'status': 'success',
        'requestId': event['requestId']
    }    

    path = '/tmp/' + event['requestId']

    try:
        os.mkdir(path)
        os.mkdir(path + '/github')
    except OSError:
        logging.warning ('Creation of the directory %s failed' % path)
    else:
        logging.info ('Successfully created the directory %s ' % path)

    try:
        macro_response['fragment'] = handle_template(event['requestId'], template, event['templateParameterValues'], event['region'])
        logging.debug(json.dumps(macro_response['fragment']))
    except Exception as e:
        traceback.print_exc()
        macro_response['status'] = 'failure'
        macro_response['errorMessage'] = str(e)

    return macro_response

if __name__ == '__main__':
  with open('./source/event.json') as json_file:
    event = json.load(json_file)
  print(json.dumps(handler(event, None)))
