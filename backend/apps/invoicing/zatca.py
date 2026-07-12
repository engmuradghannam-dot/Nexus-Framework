"""ZATCA Phase-1 (Fatoora) TLV QR encoding for simplified tax invoices."""
import base64


def _tlv(tag: int, value: str) -> bytes:
    raw = (value or "").encode("utf-8")
    return bytes([tag, len(raw)]) + raw


def zatca_qr_base64(seller_name, vat_number, timestamp, total, vat_amount):
    """Return the base64 TLV string ZATCA requires in the invoice QR.

    Tags: 1=seller, 2=VAT number, 3=timestamp(ISO), 4=total (incl. VAT), 5=VAT.
    """
    payload = (
        _tlv(1, str(seller_name))
        + _tlv(2, str(vat_number))
        + _tlv(3, str(timestamp))
        + _tlv(4, f"{float(total):.2f}")
        + _tlv(5, f"{float(vat_amount):.2f}")
    )
    return base64.b64encode(payload).decode("ascii")
