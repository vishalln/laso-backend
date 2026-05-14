"""Backend Stack — Quiz + Hello Lambdas, API Gateway (uses RDS publicly)."""

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
)
from lib.app_constructs.lambda_construct import PythonLambdaConstruct
from lib.config.backend_config import API
from lib.config.data_config import LAYER


class BackendStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        db_secret: secretsmanager.Secret,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deps_layer = _lambda.LayerVersion(
            self, "DepsLayer",
            layer_version_name=f"{LAYER.name}-backend",
            description=LAYER.description,
            code=_lambda.Code.from_asset(LAYER.asset_path),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
        )

        db_env = {"DB_SECRET_ARN": db_secret.secret_arn}

        hello_lambda = PythonLambdaConstruct(
            self, "HelloLambda",
            function_name="laso-hello",
            path="src",
            handler="laso.handlers.hello_handler.lambda_handler",
        )

        quiz_lambda = PythonLambdaConstruct(
            self, "QuizLambda",
            function_name="laso-quiz",
            path="src",
            handler="laso.handlers.quiz_handler.lambda_handler",
            environment=db_env,
            layers=[deps_layer],
        )
        db_secret.grant_read(quiz_lambda.function)

        api = apigw.RestApi(
            self, "LasoApi",
            rest_api_name="laso-api",
            deploy_options=apigw.StageOptions(
                stage_name=API.stage_name,
                throttling_rate_limit=API.throttle_rps,
                throttling_burst_limit=API.throttle_burst,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
            ),
        )

        api.root.add_method("GET", apigw.LambdaIntegration(hello_lambda.function))

        quiz_r = api.root.add_resource("quiz")
        submit_r = quiz_r.add_resource("submit")
        submit_r.add_method("POST", apigw.LambdaIntegration(quiz_lambda.function))
