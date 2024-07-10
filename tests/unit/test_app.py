import json
from unittest import mock

from src.app import lambda_handler


@mock.patch("src.app.InvoiceWebhookUseCase.process_invoice_credited_webhook")
class TestApp:
    def test_success(
        self,
        process_invoice_credited_webhook_mock,
        testing_config,
        event_content_invoice_credited,
    ):
        lambda_event = {
            "resource": "/webhook",
            "path": "/webhook",
            "httpMethod": "POST",
            "headers": {"Digital-Signature": "Signature"},
            "multiValueHeaders": {},
            "queryStringParameters": {},
            "multiValueQueryStringParameters": {},
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "id",
                "authorizer": {"claims": None, "scopes": None},
                "domainName": "id.execute-api.us-east-1.amazonaws.com",
                "domainPrefix": "id",
                "extendedRequestId": "request-id",
                "httpMethod": "POST",
                "identity": {},
                "path": "/webhook",
                "protocol": "HTTP/1.1",
                "requestId": "id=",
                "requestTime": "04/Mar/2020:19:15:17 +0000",
                "requestTimeEpoch": 1583349317135,
                "resourceId": None,
                "resourcePath": "/webhook",
                "stage": "$default",
            },
            "pathParameters": None,
            "stageVariables": None,
            "body": json.dumps(event_content_invoice_credited),
            "isBase64Encoded": False,
        }
        process_invoice_credited_webhook_mock.return_value = (
            200,
            "Ok",
            "Created transfer with id 123",
        )

        response = lambda_handler(
            event=lambda_event, context=mock.ANY, config=testing_config
        )

        assert response == {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Ok",
                }
            ),
        }
        process_invoice_credited_webhook_mock.assert_called_once_with(
            event_body=lambda_event["body"],
            event_headers=lambda_event["headers"],
        )
