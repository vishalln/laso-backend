"""Admin Stack — Admin Portal API Gateway, Lambda (uses RDS publicly)."""

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


class AdminStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        user_pool: cognito.UserPool,
        app_client: cognito.UserPoolClient,
        db_secret: secretsmanager.Secret,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deps_layer = _lambda.LayerVersion(
            self, "DepsLayer",
            layer_version_name=f"{LAYER.name}-admin",
            description=LAYER.description,
            code=_lambda.Code.from_asset(LAYER.asset_path),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
        )

        self.admin_lambda = self._create_admin_lambda(
            user_pool, app_client, db_secret, deps_layer,
        )
        self.admin_api = self._create_admin_api()
        self._grant_permissions(user_pool, db_secret)
        self._create_outputs()

    def _create_admin_lambda(
        self,
        user_pool: cognito.UserPool,
        app_client: cognito.UserPoolClient,
        db_secret: secretsmanager.Secret,
        deps_layer: _lambda.ILayerVersion,
    ) -> PythonLambdaConstruct:
        return PythonLambdaConstruct(
            self, "AdminLambda",
            function_name="laso-admin",
            path="src",
            handler="laso.handlers.admin_handler.lambda_handler",
            environment={
                "USER_POOL_ID": user_pool.user_pool_id,
                "APP_CLIENT_ID": app_client.user_pool_client_id,
                "DB_SECRET_ARN": db_secret.secret_arn,
            },
            layers=[deps_layer],
        )

    def _create_admin_api(self) -> apigw.RestApi:
        api = apigw.RestApi(
            self, "AdminApi",
            rest_api_name="laso-admin-api",
            description="LASO Admin Portal API for role management",
            deploy_options=apigw.StageOptions(
                stage_name=API.stage_name,
                throttling_rate_limit=API.throttle_rps,
                throttling_burst_limit=API.throttle_burst,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
                allow_credentials=False,
            ),
        )

        admin_resource = api.root.add_resource("admin")
        users_resource = admin_resource.add_resource("users")
        users_resource.add_method("GET", apigw.LambdaIntegration(self.admin_lambda.function))

        user_email_resource = users_resource.add_resource("{user_email}")
        user_email_resource.add_method("GET", apigw.LambdaIntegration(self.admin_lambda.function))

        role_resource = user_email_resource.add_resource("role")
        role_resource.add_method("PUT", apigw.LambdaIntegration(self.admin_lambda.function))

        return api

    def _grant_permissions(self, user_pool: cognito.UserPool, db_secret: secretsmanager.Secret) -> None:
        user_pool.grant(
            self.admin_lambda.function,
            "cognito-idp:AdminListGroupsForUser",
            "cognito-idp:AdminAddUserToGroup",
            "cognito-idp:AdminRemoveUserFromGroup",
            "cognito-idp:GetUser",
            "cognito-idp:ListUsers",
        )
        db_secret.grant_read(self.admin_lambda.function)

    def _create_outputs(self) -> None:
        CfnOutput(self, "AdminApiUrl",
                  value=self.admin_api.url,
                  export_name="LasoAdminApiUrl",
                  description="Admin Portal API Gateway URL")
        CfnOutput(self, "AdminApiId",
                  value=self.admin_api.rest_api_id,
                  export_name="LasoAdminApiId",
                  description="Admin Portal API Gateway ID")
