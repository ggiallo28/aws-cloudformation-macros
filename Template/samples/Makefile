BUCKET=audioposts-site
REGION=us-east-1

example-lambda:
	aws cloudformation package --template-file example-lambda.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateLambda --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output

example-vpc:
	aws cloudformation package --template-file example-vpc.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateVPC --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output