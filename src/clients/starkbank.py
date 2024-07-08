from typing import NamedTuple, Optional

from config import Config


class InvoiceLog(NamedTuple):
    log_type: str
    invoice_fee: int
    paid_amount: Optional[int] = None


class InvalidDigitalSignature(Exception):
    pass


class StarkBankAdapter:
    def __init__(self, config: Config):
        import starkbank

        user = starkbank.Project(
            environment=config["STARKBANK_ENVIRONMENT"],
            id=config["STARKBANK_PROJECT_ID"],
            private_key=config["STARKBANK_PRIVATE_KEY_CONTENT"],
        )
        starkbank.user = user

        self._starkbank_client = starkbank

    def get_invoice_data_from_event(
        self, event_body: str, digital_signature: str
    ) -> Optional[InvoiceLog]:
        try:
            event = self._starkbank_client.event.parse(
                content=event_body, signature=digital_signature
            )
        except self._starkbank_client.error.InvalidSignatureError:
            raise InvalidDigitalSignature

        if event.subscription != "invoice":
            return None

        invoice = event.log.invoice
        if (log_type := event.log.type) != "credited":
            return InvoiceLog(log_type=log_type, invoice_fee=invoice.fee)

        payment = self._starkbank_client.invoice.payment(invoice.id)

        return InvoiceLog(
            log_type=log_type, invoice_fee=invoice.fee, paid_amount=payment.amount
        )

    def create_transfer(
        self,
        amount: int,
        cpf_cnpj: str,
        name: str,
        bank_code: str,
        branch_code: str,
        account_number: str,
        account_type: str,
        tag: Optional[str] = None,
    ):
        self._starkbank_client.transfer.create(
            [
                self._starkbank_client.Transfer(
                    amount=amount,
                    tax_id=cpf_cnpj,
                    name=name,
                    bank_code=bank_code,
                    branch_code=branch_code,
                    account_number=account_number,
                    account_type=account_type,
                    tags=[tag] if tag else None,
                )
            ]
        )
