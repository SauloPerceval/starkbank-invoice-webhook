import json
import logging
from unittest import mock

import pytest

from src.use_case import InvoiceWebhookUseCase


@pytest.fixture
def mocked_adapter_class(event_entity_from_content):
    import json

    from clients.starkbank import InvalidDigitalSignature, InvoiceLog, StarkBankAdapter

    class FakeStarkBankAdapter(StarkBankAdapter):
        def __init__(self, config):
            pass

        def get_event_entity_and_id_from_body(
            self, event_body: str, digital_signature: str
        ):
            if digital_signature == "InvalidSignature":
                raise InvalidDigitalSignature

            event = event_entity_from_content(json.loads(event_body))
            return event, event.id

        def get_invoice_data_from_event_entity(self, event_entity):
            if event_entity.subscription != "invoice":
                return None

            if (log := event_entity.log).type != "credited":
                return InvoiceLog(
                    log_type=log.type,
                    invoice_fee=log.invoice.fee,
                    invoice_id=log.invoice.id,
                    paid_amount=None,
                )

            return InvoiceLog(
                log_type=log.type,
                invoice_fee=log.invoice.fee,
                invoice_id=log.invoice.id,
                paid_amount=log.invoice.amount,
            )

        def create_transfer(self, *args, **kwargs):
            return "123"

    return mock.Mock(wraps=FakeStarkBankAdapter)


@pytest.fixture(scope="function")
def fake_redis_class(testing_config):
    import fakeredis

    fake_redis_class = fakeredis.FakeRedis
    yield fake_redis_class
    client = fake_redis_class(
        host=testing_config["REDIS_HOST"],
        port=testing_config["REDIS_PORT"],
        password=testing_config["REDIS_PASSWORD"],
    )
    client.flushall()


class TestInvoiceWebhookUseCase:
    logger = logging.getLogger()

    def test_process_invoice_credited_webhook_sending_transfer(
        self,
        testing_config,
        event_content_invoice_credited,
        mocked_adapter_class,
        fake_redis_class,
    ):
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=mocked_adapter_class,
            redis_client_class=fake_redis_class,
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
        self,
        testing_config,
        event_content_invoice_created,
        mocked_adapter_class,
        fake_redis_class,
    ):
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=mocked_adapter_class,
            redis_client_class=fake_redis_class,
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
        self,
        testing_config,
        event_content_boleto_holmes,
        mocked_adapter_class,
        fake_redis_class,
    ):
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=mocked_adapter_class,
            redis_client_class=fake_redis_class,
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

    def test_process_invoice_credited_webhook_ignore_if_event_id_already_processed(
        self,
        testing_config,
        event_content_invoice_credited,
        mocked_adapter_class,
        fake_redis_class,
    ):
        event_id = event_content_invoice_credited["event"]["id"]
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=mocked_adapter_class,
            redis_client_class=fake_redis_class,
        )
        use_case._redis_client.set(event_id, 1)

        status_code, response_message, log_message = (
            use_case.process_invoice_credited_webhook(
                event_body=json.dumps(event_content_invoice_credited),
                event_headers={"Digital-Signature": "Signature"},
            )
        )

        assert status_code == 200
        assert response_message == "Ok"
        assert log_message == (
            f"Event with id {event_id} was already" " processed before, will be ignored"
        )

    def test_process_invoice_credited_webhook_return_401_for_invalid_signature(
        self,
        testing_config,
        event_content_invoice_credited,
        mocked_adapter_class,
        fake_redis_class,
    ):
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=mocked_adapter_class,
            redis_client_class=fake_redis_class,
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
        self,
        testing_config,
        event_content_invoice_credited,
        mocked_adapter_class,
        fake_redis_class,
    ):
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=mocked_adapter_class,
            redis_client_class=fake_redis_class,
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
        self, testing_config, mocked_adapter_class, fake_redis_class
    ):
        use_case = InvoiceWebhookUseCase(
            logger=self.logger,
            config=testing_config,
            adapter_class=mocked_adapter_class,
            redis_client_class=fake_redis_class,
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
