import datetime
from unittest import mock

import pytest
import starkbank

from src.clients.starkbank import InvalidDigitalSignature, InvoiceLog, StarkBankAdapter


@pytest.fixture
def event_entity_invoice_credited(
    event_content_invoice_credited, event_entity_from_content
):
    return event_entity_from_content(event_content_invoice_credited)


@pytest.fixture
def event_entity_invoice_created(
    event_content_invoice_created, event_entity_from_content
):

    return event_entity_from_content(event_content_invoice_created)


@pytest.fixture
def event_entity_boleto_holmes(event_entity_from_content, event_content_boleto_holmes):

    return event_entity_from_content(event_content_boleto_holmes)


@mock.patch.object(starkbank.event, "parse")
class TestStarkBankAdapterGetEventEntityAndIdFromBody:
    def test_success(
        self, event_parse_mock, event_entity_invoice_credited, testing_config
    ):
        sb_adapter = StarkBankAdapter(config=testing_config)
        event_parse_mock.return_value = event_entity_invoice_credited

        result = sb_adapter.get_event_entity_and_id_from_body(
            event_body="{}", digital_signature="Signature"
        )

        assert result == (
            event_entity_invoice_credited,
            event_entity_invoice_credited.id,
        )
        event_parse_mock.assert_called_once()

    def test_invalid_signature(self, event_parse_mock, testing_config):
        sb_adapter = StarkBankAdapter(config=testing_config)
        event_parse_mock.side_effect = starkbank.error.InvalidSignatureError()

        with pytest.raises(InvalidDigitalSignature):
            sb_adapter.get_event_entity_and_id_from_body(
                event_body="{}", digital_signature="Signature"
            )

        event_parse_mock.assert_called_once()


@mock.patch.object(starkbank.invoice, "payment")
class TestStarkBankAdapterGetInvoiceDataFromEventEntity:
    def test_invoice_credited(
        self,
        invoice_payment_mock,
        event_entity_invoice_credited,
        testing_config,
    ):
        sb_adapter = StarkBankAdapter(config=testing_config)
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

        result = sb_adapter.get_invoice_data_from_event_entity(
            event_entity=event_entity_invoice_credited
        )

        assert result == InvoiceLog(
            log_type=event_entity_invoice_credited.log.type,
            invoice_fee=event_entity_invoice_credited.log.invoice.fee,
            invoice_id=event_entity_invoice_credited.log.invoice.id,
            paid_amount=payment.amount,
        )
        invoice_payment_mock.assert_called_once_with(
            event_entity_invoice_credited.log.invoice.id
        )

    def test_invoice_other_than_credited(
        self,
        invoice_payment_mock,
        event_entity_invoice_created,
        testing_config,
    ):
        sb_adapter = StarkBankAdapter(config=testing_config)

        result = sb_adapter.get_invoice_data_from_event_entity(
            event_entity=event_entity_invoice_created
        )

        assert result == InvoiceLog(
            log_type=event_entity_invoice_created.log.type,
            invoice_fee=event_entity_invoice_created.log.invoice.fee,
            invoice_id=event_entity_invoice_created.log.invoice.id,
            paid_amount=None,
        )
        invoice_payment_mock.assert_not_called()

    def test_subscription_other_than_invoice(
        self,
        invoice_payment_mock,
        event_entity_boleto_holmes,
        testing_config,
    ):
        sb_adapter = StarkBankAdapter(config=testing_config)

        result = sb_adapter.get_invoice_data_from_event_entity(
            event_entity=event_entity_boleto_holmes
        )

        assert result is None
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
