# Email Queuing

Queues email in AWS SQS in batches of 50 (maximum amount of supported by AWS SES) to be processed and send by the worker function.

## Deploy Steps

1. `cd venv/lib/python-X.X/site-packages`
2. `zip -r ../../../../out.zip`
3. `zip -g out.zip lambda_function.py`
4. Upload the files to AWS Lambda

## API Documentation

Templating can be done by declaring `${key}` in the string of the body.

### Request headers

x-api-key: \<api-key\>

### Request body

```json
{
  "from_email": "string",
  "from_name": "string",
  "data": [
    {
      "e": "string",
      ...some other key value pairs
    }
  ],
  "cc": [
    "string",
    "string"
  ],
  "bcc": [
    "string",
    "string"
  ],
  "subject": "string",
  "html_body": "string",
  "text_body": "string",
  "reply_to": [
    "string",
    "string"
  ]
}
```

**Parameters:**

- **from_email** [REQUIRED] (string): The email address that is sending the email.
- **from_name** [REQUIRED] (string): The name to be displayed on the mail client.
- **data** [REQUIRED] (object):
  - **e** [REQUIRED] (string): email address of the recipient.
  - any other key value pairs can be added for email templating.
- **cc** [REQUIRED] (array): cc email addresses. Default value = `[]`
  - (string) ...
- **bcc** [REQUIRED] (array): bcc email addresses. Default value = `[]`
  - (string) ...
- **subject** [REQUIRED] (string): subject of the email.
- **html_body** [REQUIRED] (string): body of the email in HTML. Can contain `${}` for string substitution from the data key. Default value = `""`
- **text_body** [REQUIRED] (string): body of the email in text. Can contain `${}` for string substitution from the data key. Default value = `""`
- **reply_to** [REQUIRED] (string): reply to email address. Default value = `[]`

### Sample

**Sample Request**

```json
{
  "from_email": "no-reply@xyz.com",
  "from_name": "alice",
  "data": [
    {
      "e": "abc@abc.com",
      "name": "bob"
    }
  ],
  "cc": [],
  "bcc": [],
  "subject": "Hello test!!",
  "html_body": "Hello ${name}",
  "text_body": "",
  "reply_to": ["help@qwe.com"]
}
```

**Sample Response**

```json
{
  "status": "queued",
  "job_id": "669d1d4b-7243-4b58-9704-d3c1rs43b6ee"
}
```
