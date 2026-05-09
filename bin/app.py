#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aws_cdk as cdk
from lib.stacks.vpc_stack import VpcStack
from lib.stacks.data_stack import DataStack
from lib.stacks.auth_stack import AuthStack
from lib.stacks.backend_stack import BackendStack
from lib.stacks.admin_stack import AdminStack

app = cdk.App()

env = cdk.Environment(account="186911868306", region="ap-south-1")

vpc_stack = VpcStack(app, "LasoVpcStack", env=env)

data_stack = DataStack(
    app, "LasoDataStack",
    vpc=vpc_stack.vpc,
    lambda_sg=vpc_stack.lambda_sg,
    env=env,
)
data_stack.add_dependency(vpc_stack)

auth_stack = AuthStack(app, "LasoAuthStack", env=env)

backend_stack = BackendStack(
    app, "LasoBackendStack",
    db_secret=data_stack.db_secret,
    env=env,
)
backend_stack.add_dependency(data_stack)

admin_stack = AdminStack(
    app, "LasoAdminStack",
    user_pool=auth_stack.user_pool,
    app_client=auth_stack.app_client,
    db_secret=data_stack.db_secret,
    env=env,
)
admin_stack.add_dependency(auth_stack)
admin_stack.add_dependency(data_stack)

app.synth()
