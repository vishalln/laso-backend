"""Cron Stack — EventBridge scheduled Lambda functions."""

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
)
from lib.app_constructs.lambda_construct import PythonLambdaConstruct
from lib.config.backend_config import CRON
from lib.config.data_config import LAYER


CRON_LAMBDAS = [
    ("MissedCheckinCron", "laso-cron-missed-checkin", "cron.missed_checkin_handler", CRON.missed_checkin_schedule),
    ("TaskArchiverCron", "laso-cron-task-archiver", "cron.task_archiver_handler", CRON.task_archiver_schedule),
    ("ConsultStatusCron", "laso-cron-consult-status", "cron.consult_status_handler", CRON.consult_status_schedule),
]


class CronStack(Stack):
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
            layer_version_name=f"{LAYER.name}-cron",
            description=LAYER.description,
            code=_lambda.Code.from_asset(LAYER.asset_path),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
        )

        db_env = {"DB_SECRET_ARN": db_secret.secret_arn}

        for construct_id_name, fn_name, handler_module, schedule_expr in CRON_LAMBDAS:
            fn = PythonLambdaConstruct(
                self, construct_id_name,
                function_name=fn_name,
                path="src",
                handler=f"laso.handlers.{handler_module}.lambda_handler",
                environment=db_env,
                layers=[deps_layer],
            )
            db_secret.grant_read(fn.function)

            schedule = (
                events.Schedule.expression(schedule_expr)
                if schedule_expr.startswith("rate(")
                else events.Schedule.expression(f"cron({schedule_expr})")
            )

            events.Rule(
                self, f"{construct_id_name}Rule",
                schedule=schedule,
                targets=[targets.LambdaFunction(fn.function)],
            )
