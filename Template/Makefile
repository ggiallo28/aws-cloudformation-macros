BUCKET=audioposts-site
REGION=us-east-1


macros:
	aws cloudformation package --template-file template.yaml --s3-bucket $(BUCKET) --output-template-file template.output 
	aws cloudformation deploy --template-file ./template.output --stack-name TemplateMacro --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --region $(REGION) || echo "Continue"
	rm -f ./template.output

example:
	aws cloudformation package --template-file example.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateExamplev1 --region $(REGION) || echo "Continue"
	rm -f ./example.output

example-boto3:
	aws cloudformation package --template-file example-boto3.yaml --s3-bucket $(BUCKET) --output-template-file example-boto3.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example-boto3.output --stack-name TemplateExampleBoto3 --region $(REGION) || echo "Continue"
	rm -f ./example-boto3.output