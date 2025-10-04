import os, sys, logging
import json
import uuid
import snowflake.connector
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import tempfile

from dotenv import load_dotenv
from snowflake.ingest import SimpleIngestManager
from snowflake.ingest import StagedFile
from cryptography.hazmat.primitives import serialization

load_dotenv()
logging.basicConfig(level=logging.WARN)

# ---- Config (optionnel) ----
# Tu peux surcharger via variables d'env si tu veux
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "INGEST")
SNOWFLAKE_DB = os.getenv("SNOWFLAKE_DATABASE", "INGEST")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "INGEST")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "INGEST")
SNOWFLAKE_QUERY_TAG = os.getenv("SNOWFLAKE_QUERY_TAG", "py-snowpipe")

# Nom de la table cible (doit exister) pour utiliser la table stage @%TABLE
TARGET_TABLE = os.getenv("SNOWFLAKE_TARGET_TABLE", "CLIENT_SUPPORT_ORDERS_PY_SNOWPIPE")

# Nom du pipe (doit exister)
PIPE_NAME = os.getenv("SNOWFLAKE_PIPE", "INGEST.INGEST.CLIENT_SUPPORT_ORDERS_PIPE")


def connect_snow():
    private_key_pem = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n"
    p_key = serialization.load_pem_private_key(bytes(private_key_pem, "utf-8"), password=None)
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role=SNOWFLAKE_ROLE,
        database=SNOWFLAKE_DB,
        schema=SNOWFLAKE_SCHEMA,
        warehouse=SNOWFLAKE_WAREHOUSE,
        session_parameters={"QUERY_TAG": SNOWFLAKE_QUERY_TAG},
    )


def normalize_record(record: dict) -> tuple:
    """
    Adapte un record JSON généré par Data_generation.py au schéma tabulaire.
    - Adresse aplatie en 3 colonnes (rue, ville, CP).
    - Suppression de emergency_contact (plus utilisé).
    - Ajout des nouvelles colonnes (product_id, product_variant_id, date_of_birth, sex).
    """
    addr = record.get("address") or {}
    street = addr.get("street_address")
    city = addr.get("city")
    postal = addr.get("postalcode")

    # Tuple dans le même ordre que 'COLUMNS' ci-dessous
    return (
        record.get("txid"),
        record.get("rfid"),
        record.get("product_id"),
        record.get("product_variant_id"),
        record.get("item"),
        record.get("size"),
        record.get("category"),
        record.get("gender"),
        record.get("sub_category"),
        record.get("price"),
        record.get("purchase_time"),
        record.get("delivery_time"),
        record.get("expiration_time"),
        record.get("days"),
        record.get("refunded"),
        record.get("refund_reason"),
        record.get("review_score"),
        record.get("review_text"),
        record.get("name"),
        street,
        city,
        postal,
        record.get("phone"),
        record.get("email"),
        record.get("date_of_birth"),
        record.get("sex"),
    )


# Colonnes alignées avec normalize_record(...)
COLUMNS = [
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
]


def save_to_snowflake(snow, batch, temp_dir, ingest_manager):
    logging.debug("inserting batch to db")

    pandas_df = pd.DataFrame(batch, columns=COLUMNS)
    arrow_table = pa.Table.from_pandas(pandas_df, preserve_index=False)

    file_name = f"{str(uuid.uuid1())}.parquet"
    out_path = f"{temp_dir.name}/{file_name}"
    pq.write_table(arrow_table, out_path, use_dictionary=False, compression="SNAPPY")

    # Charger dans la table stage de la table cible (@%TABLE)
    snow.cursor().execute(f"PUT 'file://{out_path}' @%{TARGET_TABLE}")

    # Supprimer le fichier temporaire local
    os.unlink(out_path)

    # Notifier le pipe Snowpipe
    resp = ingest_manager.ingest_files([StagedFile(file_name, None)])
    logging.info(f"response from snowflake for file {file_name}: {resp.get('responseCode')}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: python ingest.py <batch_size>")
        sys.exit(1)

    batch_size = int(args[0])

    snow = connect_snow()
    temp_dir = tempfile.TemporaryDirectory()

    private_key_pem = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n"
    host = os.getenv("SNOWFLAKE_ACCOUNT") + ".snowflakecomputing.com"

    ingest_manager = SimpleIngestManager(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        host=host,
        user=os.getenv("SNOWFLAKE_USER"),
        pipe=PIPE_NAME,
        private_key=private_key_pem,
    )

    batch = []
    for message in sys.stdin:
        if message != "\n":
            record = json.loads(message)
            batch.append(normalize_record(record))
            if len(batch) == batch_size:
                save_to_snowflake(snow, batch, temp_dir, ingest_manager)
                batch = []
        else:
            break

    if len(batch) > 0:
        save_to_snowflake(snow, batch, temp_dir, ingest_manager)

    temp_dir.cleanup()
    snow.close()
    logging.info("Ingest complete")
