"""API Stack — Single API Gateway with proxy Lambda (catches all routes)."""

from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
)
from lib.app_constructs.lambda_construct import PythonLambdaConstruct
from lib.config.backend_config import API
from lib.config.data_config import LAYER


class ApiStack(Stack):
    """Single Lambda behind API Gateway proxy integration — all 90 routes."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        db_secret: secretsmanager.Secret,
        user_pool: cognito.UserPool,
        app_client: cognito.UserPoolClient,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deps_layer = _lambda.LayerVersion(
            self, "DepsLayer",
            layer_version_name=f"{LAYER.name}-api",
            description=LAYER.description,
            code=_lambda.Code.from_asset(LAYER.asset_path),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
        )

        fn = PythonLambdaConstruct(
            self, "ApiLambda",
            function_name="laso-api-router",
            path="src",
            handler="laso.handlers.router.lambda_handler",
            environment={
                "DB_SECRET_ARN": db_secret.secret_arn,
                "USER_POOL_ID": user_pool.user_pool_id,
                "APP_CLIENT_ID": app_client.user_pool_client_id,
            },
            layers=[deps_layer],
        )
        db_secret.grant_read(fn.function)
        user_pool.grant(
            fn.function,
            "cognito-idp:AdminGetUser",
            "cognito-idp:AdminListGroupsForUser",
            "cognito-idp:AdminAddUserToGroup",
            "cognito-idp:AdminRemoveUserFromGroup",
            "cognito-idp:AdminDisableUser",
            "cognito-idp:AdminEnableUser",
            "cognito-idp:AdminCreateUser",
            "cognito-idp:AdminSetUserPassword",
            "cognito-idp:GetUser",
            "cognito-idp:ListUsers",
        )

        api = apigw.LambdaRestApi(
            self, "LasoApi",
            rest_api_name="laso-api",
            handler=fn.function,
            proxy=True,
            deploy_options=apigw.StageOptions(
                stage_name=API.stage_name,
                throttling_rate_limit=API.throttle_rps,
                throttling_burst_limit=API.throttle_burst,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
            ),
        )

        CfnOutput(self, "ApiUrl",
                  value=api.url,
                  export_name="LasoApiUrl",
                  description="LASO API Gateway URL")
