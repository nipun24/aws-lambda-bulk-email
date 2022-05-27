import json
import os
from string import Template
from traceback import format_exc
import peewee as pw
import boto3


def lambda_handler(event, context):
    db = pw.MySQLDatabase(os.environ['DB_NAME'], host=os.environ['HOST'], port=3306, user=os.environ['USER'],
                          password=os.environ['PASSWORD'])
    db.connect()

    # job model
    class Job(pw.Model):
        job_id = pw.CharField()
        source = pw.CharField()
        subject = pw.CharField()
        htmlbody = pw.CharField()
        textbody = pw.CharField()
        message_id = pw.CharField()
        response_metadata = pw.CharField()
        email = pw.CharField()
        error_message = pw.CharField()

        class Meta:
            database = db
            db_table = os.environ['DB_TABLE_NAME']

    try:
        req = json.loads(event["Records"][0]["body"])
        print(req)
        job_id = req["job_id"]
        print(job_id)

        # initialize ses client
        client = boto3.client('ses', region_name=os.environ["REGION"])

        # create string template
        html_template = Template(req.get("html_body"))
        text_template = Template(req.get("text_body"))

        # send emails
        res = list()
        err = 0
        for i in req["data"]:
            try:
                body = dict()
                if req.get("html_body"):
                    body["Html"] = {
                        "Data": html_template.safe_substitute(i),
                        "Charset": 'utf-8'
                    }
                if req.get("text_body"):
                    body["Text"] = {
                        "Data": text_template.safe_substitute(i),
                        "Charset": 'utf-8'
                    }

                response = client.send_email(
                    Source=req["from_address"],
                    Destination={
                        'ToAddresses': [i["e"]],
                        'CcAddresses': req.get("cc") or [],
                        'BccAddresses': req.get("bcc") or [],
                    },
                    Message={
                        'Subject': {
                            'Data': req["subject"],
                            'Charset': 'utf-8'
                        },
                        'Body': body
                    },
                    ReplyToAddresses=req.get("reply_to") or []
                )

                # appending to list to update db
                res.append({
                    "job_id": job_id,
                    "message_id": response["MessageId"],
                    "source": req["from_address"],
                    "subject": req["subject"],
                    "htmlbody": req.get("html_body"),
                    "textbody": req.get("text_body"),
                    "response_metadata": json.dumps(response["ResponseMetadata"]),
                    "email": i["e"]
                })

            except Exception:
                print(format_exc())
                job = Job.create(job_id=job_id, error_message=format_exc())
                job.save()
                err += 1

        with db.atomic():
            Job.insert_many(res).execute()

    except Exception:
        print(format_exc())
        job = Job.create(error_message=format_exc())
        job.save()
