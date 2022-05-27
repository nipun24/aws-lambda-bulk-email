import os
import json
import peewee as pw


def lambda_handler(event, context):
    db = pw.MySQLDatabase(os.environ['DB_NAME'], host=os.environ['HOST'], port=3306, user=os.environ['USER'],
                          password=os.environ['PASSWORD'])

    class Report(pw.Model):
        message_id = pw.CharField()
        type = pw.CharField()
        source = pw.CharField()
        ts = pw.CharField()
        recipients = pw.CharField()
        feedback_id = pw.CharField()

        class Meta:
            database = db
            db_table = os.environ['DB_TABLE_NAME']

    db.connect()

    data = json.loads(event["Records"][0]["Sns"]["Message"])
    msg_type = data["notificationType"].lower()
    res = list()
    if msg_type == "delivery":
        for i in data["delivery"]["recipients"]:
            res.append({"message_id": data["mail"]["messageId"],
                        "type": msg_type,
                        "source": data["mail"]["source"],
                        "ts": data["mail"]["timestamp"],
                        "recipients": i,
                        "feedback_id": None})
    elif msg_type == "bounce":
        for i in data["bounce"]["bouncedRecipients"]:
            res.append({"message_id": data["mail"]["messageId"],
                        "type": msg_type,
                        "source": data["mail"]["source"],
                        "ts": data["mail"]["timestamp"],
                        "recipients": json.dumps(i),
                        "feedback_id": data["bounce"]["feedbackId"]})
    elif msg_type == "complaint":
        for i in data["complaint"]["complainedRecipients"]:
            res.append({"message_id": data["mail"]["messageId"],
                        "type": msg_type,
                        "source": data["mail"]["source"],
                        "ts": data["mail"]["timestamp"],
                        "recipients": json.dumps([i, data.get("complaintFeedbackType")]),
                        "feedback_id": data["complaint"]["feedbackId"]})

    with db.atomic():
        Report.insert_many(res).execute()

    db.close()
