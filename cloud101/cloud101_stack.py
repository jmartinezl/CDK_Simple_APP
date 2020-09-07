from aws_cdk import core
from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as _s3,
    core,
)
import datetime
import os
import subprocess
import json


class Cloud101Stack(core.Stack):

    project_name = "Cloud101_" 

    def create_dependencies_layer(self, project_name, function_name: str) -> _lambda.LayerVersion:
        requirements_file = "lambda_dependencies/" + function_name + ".txt"
        output_dir = ".lambda_dependencies/" + function_name

        # Install requirements for layer in the output_dir
        if not os.environ.get("SKIP_PIP"):
            # Note: Pip will create the output dir if it does not exist
            subprocess.check_call(
                f"pip install -r {requirements_file} -t {output_dir}/python".split()
            )
        return _lambda.LayerVersion(
            self,
            self.project_name + "-" + function_name + "-dependencies",
            code=_lambda.Code.from_asset(output_dir)
        )

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here

        # create s3 bucket
        bucket = _s3.Bucket(self, self.project_name+"s3bucket")
        
        test_lambda = _lambda.Function(
            self, 'TestHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='test.handler',
        )

        test_date_lambda = _lambda.Function(
            self, 'TestdateHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='testdate.handler',
            layers=[self.create_dependencies_layer(self.project_name, "testdate")]
        )

        now = datetime.datetime.now()
        iso_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        version = test_lambda.add_version(iso_time)

        alias = _lambda.Alias(self, "TestHandlerAlias",
                              alias_name="dev", version=version)

        api = apigw.RestApi(self, self.project_name+"test_api",
                            default_cors_preflight_options={
                                "allow_origins": apigw.Cors.ALL_ORIGINS,
                                "allow_methods": apigw.Cors.ALL_METHODS
                            },
                            #deploy=False
                            )

        api.root.add_resource("hello").add_method(
            "GET", apigw.LambdaIntegration(alias))
        api.root.add_resource("date").add_method(
            "GET", apigw.LambdaIntegration(test_date_lambda))

        with open('resources/api_stack.json', 'r') as myfile:
            data = myfile.read()
        # parse file
        api_stack = json.loads(data)

        for item in api_stack:
            current_resource = api.root
            for _resource in item['path'].split(os.sep):
                if current_resource.get_resource(_resource):
                    current_resource = current_resource.get_resource(_resource)
                else:
                    current_resource = current_resource.add_resource(_resource)

            _api_lambda = _lambda.Function(
                self, item['lambda'],
                runtime=_lambda.Runtime.PYTHON_3_7,
                code=_lambda.Code.asset("lambda/"+item['lambda']+'.zip'),
                handler='main.handler',
            )

            bucket.grant_read_write(_api_lambda)

            _version = _api_lambda.add_version(
                datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))

            _alias = _lambda.Alias(self, item['lambda']+"Alias",
                                   alias_name="dev", version=_version)

            _api_lambda.add_environment("BUCKET_NAME", bucket.bucket_name)

            current_resource.add_method(
                item['method'], apigw.LambdaIntegration(_alias))

        #deployment = apigw.Deployment(self, "development", api=api)
        #stage = apigw.Stage(self, "DEV", deployment=deployment)
