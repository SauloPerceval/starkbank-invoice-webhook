import json
import logging
from unittest import mock

from src.use_case import InvoiceWebhookUseCase


class TestInvoiceWebhookUseCase:
    logger = logging.getLogger()

    @staticmethod
    def create_mocked_adapter_class():
        import json

        from clients.starkbank import (
            InvalidDigitalSignature,
            InvoiceLog,
            StarkBankAdapter,
        )

        class FakeStarkBankAdapter(StarkBankAdapter):
            def __init__(self, config):
                pass

            def get_invoice_data_from_event(
                self, event_body: str, digital_signature: str
            ):
                if digital_signature == "InvalidSignature":
                    raise InvalidDigitalSignature

                event_dict = json.loads(event_body)

                if event_dict["event"]["subscription"] != "invoice":
                    return None

                if (log := event_dict["event"]["log"])["type"] != "credited":
                    return InvoiceLog(
                        log_type=log["type"],
                        invoice_fee=log["invoice"]["fee"],
                        invoice_id=log["invoice"]["id"],
                        paid_amount=None,
                    )

                return InvoiceLog(
                    log_type=log["type"],
                    invoice_fee=log["invoice"]["fee"],
                    invoice_id=log["invoice"]["id"],
                    paid_amount=log["invoice"]["amount"],
                )

            def create_transfer(self, *args, **kwargs):
                return "123"

        return mock.Mock(wraps=FakeStarkBankAdapter)

    def test_process_invoice_credited_webhook_sending_transfer(
        self,
        testing_config,
        event_content_invoice_credited,
    ):
        adapter_class = self.create_mocked_adapter_class()
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=adapter_class,
        )

        status_code, response_message, log_message = (
            use_case.process_invoice_credited_webhook(
                event_body=json.dumps(event_content_invoice_credited),
                event_headers={"Digital-Signature": "Signature"},
            )
        )

        assert status_code == 200
        assert response_message == "Ok"
        assert log_message == "Created transfer with id 123"

    def test_process_invoice_credited_webhook_do_not_send_transfer_for_diffrent_log_type(
        self, testing_config, event_content_invoice_created
    ):
        adapter_class = self.create_mocked_adapter_class()
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=adapter_class,
        )

        status_code, response_message, log_message = (
            use_case.process_invoice_credited_webhook(
                event_body=json.dumps(event_content_invoice_created),
                event_headers={"Digital-Signature": "Signature"},
            )
        )

        assert status_code == 200
        assert response_message == "Ok"
        assert log_message == (
            "Received event for invoice with id 5807638394699776 "
            "is type created instead of credited"
        )

    def test_process_invoice_credited_webhook_do_not_send_transfer_for_different_event(
        self, testing_config, event_content_boleto_holmes
    ):
        adapter_class = self.create_mocked_adapter_class()
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=adapter_class,
        )

        status_code, response_message, log_message = (
            use_case.process_invoice_credited_webhook(
                event_body=json.dumps(event_content_boleto_holmes),
                event_headers={"Digital-Signature": "Signature"},
            )
        )

        assert status_code == 200
        assert response_message == "Ok"
        assert log_message == "Received event was not related with invoice"

    def test_process_invoice_credited_webhook_return_401_for_invalid_signature(
        self, testing_config, event_content_invoice_credited
    ):
        adapter_class = self.create_mocked_adapter_class()
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=adapter_class,
        )

        status_code, response_message, log_message = (
            use_case.process_invoice_credited_webhook(
                event_body=json.dumps(event_content_invoice_credited),
                event_headers={"Digital-Signature": "InvalidSignature"},
            )
        )

        assert status_code == 401
        assert response_message == "Invalid Digital-Signature"
        assert log_message == (
            "Received a request with invalid Digital-Signature headers"
        )

    def test_process_invoice_credited_webhook_return_401_for_missing_signature(
        self, testing_config, event_content_invoice_credited
    ):
        adapter_class = self.create_mocked_adapter_class()
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=adapter_class,
        )

        status_code, response_message, log_message = (
            use_case.process_invoice_credited_webhook(
                event_body=json.dumps(event_content_invoice_credited),
                event_headers={},
            )
        )

        assert status_code == 401
        assert response_message == (
            "Digital-Signature not provided on headers, "
            "can not confirm webhook authenticity"
        )

        assert log_message == "Received a request without Digital-Signature on headers"

    def test_process_invoice_credited_webhook_return_400_for_missing_body(
        self, testing_config
    ):
        adapter_class = self.create_mocked_adapter_class()
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=adapter_class,
        )

        status_code, response_message, log_message = (
            use_case.process_invoice_credited_webhook(
                event_body=None,
                event_headers={"Digital-Signature": "Signature"},
            )
        )

        assert status_code == 400
        assert response_message == "Request must contain body"
        assert log_message == "Received a request without body"
