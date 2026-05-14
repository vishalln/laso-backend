"""Admin handler — role management operations."""

import json
import logging
import os
from typing import Dict, Any
from uuid import uuid4
from botocore.exceptions import ClientError

from laso.utils.cognito import CognitoClient
from laso.models.auth import User, RoleChangeAudit
from laso.enums import UserRole, HttpStatus, CognitoErrorCode
from laso.constants.auth import AUTH_ERRORS, ENV, HEADER, HEADER_VALUE, COGNITO_ATTR

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

cognito_client = CognitoClient(
    user_pool_id=os.environ[ENV.USER_POOL_ID],
    client_id=os.environ[ENV.APP_CLIENT_ID],
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    log.info("admin_handler | event=%s", event)

    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{http_method} {resource}"
    log.info("admin_handler | route=%s", route)

    route_map = {
        "PUT /admin/users/{user_email}/role": update_user_role,
        "PUT /admin/users/{user_email}/status": toggle_user_status,
        "DELETE /admin/users/{user_email}/purge": purge_user,
        "GET /admin/users": list_all_users,
        "GET /admin/users/{user_email}": get_user_details,
    }

    handler = route_map.get(route)
    if handler:
        return handler(event)

    log.warning("admin_handler | unknown_route=%s", route)
    return response(HttpStatus.NOT_FOUND, {"error": "Route not found"})


def update_user_role(event: Dict[str, Any]) -> Dict[str, Any]:
    log.info("update_user_role | start")

    try:
        admin_user = extract_user_from_token(event)
        log.info("update_user_role | admin=%s", admin_user.to_dict())

        if admin_user.role != UserRole.ADMIN:
            log.warning("update_user_role | unauthorized | email=%s role=%s",
                        admin_user.email, admin_user.role.value)
            return response(HttpStatus.FORBIDDEN, {"error": AUTH_ERRORS.ERROR_ADMIN_ONLY})

        target_email = event["pathParameters"]["user_email"]
        body = json.loads(event["body"])
        new_role_str = body.get("role", "").lower()
        log.info("update_user_role | target=%s new_role=%s", target_email, new_role_str)

        if not UserRole.is_valid(new_role_str):
            return response(HttpStatus.BAD_REQUEST, {"error": AUTH_ERRORS.ERROR_INVALID_ROLE})

        new_role = UserRole(new_role_str)
        current_groups = cognito_client.get_user_groups(target_email)
        previous_role = UserRole.from_group_name(current_groups[0]) if current_groups else UserRole.PATIENT
        log.info("update_user_role | previous_role=%s", previous_role.value)

        if previous_role == new_role:
            return response(HttpStatus.OK, {
                "message": "User already has this role",
                "user_email": target_email,
                "role": new_role.value,
            })

        for group in current_groups:
            cognito_client.remove_user_from_group(target_email, group)
        cognito_client.add_user_to_group(target_email, new_role.group_name)

        audit = RoleChangeAudit(
            audit_id=str(uuid4()),
            target_user_email=target_email,
            previous_role=previous_role.value,
            new_role=new_role.value,
            changed_by_admin_email=admin_user.email,
            changed_by_admin_id=admin_user.id,
        )
        audit.save()

        log.info("update_user_role | success | target=%s %s→%s audit_id=%s",
                 target_email, previous_role.value, new_role.value, audit.audit_id)

        return response(HttpStatus.OK, {
            "message": AUTH_ERRORS.SUCCESS_ROLE_UPDATED,
            "user_email": target_email,
            "previous_role": previous_role.value,
            "new_role": new_role.value,
            "changed_by": admin_user.email,
            "audit_id": audit.audit_id,
        })

    except KeyError as e:
        log.error("update_user_role | missing_field=%s", e)
        return response(HttpStatus.BAD_REQUEST, {"error": f"Missing required field: {str(e)}"})
    except ClientError as e:
        log.error("update_user_role | cognito_error=%s", e)
        error_code = e.response["Error"]["Code"]
        if error_code == CognitoErrorCode.USER_NOT_FOUND.value:
            return response(HttpStatus.NOT_FOUND, {"error": AUTH_ERRORS.ERROR_USER_NOT_FOUND})
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": AUTH_ERRORS.ERROR_ROLE_UPDATE_FAILED})
    except Exception as e:
        log.error("update_user_role | error=%s", e, exc_info=True)
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": AUTH_ERRORS.ERROR_ROLE_UPDATE_FAILED})


def list_all_users(event: Dict[str, Any]) -> Dict[str, Any]:
    log.info("list_all_users | start")

    try:
        admin_user = extract_user_from_token(event)
        if admin_user.role != UserRole.ADMIN:
            return response(HttpStatus.FORBIDDEN, {"error": AUTH_ERRORS.ERROR_ADMIN_ONLY})

        pagination_token = (event.get("queryStringParameters") or {}).get("next_token")
        log.info("list_all_users | pagination_token=%s", pagination_token)

        result = cognito_client.list_users(limit=60, pagination_token=pagination_token)

        users = []
        for cognito_user in result.get("Users", []):
            attributes = {attr["Name"]: attr["Value"] for attr in cognito_user.get("Attributes", [])}
            email = attributes.get(COGNITO_ATTR.EMAIL, "")
            groups = cognito_client.get_user_groups(email) if email else []
            role = UserRole.from_group_name(groups[0]) if groups else UserRole.PATIENT

            users.append({
                "id": attributes.get(COGNITO_ATTR.SUB),
                "email": email,
                "name": attributes.get(COGNITO_ATTR.NAME),
                "role": role.value,
                "created_at": cognito_user.get("UserCreateDate").isoformat() if cognito_user.get("UserCreateDate") else None,
                "status": cognito_user.get("UserStatus"),
            })

        log.info("list_all_users | count=%d", len(users))

        return response(HttpStatus.OK, {
            "users": users,
            "next_token": result.get("PaginationToken"),
            "count": len(users),
        })

    except Exception as e:
        log.error("list_all_users | error=%s", e, exc_info=True)
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Failed to list users"})


def get_user_details(event: Dict[str, Any]) -> Dict[str, Any]:
    log.info("get_user_details | start")

    try:
        admin_user = extract_user_from_token(event)
        if admin_user.role != UserRole.ADMIN:
            return response(HttpStatus.FORBIDDEN, {"error": AUTH_ERRORS.ERROR_ADMIN_ONLY})

        target_email = event["pathParameters"]["user_email"]
        log.info("get_user_details | target=%s", target_email)

        groups = cognito_client.get_user_groups(target_email)
        role = UserRole.from_group_name(groups[0]) if groups else UserRole.PATIENT

        return response(HttpStatus.OK, {"email": target_email, "role": role.value, "groups": groups})

    except ClientError as e:
        log.error("get_user_details | cognito_error=%s", e)
        if e.response["Error"]["Code"] == CognitoErrorCode.USER_NOT_FOUND.value:
            return response(HttpStatus.NOT_FOUND, {"error": AUTH_ERRORS.ERROR_USER_NOT_FOUND})
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Failed to get user details"})
    except Exception as e:
        log.error("get_user_details | error=%s", e, exc_info=True)
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Failed to get user details"})


def toggle_user_status(event: Dict[str, Any]) -> Dict[str, Any]:
    log.info("toggle_user_status | start")

    try:
        admin_user = extract_user_from_token(event)
        if admin_user.role != UserRole.ADMIN:
            return response(HttpStatus.FORBIDDEN, {"error": AUTH_ERRORS.ERROR_ADMIN_ONLY})

        target_email = event["pathParameters"]["user_email"]
        body = json.loads(event["body"])
        status = body.get("status", "").lower()
        log.info("toggle_user_status | target=%s status=%s", target_email, status)

        from laso.services import admin_user_service
        result = admin_user_service.toggle_status(email=target_email, status=status)

        return response(HttpStatus.OK, result)

    except KeyError as e:
        log.error("toggle_user_status | missing_field=%s", e)
        return response(HttpStatus.BAD_REQUEST, {"error": f"Missing required field: {str(e)}"})
    except ClientError as e:
        log.error("toggle_user_status | cognito_error=%s", e)
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Failed to toggle user status"})
    except Exception as e:
        log.error("toggle_user_status | error=%s", e, exc_info=True)
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Failed to toggle user status"})


def purge_user(event: Dict[str, Any]) -> Dict[str, Any]:
    log.info("purge_user | start")

    try:
        admin_user = extract_user_from_token(event)
        if admin_user.role != UserRole.ADMIN:
            return response(HttpStatus.FORBIDDEN, {"error": AUTH_ERRORS.ERROR_ADMIN_ONLY})

        target_email = event["pathParameters"]["user_email"]
        log.info("purge_user | target=%s admin=%s", target_email, admin_user.email)

        from laso.services import admin_user_service
        result = admin_user_service.purge(email=target_email, cognito_client=cognito_client)

        log.info("purge_user | success | target=%s deleted=%s", target_email, result)
        return response(HttpStatus.OK, {"message": "User purged", "email": target_email, "deleted": result})

    except ClientError as e:
        log.error("purge_user | cognito_error=%s", e)
        error_code = e.response["Error"]["Code"]
        if error_code == CognitoErrorCode.USER_NOT_FOUND.value:
            return response(HttpStatus.NOT_FOUND, {"error": AUTH_ERRORS.ERROR_USER_NOT_FOUND})
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Failed to purge user"})
    except Exception as e:
        log.error("purge_user | error=%s", e, exc_info=True)
        return response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Failed to purge user"})


def extract_user_from_token(event: Dict[str, Any]) -> User:
    headers = event.get("headers", {})
    auth_header = headers.get(HEADER.AUTHORIZATION.lower(), headers.get(HEADER.AUTHORIZATION, ""))
    access_token = auth_header.replace("Bearer ", "").replace("bearer ", "")

    if not access_token:
        raise ValueError(AUTH_ERRORS.ERROR_NO_TOKEN)

    user_info = cognito_client.get_user(access_token)
    log.info("extract_user_from_token | username=%s", user_info.get("Username"))

    attributes = {attr["Name"]: attr["Value"] for attr in user_info.get("UserAttributes", [])}
    email = attributes.get(COGNITO_ATTR.EMAIL, "")
    groups = cognito_client.get_user_groups(email)

    return User.from_cognito(user_info, groups)


def response(status_code: HttpStatus, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code.value,
        "headers": {
            HEADER.CONTENT_TYPE: HEADER_VALUE.JSON,
            HEADER.ACCESS_CONTROL_ALLOW_ORIGIN: HEADER_VALUE.CORS_ORIGIN,
            HEADER.ACCESS_CONTROL_ALLOW_HEADERS: HEADER_VALUE.CORS_HEADERS,
            HEADER.ACCESS_CONTROL_ALLOW_METHODS: HEADER_VALUE.CORS_METHODS,
        },
        "body": json.dumps(body),
    }
