# STARKBANK INVOICE WEBHOOK

This application is part of the Starkbank backend test. It consists in a AWS Lambda Function triggered by a API Gateway to receive invoices related webhooks from Starkbank and create transfers with paid invoices values.

## Running tests

- Install testing requirements

```bash
pip install -r tests/requirements.txt
```

- Execute tests using pytest

```bash
pytest --cov=src tests
```

## Build and run app locally with SAM + ngrok

- Install and configure [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

- Build SAM application stack

```bash
sam build
```

- Create a json file (e.x. .env.json) with the required env vars, following the example:

```
{
  "StarkbankInvoiceCreation": {
    "STARKBANK_PROJECT_ID": "Your Starkbank Project ID",
    "STARKBANK_PRIVATE_KEY_CONTENT": "Your private key content",
  }
}
```

- Start your API Gateway and lambda locally, passing the json file as environment file (require [Docker](https://docs.docker.com/engine/install/) installed)

```bash
sam local start-api --env-vars .env.json --log-file /dev/stdout
```

- Install and configure [ngrok](https://ngrok.com/download)

- In a different terminal, start ngrok redirecting requests to your running API Gateway

```bash
ngrok http 3000
```

- Configure a new webhook on Starkbank, using the URL provided by ngrok

- Start receiving events on your local API Gateway, that will trigger your local lambda
