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

example-beanstalk:
	aws cloudformation package --template-file example-beanstalk.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateBeanstalk --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output

example-webserver:
	aws cloudformation package --template-file example-webserver.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateWebServer --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output

example-asg:
	aws cloudformation package --template-file example-asg.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateASG --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output

example-dns-asg:
	aws cloudformation package --template-file example-dns-asg.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateDnsASG --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output

example-ec2:
	aws cloudformation package --template-file example-ec2.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateBastionHost --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output

example-nlb:
	aws cloudformation package --template-file example-nlb.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateFrontend --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output

example-db:
	aws cloudformation package --template-file example-db.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name TemplateDatabase --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output

example-3tier:
	aws cloudformation package --template-file example-3tier.yaml --s3-bucket $(BUCKET) --output-template-file example.output  || echo "Continue"
	aws cloudformation deploy --template-file ./example.output --stack-name Template3Tier --region $(REGION) --parameter-overrides Environment=prod --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM || echo "Continue"
	rm -f ./example.output