import json
import logging

from config import StagingConfig
from use_case import InvoiceWebhookUseCase


logger = logging.getLogger()


def lambda_handler(event, context, config=StagingConfig()):
    logger.setLevel(config["LOGLEVEL"] or "INFO")

    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    use_case = InvoiceWebhookUseCase(config=config, logger=logger)
    status_code, response_message, log_message = (
        use_case.process_invoice_credited_webhook(
            event_body=event.get("body"),
            event_headers=event.get("headers", {}),
        )
    )

    logger.info(log_message)
    return {
        "statusCode": status_code,
        "body": json.dumps(
            {
                "message": response_message,
            }
        ),
    }
