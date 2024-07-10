import datetime
from unittest import mock

import pytest
import starkbank

from clients.starkbank import InvalidDigitalSignature, InvoiceLog, StarkBankAdapter


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
def event_entity_from_content():
    def get_event_entity_from_content_dict(content_dict):
        return starkbank.Event(
            id=content_dict["event"]["id"],
            workspace_id=content_dict["event"]["workspaceId"],
            log=content_dict["event"]["log"],
            created=datetime.datetime.fromisoformat(content_dict["event"]["created"]),
            subscription=content_dict["event"]["subscription"],
            is_delivered=False,
        )

    return get_event_entity_from_content_dict


@pytest.fixture
def event_entity_invoice_credited(
    event_content_invoice_credited, event_entity_from_content
):
    return event_entity_from_content(event_content_invoice_credited)


@pytest.fixture
def event_entity_invoice_created(
    event_content_invoice_credited, event_entity_from_content
):
    event_content_invoice_credited["event"]["log"]["type"] = "created"

    return event_entity_from_content(event_content_invoice_credited)


@pytest.fixture
def event_boleto_holmes(event_entity_from_content, event_content_invoice_credited):
    boleto_holmes_event_content = {
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

    return event_entity_from_content(boleto_holmes_event_content)


@mock.patch.object(starkbank.invoice, "payment")
@mock.patch.object(starkbank.event, "parse")
class TestStarkBankAdapterGetInvoiceDataFromEvent:
    def test_invoice_credited(
        self,
        event_parse_mock,
        invoice_payment_mock,
        event_entity_invoice_credited,
        testing_config,
    ):
        sb_adapter = StarkBankAdapter(config=testing_config)
        event_parse_mock.return_value = event_entity_invoice_credited
        payment = starkbank.invoice.Payment(
            amount=10100,
            name="Fulano da Silva",
            tax_id="12345678900",
            bank_code="123",
            branch_code="123456-7",
            account_number="1234567-8",
            account_type="checking",
            end_to_end_id="ABC123",
            method="pix",
        )
        invoice_payment_mock.return_value = payment

        result = sb_adapter.get_invoice_data_from_event(
            event_body="{}",
            digital_signature="Signature",
        )

        assert result == InvoiceLog(
            log_type=event_entity_invoice_credited.log.type,
            invoice_fee=event_entity_invoice_credited.log.invoice.fee,
            invoice_id=event_entity_invoice_credited.log.invoice.id,
            paid_amount=payment.amount,
        )
        event_parse_mock.assert_called_once()
        invoice_payment_mock.assert_called_once_with(
            event_entity_invoice_credited.log.invoice.id
        )

    def test_invoice_other_than_credited(
        self,
        event_parse_mock,
        invoice_payment_mock,
        event_entity_invoice_created,
        testing_config,
    ):
        sb_adapter = StarkBankAdapter(config=testing_config)
        event_parse_mock.return_value = event_entity_invoice_created

        result = sb_adapter.get_invoice_data_from_event(
            event_body="{}",
            digital_signature="Signature",
        )

        assert result == InvoiceLog(
            log_type=event_entity_invoice_created.log.type,
            invoice_fee=event_entity_invoice_created.log.invoice.fee,
            invoice_id=event_entity_invoice_created.log.invoice.id,
            paid_amount=None,
        )
        event_parse_mock.assert_called_once()
        invoice_payment_mock.assert_not_called()

    def test_subscription_other_than_invoice(
        self,
        event_parse_mock,
        invoice_payment_mock,
        event_boleto_holmes,
        testing_config,
    ):
        sb_adapter = StarkBankAdapter(config=testing_config)
        event_parse_mock.return_value = event_boleto_holmes

        result = sb_adapter.get_invoice_data_from_event(
            event_body="{}",
            digital_signature="Signature",
        )

        assert result is None
        event_parse_mock.assert_called_once()
        invoice_payment_mock.assert_not_called()

    def test_invalid_digital_signature(
        self,
        event_parse_mock,
        invoice_payment_mock,
        testing_config,
    ):
        sb_adapter = StarkBankAdapter(config=testing_config)
        event_parse_mock.side_effect = starkbank.error.InvalidSignatureError()

        with pytest.raises(InvalidDigitalSignature):
            sb_adapter.get_invoice_data_from_event(
                event_body="{}",
                digital_signature="Signature",
            )

        event_parse_mock.assert_called_once()
        invoice_payment_mock.assert_not_called()


@mock.patch.object(starkbank.transfer, "create")
class TestStarkBankAdapterCreateTransfer:
    def test_success(self, transfer_create_mock, testing_config):
        transfer_result = starkbank.Transfer(
            amount=10000,
            name="Fulano da Silva",
            tax_id="123.456.789-00",
            bank_code="123",
            branch_code="123456-7",
            account_number="134567-8",
            account_type="checking",
            id="123",
        )

        transfer_create_mock.return_value = [transfer_result]

        transfer_args = {
            "amount": 100000,
            "cpf_cnpj": "123.456.789-00",
            "name": "Fulano da Silva",
            "bank_code": "123",
            "branch_code": "123456-7",
            "account_number": "134567-8",
            "account_type": "checking",
            "tag": "testing",
        }
        sb_adapter = StarkBankAdapter(config=testing_config)

        result = sb_adapter.create_transfer(**transfer_args)

        assert result == transfer_result.id
        transfers = transfer_create_mock.call_args.args[0]
        assert len(transfers) == 1
        assert transfers[0].amount == transfer_args["amount"]
        assert transfers[0].tax_id == transfer_args["cpf_cnpj"]
        assert transfers[0].name == transfer_args["name"]
        assert transfers[0].bank_code == transfer_args["bank_code"]
        assert transfers[0].branch_code == transfer_args["branch_code"]
        assert transfers[0].account_number == transfer_args["account_number"]
        assert transfers[0].account_type == transfer_args["account_type"]
        assert transfers[0].tags == [transfer_args["tag"]]
