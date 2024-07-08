# STARKBANK INVOICE CREATION

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

## Build and execute Lambda Function locally with SAM

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
    "STARKBANK_PRIVATE_KEY_CONTENT": "Your private key content"
  }
}
```
