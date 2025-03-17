import json
import os
import boto3


# Add cfnresponse
def send_cfn_response(event, context, response_status, response_data, reason=None):
    response_body = {
        "Status": response_status,
        "Reason": reason or "See the details in CloudWatch Log Stream",
        "PhysicalResourceId": None,
        "StackId": event["StackId"],
        "RequestId": None,
        "LogicalResourceId": None,
        "NoEcho": False,
        "Data": response_data,
    }


def handler(event, context):
    if event["RequestType"] in ["Create", "Update"]:
        try:
            rds_data = boto3.client("rds-data")
            secrets = boto3.client("secretsmanager")

            # Get readonly user credentials
            readonly_secret = secrets.get_secret_value(
                SecretId=os.environ["READONLY_SECRET_ARN"]
            )
            readonly_creds = json.loads(readonly_secret["SecretString"])

            # SQL statements to create read-only user and permissions
            statements = [
                f"CREATE USER {readonly_creds['username']} WITH PASSWORD '{readonly_creds['password']}'",
                "CREATE ROLE readonly_role",
                f"GRANT CONNECT ON DATABASE {os.environ['DB_NAME']} TO readonly_role",
                "GRANT USAGE ON SCHEMA public TO readonly_role",
                "GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_role",
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_role",
                f"GRANT readonly_role TO {readonly_creds['username']}",
                f"ALTER USER {readonly_creds['username']} SET default_transaction_read_only = ON",
            ]

            # Execute each statement using Data API
            for sql in statements:
                response = rds_data.execute_statement(
                    resourceArn=os.environ["CLUSTER_ARN"],
                    secretArn=os.environ["ADMIN_SECRET_ARN"],
                    database=os.environ["DB_NAME"],
                    sql=sql,
                )
                print(f"Executed statement: {sql}")

            response_data = {
                "PhysicalResourceId": f"ReadOnlyUser-{readonly_creds['username']}",
                "Data": {"Message": "Read-only user created successfully"},
            }
            send_cfn_response(event, context, "SUCCESS", response_data)

        except Exception as e:
            print(f"Error: {str(e)}")
            send_cfn_response(event, context, "FAILED", {"Error": str(e)})

    elif event["RequestType"] == "Delete":
        try:
            rds_data = boto3.client("rds-data")
            secrets = boto3.client("secretsmanager")

            # Get readonly user credentials
            readonly_secret = secrets.get_secret_value(
                SecretId=os.environ["READONLY_SECRET_ARN"]
            )
            readonly_creds = json.loads(readonly_secret["SecretString"])

            # Drop user if exists
            sql = f"DROP USER IF EXISTS {readonly_creds['username']}"
            rds_data.execute_statement(
                resourceArn=os.environ["CLUSTER_ARN"],
                secretArn=os.environ["CLUSTER_SECRET_ARN"],
                database=os.environ["DB_NAME"],
                sql=sql,
            )
            response_data = {
                "PhysicalResourceId": event.get(
                    "PhysicalResourceId", "ReadOnlyUserCreated"
                )
            }
            send_cfn_response(event, context, "SUCCESS", response_data)

        except Exception as e:
            print(f"Error during deletion: {str(e)}")
            send_cfn_response(event, context, "FAILED", {"Error": str(e)})
