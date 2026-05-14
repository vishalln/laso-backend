"""Generic Cognito operations — authenticate, groups, user management."""

import logging
from typing import Dict, List, Optional
import boto3

from laso.enums import AuthFlow
from laso.constants.auth import COGNITO_ATTR

log = logging.getLogger(__name__)


class CognitoClient:
    def __init__(self, user_pool_id: str, client_id: str) -> None:
        log.info("CognitoClient init", extra={
            "user_pool_id": user_pool_id,
            "client_id": client_id
        })
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.client = boto3.client("cognito-idp")
    
    def authenticate(self, email: str, password: str) -> Dict:
        log.info("authenticate", extra={"email": email})
        response = self.client.initiate_auth(
            ClientId=self.client_id,
            AuthFlow=AuthFlow.USER_PASSWORD_AUTH.value,
            AuthParameters={"USERNAME": email, "PASSWORD": password}
        )
        log.info("authenticate | success", extra={"email": email})
        return response
    
    def get_user(self, access_token: str) -> Dict:
        log.info("get_user | fetching")
        response = self.client.get_user(AccessToken=access_token)
        log.info("get_user | success", extra={
            "username": response.get("Username")
        })
        return response
    
    def get_user_groups(self, email: str) -> List[str]:
        log.info("get_user_groups", extra={"email": email})
        response = self.client.admin_list_groups_for_user(
            Username=email,
            UserPoolId=self.user_pool_id
        )
        groups = [g["GroupName"] for g in response.get("Groups", [])]
        log.info("get_user_groups | success", extra={
            "email": email,
            "groups": groups
        })
        return groups
    
    def add_user_to_group(self, email: str, group: str) -> None:
        log.info("add_user_to_group", extra={"email": email, "group": group})
        self.client.admin_add_user_to_group(
            UserPoolId=self.user_pool_id,
            Username=email,
            GroupName=group
        )
        log.info("add_user_to_group | success", extra={
            "email": email,
            "group": group
        })
    
    def remove_user_from_group(self, email: str, group: str) -> None:
        log.info("remove_user_from_group", extra={"email": email, "group": group})
        self.client.admin_remove_user_from_group(
            UserPoolId=self.user_pool_id,
            Username=email,
            GroupName=group
        )
        log.info("remove_user_from_group | success", extra={
            "email": email,
            "group": group
        })
    
    def sign_up(self, email: str, password: str, name: str) -> Dict:
        log.info("sign_up", extra={"email": email, "name": name})
        response = self.client.sign_up(
            ClientId=self.client_id,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": COGNITO_ATTR.EMAIL, "Value": email},
                {"Name": COGNITO_ATTR.NAME, "Value": name}
            ]
        )
        log.info("sign_up | success", extra={
            "email": email,
            "user_sub": response.get("UserSub")
        })
        return response
    
    def confirm_sign_up(self, email: str) -> None:
        log.info("confirm_sign_up", extra={"email": email})
        self.client.admin_confirm_sign_up(
            UserPoolId=self.user_pool_id,
            Username=email
        )
        log.info("confirm_sign_up | success", extra={"email": email})
    
    def refresh_token(self, refresh_token: str) -> Dict:
        log.info("refresh_token | refreshing")
        response = self.client.initiate_auth(
            ClientId=self.client_id,
            AuthFlow=AuthFlow.REFRESH_TOKEN_AUTH.value,
            AuthParameters={"REFRESH_TOKEN": refresh_token}
        )
        log.info("refresh_token | success")
        return response
    
    def list_users(self, limit: int = 60, pagination_token: Optional[str] = None) -> Dict:
        log.info("list_users", extra={"limit": limit})
        params = {"UserPoolId": self.user_pool_id, "Limit": limit}
        if pagination_token:
            params["PaginationToken"] = pagination_token

        response = self.client.list_users(**params)
        log.info("list_users | success", extra={
            "count": len(response.get("Users", []))
        })
        return response

    def admin_create_user(self, email: str, name: str, group: str, suppress_invite: bool = True) -> str:
        log.info("admin_create_user | email=%s group=%s", email, group)
        response = self.client.admin_create_user(
            UserPoolId=self.user_pool_id,
            Username=email,
            UserAttributes=[
                {"Name": COGNITO_ATTR.EMAIL, "Value": email},
                {"Name": COGNITO_ATTR.EMAIL_VERIFIED, "Value": "true"},
                {"Name": COGNITO_ATTR.NAME, "Value": name},
            ],
            MessageAction="SUPPRESS" if suppress_invite else "RESEND",
        )
        user_sub = next(
            (a["Value"] for a in response["User"]["Attributes"] if a["Name"] == "sub"), ""
        )
        self.add_user_to_group(email, group)
        log.info("admin_create_user | success | sub=%s email=%s group=%s", user_sub, email, group)
        return user_sub

    def admin_set_password(self, email: str, password: str, permanent: bool = True) -> None:
        log.info("admin_set_password | email=%s", email)
        self.client.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=email,
            Password=password,
            Permanent=permanent,
        )
        log.info("admin_set_password | success | email=%s", email)

    def delete_user(self, email: str) -> None:
        log.info("delete_user", extra={"email": email})
        self.client.admin_delete_user(
            UserPoolId=self.user_pool_id,
            Username=email
        )
        log.info("delete_user | success", extra={"email": email})
