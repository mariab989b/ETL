import os, sys, logging
import json
import uuid
import snowflake.connector
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import tempfile

from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

load_dotenv()
logging.basicConfig(level=logging.WARN)


def connect_snow():
    private_key = (
        "-----BEGIN PRIVATE KEY-----\n"
        + os.getenv("PRIVATE_KEY")
        + "\n-----END PRIVATE KEY-----\n"
    )
    p_key = serialization.load_pem_private_key(
        bytes(private_key, "utf-8"), password=None
    )
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role="INGEST",
        database="INGEST",
        schema="INGEST",
        warehouse="INGEST",
        session_parameters={"QUERY_TAG": "py-copy-into"},
    )


def save_to_snowflake(snow, batch, temp_dir):
    logging.debug("inserting batch to db")
    pandas_df = pd.DataFrame(
        batch,
        columns=[
            "TXID",
            "RFID",
            "PRODUCT_ID",
            "PRODUCT_VARIANT_ID",
            "ITEM",  
            "SIZE",
            "CATEGORY",
            "GENDER",
            "SUB_CATEGORY",
            "PRICE",
            "PURCHASE_TIME",
            "DELIVERY_TIME",
            "EXPIRATION_TIME",
            "DAYS",
            "REFUNDED",
            "REFUND_REASON",
            "REVIEW_SCORE",
            "REVIEW_TEXT",
            "NAME",
            "ADDRESS_STREET",
            "ADDRESS_CITY",
            "ADDRESS_POSTALCODE",
            "PHONE",
            "EMAIL",
            "DATE_OF_BIRTH",
            "SEX",
        ],
    )
    arrow_table = pa.Table.from_pandas(pandas_df)
    out_path = f"{temp_dir.name}/{str(uuid.uuid1())}.parquet"
    pq.write_table(arrow_table, out_path, use_dictionary=False, compression="SNAPPY")
    snow.cursor().execute(
        "PUT 'file://{0}' @%CLIENT_SUPPORT_ORDERS".format(
            out_path
        )  # Updated table name
    )
    os.unlink(out_path)
    snow.cursor().execute(
        "COPY INTO CLIENT_SUPPORT_ORDERS FILE_FORMAT=(TYPE='PARQUET') MATCH_BY_COLUMN_NAME=CASE_SENSITIVE PURGE=TRUE"  # Updated table name
    )
    logging.debug(f"inserted {len(batch)} orders")  # Changed from tickets to orders


if __name__ == "__main__":
    args = sys.argv[1:]
    batch_size = int(args[0])
    snow = connect_snow()
    batch = []
    temp_dir = tempfile.TemporaryDirectory()
    for message in sys.stdin:
        if message != "\n":
            record = json.loads(message)
            addr = record.get("address") or {}
            batch.append(
                (
                    record["txid"],
                    record["rfid"],
                    record["product_id"],
                    record["product_variant_id"],
                    record["item"],  # Changed from resort to item,
                    record["size"],
                    record["category"],
                    record["gender"],
                    record["sub_category"],
                    record["price"],
                    record["purchase_time"],
                    record["delivery_time"],
                    record["expiration_time"],
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
                    record["date_of_birth"],
                    record["sex"],
                )
            )
            if len(batch) == batch_size:
                save_to_snowflake(snow, batch, temp_dir)
                batch = []
        else:
            break
    if len(batch) > 0:
        save_to_snowflake(snow, batch, temp_dir)
    temp_dir.cleanup()
    snow.close()
    logging.info("Ingest complete")
