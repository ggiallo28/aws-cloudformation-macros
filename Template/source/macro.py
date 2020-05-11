import sys, os, io, traceback

sys.path.insert(1, 'libs')
sys.path.insert(1, 'source/libs')
from cfn_flip import flip, to_json

import json
import boto3
import json
import logging

from utils import *
from resources import *
from simulator import *

logging.basicConfig(level=logging.INFO)   

def handle_template(main_template):
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

            if mode.lower() == 'nested':
                stack_template = resource_obj.get_stack_template()
                merge_template.add_resource(stack_template)

                logging.info('Add Template Resource {}, Mode={}'.format(resource_id, mode))

            if mode.lower() == 'inline':
                import_template = TemplateLoader.loads(resource_obj.get_template())
                import_template = import_template.translate(prefix=resource_id)

                import_templates = {**import_templates, **{ resource_id : (resource_obj, import_template) }}

                logging.info('Add Template Resource {}, Mode={}'.format(resource_id, mode))

    merge_template.resolve_attrs(import_templates)

    for key in import_templates:
        top_level_resource, inline_template = import_templates[key]
        inline_template.set_attrs(top_level_resource, import_templates)
        merge_template += inline_template

    print(merge_template.to_yaml())

    if merge_template.is_custom():
        logging.info('Recursive Call.')
        return handle_template(json.loads(merge_template.to_json()))

    return json.loads(merge_template.to_json())

def create_local_path(requestId):
    path = '/tmp/' + requestId
    try:
        os.mkdir(path)
        os.mkdir(path + '/github')
    except OSError:
        logging.warning ('Creation of the directory %s failed' % path)
    else:
        logging.info ('Successfully created the directory %s ' % path)
    return requestId

def handler(event, context):
    logging.debug("Input:", json.dumps(event))

    request_id = create_local_path(event['requestId'])
    parameters = event['templateParameterValues']

    cfn = Simulator(event['fragment'], event['templateParameterValues'])
    template = cfn.simulate(excude_clean=['Parameters'])
    aws_region = event['region']

    macro_response = {
        'fragment': template,
        'status': 'success',
        'requestId': request_id
    } 

    Template.aws_cfn_request_id = request_id
    Template.template_params = parameters
    Template.aws_region = aws_region

    try:
        macro_response['fragment'] = handle_template(template)
        logging.debug("Output:", json.dumps(event))
    except Exception as e:
        traceback.print_exc()
        macro_response['status'] = 'failure'
        macro_response['errorMessage'] = str(e)

    return macro_response

if __name__ == '__main__':
    with open('./source/event.json') as json_file:
        event = json.load(json_file)
    handler(event, None)
    #print(json.dumps(handler(event, None)))
