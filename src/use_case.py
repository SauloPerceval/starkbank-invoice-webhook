from logging import Logger
from typing import Optional, Tuple

import redis

from clients.starkbank import InvalidDigitalSignature, StarkBankAdapter
from config import Config


class InvoiceWebhookUseCase:
    def __init__(
        self,
        logger: Logger,
        config: Config,
        adapter_class=StarkBankAdapter,
        redis_client_class=redis.Redis,
    ) -> None:
        self._logger = logger
        self._config = config
        self._sb_adapter = adapter_class(config=config)

        self._redis_client = redis_client_class(
            host=config["REDIS_HOST"],
            port=config["REDIS_PORT"],
            password=config["REDIS_PASSWORD"],
        )

    def process_invoice_credited_webhook(
        self, event_body: Optional[str], event_headers: dict
    ) -> Tuple[int, str, str]:
        if not event_body:
            return 400, "Request must contain body", "Received a request without body"

        if not (digital_signature := event_headers.get("Digital-Signature")):
            return (
                401,
                "Digital-Signature not provided on headers, can not confirm webhook authenticity",
                "Received a request without Digital-Signature on headers",
            )

        try:
            starkbank_event_entity, event_id = (
                self._sb_adapter.get_event_entity_and_id_from_body(
                    event_body=event_body, digital_signature=digital_signature
                )
            )
        except InvalidDigitalSignature:
            return (
                401,
                "Invalid Digital-Signature",
                "Received a request with invalid Digital-Signature headers",
            )

        event_id_setted = self._redis_client.set(
            f"starkbank-event-id:{event_id}",
            1,
            nx=True,
            ex=self._config["DUPLICATED_EVENT_VALIDATION_EXP"],
        )

        if not event_id_setted:
            return (
                200,
                "Ok",
                f"Event with id {event_id} was already processed before, will be ignored",
            )

        self._logger.info(f"Processing event with id {event_id}")

        invoice_log = self._sb_adapter.get_invoice_data_from_event_entity(
            event_entity=starkbank_event_entity
        )
        if not invoice_log:
            return 200, "Ok", "Received event was not related with invoice"

        if not invoice_log.paid_amount:
            return (
                200,
                "Ok",
                f"Received event for invoice with id {invoice_log.invoice_id} is type {invoice_log.log_type} instead of credited",
            )

        self._logger.info(
            f"Invoice with id {invoice_log.invoice_id} paid with {invoice_log.paid_amount} and fee {invoice_log.invoice_fee}"
        )
        amount = invoice_log.paid_amount - invoice_log.invoice_fee
        self._logger.info(f"Creating a transfer with value {amount}")

        transfer_id = self._sb_adapter.create_transfer(
            amount=amount,
            cpf_cnpj=self._config["TRANSFER_DESTINATION_CPF_CNPJ"],
            name=self._config["TRANSFER_DESTINATION_NAME"],
            bank_code=self._config["TRANSFER_DESTINATION_BANK_CODE"],
            branch_code=self._config["TRANSFER_DESTINATION_BRANCH"],
            account_number=self._config["TRANSFER_DESTINATION_ACCOUNT"],
            account_type=self._config["TRANSFER_DESTINATION_ACCOUNT_TYPE"],
            tag=self._config["TRANSFERS_TAG"],
        )

        return 200, "Ok", f"Created transfer with id {transfer_id}"
