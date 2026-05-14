"""Auth Stack — Cognito User Pool, Groups, App Client, OAuth, Post-Confirmation Trigger."""

from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

from lib.app_constructs.lambda_construct import PythonLambdaConstruct
from lib.config.auth_config import USER_POOL, USER_GROUPS, OAUTH
from lib.config.data_config import LAYER
from src.laso.constants.oauth import OAuthProvider


class AuthStack(Stack):
    user_pool: cognito.UserPool
    app_client: cognito.UserPoolClient

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        db_secret: secretsmanager.Secret,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = self._create_user_pool()
        self.user_pool_domain = self._create_user_pool_domain()
        self.user_groups = self._create_user_groups()
        self.google_secret = self._get_google_secret()
        self.google_provider = self._create_google_provider()
        self.app_client = self._create_app_client()
        self._create_post_confirmation_trigger(db_secret)
        self._create_outputs()

    def _create_user_pool(self) -> cognito.UserPool:
        return cognito.UserPool(
            self, "LasoUserPool",
            user_pool_name=USER_POOL.pool_name,
            self_sign_up_enabled=USER_POOL.self_sign_up_enabled,
            sign_in_aliases=cognito.SignInAliases(email=True, username=False, phone=False),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=USER_POOL.min_password_length,
                require_lowercase=USER_POOL.require_lowercase,
                require_uppercase=USER_POOL.require_uppercase,
                require_digits=USER_POOL.require_digits,
                require_symbols=USER_POOL.require_symbols,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN,
        )

    def _create_user_pool_domain(self) -> cognito.UserPoolDomain:
        return self.user_pool.add_domain(
            "LasoUserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=OAUTH.domain_prefix),
        )

    def _get_google_secret(self) -> secretsmanager.ISecret:
        return secretsmanager.Secret(
            self, "GoogleClientSecret",
            secret_name=OAUTH.secret_name,
            description="Google OAuth Client Secret for Cognito",
            removal_policy=RemovalPolicy.RETAIN,
        )

    def _create_google_provider(self) -> cognito.UserPoolIdentityProviderGoogle:
        return cognito.UserPoolIdentityProviderGoogle(
            self, "GoogleProvider",
            user_pool=self.user_pool,
            client_id=OAUTH.google_client_id,
            client_secret_value=self.google_secret.secret_value,
            scopes=OAUTH.google_scopes,
            attribute_mapping=cognito.AttributeMapping(
                email=cognito.ProviderAttribute.GOOGLE_EMAIL,
                given_name=cognito.ProviderAttribute.GOOGLE_GIVEN_NAME,
                family_name=cognito.ProviderAttribute.GOOGLE_FAMILY_NAME,
                profile_picture=cognito.ProviderAttribute.GOOGLE_PICTURE,
            ),
        )

    def _create_user_groups(self) -> dict:
        groups = {}
        for group_key, group_config in [
            ("patient", USER_GROUPS.PATIENT),
            ("doctor", USER_GROUPS.DOCTOR),
            ("coordinator", USER_GROUPS.COORDINATOR),
            ("admin", USER_GROUPS.ADMIN),
        ]:
            groups[group_key] = cognito.CfnUserPoolGroup(
                self, f"{group_config.name}Group",
                user_pool_id=self.user_pool.user_pool_id,
                group_name=group_config.name,
                description=group_config.description,
                precedence=group_config.precedence,
            )
        return groups

    def _create_app_client(self) -> cognito.UserPoolClient:
        app_client = self.user_pool.add_client(
            "LasoWebAppClient",
            user_pool_client_name="laso-web-app-client",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL, cognito.OAuthScope.PROFILE],
                callback_urls=OAUTH.callback_urls,
                logout_urls=OAUTH.logout_urls,
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.GOOGLE,
                cognito.UserPoolClientIdentityProvider.COGNITO,
            ],
            access_token_validity=Duration.hours(USER_POOL.access_token_validity_hours),
            id_token_validity=Duration.hours(USER_POOL.id_token_validity_hours),
            refresh_token_validity=Duration.days(USER_POOL.refresh_token_validity_days),
            prevent_user_existence_errors=True,
        )
        app_client.node.add_dependency(self.google_provider)
        return app_client

    def _create_post_confirmation_trigger(self, db_secret: secretsmanager.Secret) -> None:
        deps_layer = _lambda.LayerVersion(
            self, "PostConfirmDepsLayer",
            layer_version_name=f"{LAYER.name}-post-confirm",
            description=LAYER.description,
            code=_lambda.Code.from_asset(LAYER.asset_path),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
        )

        trigger_fn = PythonLambdaConstruct(
            self, "PostConfirmationTrigger",
            function_name="laso-post-confirmation",
            path="src",
            handler="laso.handlers.post_confirmation_handler.lambda_handler",
            environment={"DB_SECRET_ARN": db_secret.secret_arn},
            layers=[deps_layer],
        )
        db_secret.grant_read(trigger_fn.function)

        self.user_pool.add_trigger(
            cognito.UserPoolOperation.POST_CONFIRMATION,
            trigger_fn.function,
        )

    def _create_outputs(self) -> None:
        CfnOutput(self, "UserPoolId",
                  value=self.user_pool.user_pool_id,
                  export_name="LasoUserPoolId",
                  description="Cognito User Pool ID")

        CfnOutput(self, "UserPoolClientId",
                  value=self.app_client.user_pool_client_id,
                  export_name="LasoUserPoolClientId",
                  description="Cognito User Pool Client ID")

        domain_url = f"https://{OAUTH.domain_prefix}.auth.{self.region}.amazoncognito.com"

        CfnOutput(self, "CognitoDomainUrl",
                  value=domain_url,
                  export_name="LasoCognitoDomainUrl",
                  description="Cognito Hosted UI Domain URL")

        oauth_login_url = (
            f"{domain_url}/oauth2/authorize"
            f"?client_id={self.app_client.user_pool_client_id}"
            f"&response_type=code"
            f"&scope=openid+email+profile"
            f"&redirect_uri={OAUTH.callback_urls[0]}"
            f"&identity_provider={OAuthProvider.GOOGLE.value}"
        )

        CfnOutput(self, "GoogleOAuthUrl",
                  value=oauth_login_url,
                  export_name="LasoGoogleOAuthUrl",
                  description="Google OAuth Login URL")
