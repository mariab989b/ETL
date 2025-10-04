import os, sys, logging, json
import snowflake.connector
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

load_dotenv()
logging.basicConfig(level=logging.WARN)
snowflake.connector.paramstyle = 'qmark'

def connect_snow():
    private_key = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n"
    p_key = serialization.load_pem_private_key(private_key.encode("utf-8"), password=None)
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role="INGEST",
        database="INGEST",
        schema="INGEST",
        warehouse="INGEST",
        session_parameters={'QUERY_TAG': 'py-insert'},
    )

def save_to_snowflake(snow, message):
    record = json.loads(message)
    addr = record.get("address") or {}
    row = (
        record["txid"],
        record["rfid"],
        record["product_id"],
        record["product_variant_id"],
        record["item"],
        record["size"],
        record["category"],
        record["gender"],
        record["sub_category"],
        record["price"],
        record["purchase_time"],   # ex: "2025-10-04T12:34:56+02:00" (TIMESTAMP_TZ)
        record["delivery_time"],   # ex: "2025-10-06" (DATE)
        record["expiration_time"], # ex: "2026-10-06" (DATE)
        record["days"],
        record["refunded"],
        record["refund_reason"],
        record["review_score"],
        record["review_text"],
        record["name"],
        addr.get("street_address"),
        addr.get("city"),
        addr.get("postalcode"),
        record["phone"],
        record["email"],
        record["date_of_birth"],   # "YYYY-MM-DD"
        record["sex"],
    )
    assert len(row) == 26, f"Param count mismatch: {len(row)}"
    snow.cursor().execute(
        '''
        INSERT INTO CLIENT_SUPPORT_ORDERS (
          "TXID","RFID","PRODUCT_ID","PRODUCT_VARIANT_ID",
          "ITEM","SIZE","CATEGORY","GENDER","SUB_CATEGORY","PRICE",
          "PURCHASE_TIME","DELIVERY_TIME","EXPIRATION_TIME","DAYS",
          "REFUNDED","REFUND_REASON","REVIEW_SCORE","REVIEW_TEXT",
          "NAME","ADDRESS_STREET","ADDRESS_CITY","ADDRESS_POSTALCODE",
          "PHONE","EMAIL","DATE_OF_BIRTH","SEX"
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''',
        row
    )

if __name__ == "__main__":
    snow = connect_snow()
    try:
        for message in sys.stdin:
            if message.strip():
                save_to_snowflake(snow, message)
    finally:
        snow.close()
        logging.info("Ingest complete")
