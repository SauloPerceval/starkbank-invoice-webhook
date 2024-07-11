import pytest


@pytest.fixture
def testing_config():
    from src.config import TestingConfig

    return TestingConfig(
        {
            "STARKBANK_ENVIRONMENT": "sandbox",
            "STARKBANK_PROJECT_ID": "12345678900",
            "STARKBANK_PRIVATE_KEY_CONTENT": """
            -----BEGIN EC PARAMETERS-----
            BgUrgQQACg==
            -----END EC PARAMETERS-----
            -----BEGIN EC PRIVATE KEY-----
            MHQCAQEEIMCwW74H6egQkTiz87WDvLNm7fK/cA+ctA2vg/bbHx3woAcGBSuBBAAK
            oUQDQgAE0iaeEHEgr3oTbCfh8U2L+r7zoaeOX964xaAnND5jATGpD/tHec6Oe9U1
            IF16ZoTVt1FzZ8WkYQ3XomRD4HS13A==
            -----END EC PRIVATE KEY-----
            """,
            "TRANSFERS_TAG": "test",
            "TRANSFER_DESTINATION_BANK_CODE": "123",
            "TRANSFER_DESTINATION_BRANCH": "12345-7",
            "TRANSFER_DESTINATION_ACCOUNT": "1234567-8",
            "TRANSFER_DESTINATION_NAME": "Fulano da Silva",
            "TRANSFER_DESTINATION_CPF_CNPJ": "123.456.789-00",
            "TRANSFER_DESTINATION_ACCOUNT_TYPE": "checking",
            "REDIS_HOST": "test",
            "REDIS_PORT": "6379",
            "REDIS_PASSWORD": "pass",
            "DUPLICATED_EVENT_VALIDATION_EXP": 60,
        }
    )


@pytest.fixture
def event_content_invoice_credited():
    return {
        "event": {
            "created": "2024-01-31T21:15:17.463956+00:00",
            "id": "6046987522670592",
            "log": {
                "created": "2024-01-31T21:15:16.852263+00:00",
                "errors": [],
                "id": "5244688441278464",
                "invoice": {
                    "amount": 10000,
                    "brcode": "",
                    "created": "2024-01-31T21:15:16.701209+00:00",
                    "descriptions": [],
                    "discountAmount": 0,
                    "discounts": [],
                    "due": "2024-11-30T02:06:26.249976+00:00",
                    "expiration": 1,
                    "fee": 100,
                    "fine": 2.5,
                    "fineAmount": 0,
                    "id": "5807638394699776",
                    "interest": 1.3,
                    "interestAmount": 0,
                    "link": "",
                    "name": "Iron Bank S.A.",
                    "nominalAmount": 10000,
                    "pdf": "",
                    "rules": [],
                    "splits": [],
                    "status": "paid",
                    "tags": ["war supply", "invoice #1234"],
                    "taxId": "20.018.183/0001-80",
                    "transactionIds": [],
                    "updated": "2024-01-31T21:15:16.852309+00:00",
                },
                "type": "credited",
            },
            "subscription": "invoice",
            "workspaceId": "6341320293482496",
        }
    }


@pytest.fixture
def event_content_invoice_created(event_content_invoice_credited):
    event_content_invoice_credited["event"]["log"]["type"] = "created"

    return event_content_invoice_credited


@pytest.fixture
def event_content_boleto_holmes(event_content_invoice_credited):
    return {
        "event": {
            **event_content_invoice_credited["event"],
            "subscription": "boleto-holmes",
            "log": {
                "id": "1010101010101010",
                "created": "2020-07-24T17:58:08.338233+00:00",
                "updated": "2020-07-24T17:58:08.338233+00:00",
                "errors": [],
                "type": "solved",
                "holmes": {
                    "boletoId": "5656565656565656",
                    "created": "2020-07-23T00:07:51.611174+00:00",
                    "id": "3232323232323232",
                    "result": "paid",
                    "status": "solved",
                    "tags": ["sherlock", "holmes"],
                    "updated": "2020-07-23T00:07:51.611174+00:00",
                },
            },
        },
    }


@pytest.fixture
def event_entity_from_content():
    from datetime import datetime

    import starkbank

    def get_event_entity_from_content_dict(content_dict):
        return starkbank.Event(
            id=content_dict["event"]["id"],
            workspace_id=content_dict["event"]["workspaceId"],
            log=content_dict["event"]["log"],
            created=datetime.fromisoformat(content_dict["event"]["created"]),
            subscription=content_dict["event"]["subscription"],
            is_delivered=False,
        )

    return get_event_entity_from_content_dict
