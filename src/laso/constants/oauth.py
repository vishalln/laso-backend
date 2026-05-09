from enum import Enum


class OAuthProvider(str, Enum):
    GOOGLE = "Google"
    COGNITO = "COGNITO"


class OAuthConfig:
    GOOGLE_CLIENT_ID = "250183308675-pb2hjuj62q0j0ceuruk87m2o9u3judle.apps.googleusercontent.com"
    GOOGLE_SCOPES = ["openid", "email", "profile"]
    COGNITO_DOMAIN_PREFIX = "laso-health"
    OAUTH_FLOWS = ["code"]
    OAUTH_SCOPES = ["openid", "email", "profile"]
    
    CALLBACK_URLS = {
        "dev": "http://localhost:5173/auth/callback",
        "prod": "https://laso-health.com/auth/callback",
    }
    
    LOGOUT_URLS = {
        "dev": "http://localhost:5173/login",
        "prod": "https://laso-health.com/login",
    }
    
    ATTRIBUTE_MAPPING = {
        "email": "email",
        "given_name": "given_name",
        "family_name": "family_name",
        "picture": "picture",
    }
    
    SECRET_NAME = "laso/google-oauth-client-secret"


class OAuthEndpoints:
    TOKEN_PATH = "/oauth2/token"
    AUTHORIZE_PATH = "/oauth2/authorize"
    LOGOUT_PATH = "/logout"
    IDP_RESPONSE_PATH = "/oauth2/idpresponse"
    
    @staticmethod
    def get_redirect_uri(region: str, domain_prefix: str) -> str:
        return f"https://{domain_prefix}.auth.{region}.amazoncognito.com{OAuthEndpoints.IDP_RESPONSE_PATH}"
