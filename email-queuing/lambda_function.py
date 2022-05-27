import json
import boto3
import os
from uuid import uuid4
from traceback import format_exc
import peewee as pw


def lambda_handler(event, context):
    db = pw.MySQLDatabase(os.environ['DB_NAME'], host=os.environ['HOST'], port=3306, user=os.environ['USER'],
                          password=os.environ['PASSWORD'])
    db.connect()

    # api key Model
    class Api(pw.Model):
        api_key = pw.CharField()
        email = pw.CharField()

        class Meta:
            database = db
            db_table = os.environ['DB_TABLE_NAME']

    # generate unique job id
    job_id = str(uuid4())
    print("JOB ID:", job_id)

    try:
        # check if api key is valid
        api_key = event["headers"]["x-api-key"]

        email = ""

        # check if api key exists
        try:
            rec = Api.get(Api.api_key == api_key)
            email = rec.email
        except Exception:
            print("invalid api key")
            return {
                "statusCode": 401,
                "body": json.dumps("invalid api key")
            }

        # parsing request body
        req = json.loads(event["body"])
        print(req)

        # checking request properties
        if req.get("from_email"):
            del req["from_email"]

        if not isinstance(req.get("from_name"), str):
            return {
                "statusCode": 400,
                "body": 'from_name should be string'
            }

        if not isinstance(req.get("data"), list):
            return {
                "statusCode": 400,
                "body": 'data should be array'
            }

        if len(req.get("data")) > 1000:
            return {
                "statusCode": 400,
                "body": 'data cannot be greater than 1000'
            }

        limit = 50
        if req.get("cc"):
            if isinstance(req.get("cc"), list):
                limit -= len(req.get("cc"))
            else:
                return {
                    "statusCode": 400,
                    "body": 'cc should be array'
                }

        if req.get("bcc"):
            if isinstance(req.get("bcc"), list):
                limit -= len(req.get("bcc"))
            else:
                return {
                    "statusCode": 400,
                    "body": 'bcc should be array'
                }

        if limit < 1:
            return {
                "statusCode": 400,
                "body": "more than 49 cc and bcc emails"
            }

        if not isinstance(req.get("subject"), str):
            return {
                "statusCode": 400,
                "body": 'subject should be array'
            }

        if not (req.get("html_body") or req.get("text_body")):
            return {
                "statusCode": 400,
                "body": 'one of html_body or text_body should be present'
            }

        if req.get("reply_to") and not isinstance(req.get("reply_to"), list):
            return {
                "statusCode": 400,
                "body": 'reply_to should be array'
            }

        # remove "," from from_name
        from_address = f'{req["from_name"].replace(",", " ")} <{email}>'

        # initialize sqs client
        sqs = boto3.client('sqs')

        # add to queue
        err = 0
        data = req.get("data")
        del req["data"]
        for i in range(0, len(data), limit):
            try:
                response = sqs.send_message(
                    QueueUrl=os.environ["SQS_URL"],
                    MessageBody=json.dumps(
                        {
                            "job_id": job_id,
                            "data": data[i:i + limit],
                            "from_address": from_address,
                            **req
                        })
                )

            except Exception:
                print(format_exc())
                err += 1

        return {
            'statusCode': 200,
            'body': json.dumps({"status": "queued", "job_id": job_id, "errors": err})
        }

    except Exception:
        print(format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({"error": format_exc()})
        }
