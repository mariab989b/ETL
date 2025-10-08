# ETL Project — Snowflake Maison Albert
## Groupe 2 - Emilie Boulanger, Maria Boussa, Hugo Braun,Jean-Baptiste Brun

This project demonstrates a data pipeline on **Snowflake** for the fictitious retailer **Maison Albert**.  
We generate realistic synthetic commerce data, route it through a resilient ingestion layer, transform it into an analytical model, and surface results through two **Streamlit** dashboards (analytics and monitoring).  
We document the architecture, data model, methodology, and reproducibility steps, and discuss limitations and future enhancements.

---

## Introduction
Digital retailers require reliable data foundations to drive personalization, merchandising, and customer service.  
We built a production‑like pipeline that transforms raw purchase events into **analysis‑ready datasets**.  
The project implements pragmatic patterns — **landing → staging → dimensional/fact model → consumption**.

---

## Table of Contents
1. Executive Summary  
2. Architecture & Pipeline  
3. Environment & Prerequisites  
4. Data Model  
5. Ingestion & Transformation  
5. Data Structure
6. Streamlit Dashboards  
7. Run Book  
8. Security & Governance  
9. Data Quality & Monitoring  
10. Future Work

---

## 1) Executive Summary
- **Goal.** Demonstrate a reliable and scalable Snowflake pipeline that converts synthetic order events into analysis‑ready datasets.  
- **Implemented:** Python generation → landing table **CLIENT_SUPPORT_ORDERS_PY_SNOWPIPE** → SQL transformations → analytical tables → two Streamlit apps (analytics & monitoring).  
- **Value.** Applies modern Data/Analytics patterns (staging → model → consumption) with a production‑minded, cost‑aware approach.

---

## 2) Architecture & Pipeline
**End‑to‑end flow:**
```
Synthetic Sources
  → DataGenerator
  → Snowflake: Landing
  → SQL Transformations
  → Analytical Storage
  → Streamlit Apps (analytics & monitoring)

(Optional future) → Amazon Aurora / Amazon Personalize / QuickSight
```
The pipeline diagram is included in the repository (`PipeLine_Group2.png`).

**Logical naming.**  
For clarity, we refer to the landing under `INGEST` and the Snowflake analytical objects under `SALES_DATA.SALES_DATA` (DB & Schema).

---

## 3) Environment & Prerequisites
- **Snowflake (Snowsight):** role/warehouse/database/schema configured.  
- **Python ≥ 3.9** for local generation and ingestion.  
- **Key dependencies:** `snowflake-connector-python`, `snowflake-ingest`, `pandas`, `pyarrow`, `python-dotenv`, `faker`, `optional-faker`.

**Secrets / `.env`**
```
SNOWFLAKE_ACCOUNT=...
SNOWFLAKE_USER=...
PRIVATE_KEY=...        # RSA private key
```

**Snowflake Objects**
- **Database:** `SALES_DATA`  
- **Schema:** `SALES_DATA`  
- **Landing table (Snowpipe/COPY target):** `CLIENT_SUPPORT_ORDERS_PY_SNOWPIPE` or `CLIENT_SUPPORT_ORDERS_Kafka` (depending on the chosen ingestion method).  
- **Analytical tables:** `CLIENTS`, `PRODUCTS`, `PRODUCT_VARIANTS`, `ORDERS`, `ORDER_LINES`, `ORDER_STATUS_HISTORY`, `REVIEWS`, `INVENTORY_MOVEMENTS`  
- **Stock view:** `STOCK`, aggregated from movements.

---

## 4) Data Model
Normalized model (clients, products, variants, orders) + stock movements.

```
[CLIENTS] (unique email)   1 ───< [ORDERS] 1 ───< [ORDER_LINES] >─── 1 [PRODUCT_VARIANTS] >─── 1 [PRODUCTS]
      |                         |    \                                  |
      |                         |     \───< [ORDER_STATUS_HISTORY]      \──< [INVENTORY_MOVEMENTS]
      |                         \───< [REVIEWS]
      |
     (demographics / geography base)
```

**Principles**
- One order can contain multiple lines (the generator currently emits **1 line per order**).  
- We store **catalog price (variant)** and **paid price (order line)**.  
- **Stock** = sum of movements by variant.  
- **Refunds** are captured as status events with a `refund_reason` when applicable.

**Landing (wide, JSON‑like):** `CLIENT_SUPPORT_ORDERS` receives one record per purchase.  
**Modeled layer:** `MERGE`s load dimensions/facts; dashboards query these tables/views.

---

## 5) Ingestion & Transformation
### 5.1 Data Generation
`data_gen/Data_generation.py` (Faker `fr_FR`, realistic business rules):
- Always non‑null: `name`, `email`, `address`.  
- `purchase_time` in Europe/Paris; `delivery_date = purchase_date + [1..7]` days;  
  `expiration_date = purchase_date + [36..60]` months (≥ delivery).  
- IDs: `product_id` (UUIDv5 from name), `product_variant_id = product_id_size`.  
- Currency in **EUR**, **2‑decimal** rounding.

### 5.2 Landing (Snowpipe / COPY INTO)
- **Landing table:** `SALES_DATA.SALES_DATA.CLIENT_SUPPORT_ORDERS`  
- Supported methods:
  - **Direct INSERT** (`ingest/py_insert*.py`) — simple; less efficient for large volumes.
  - **Parquet + PUT + COPY INTO** (`ingest/file_insert.py`) — scalable batch ingestion.
  - **Snowpipe** (serverless) — near real‑time (SimpleIngestManager, auto‑ingest).

**Landing DDL**
```sql
CREATE TABLE IF NOT EXISTS SALES_DATA.SALES_DATA.CLIENT_SUPPORT_ORDERS_PY_SNOWPIPE (
  TXID STRING, RFID STRING, PRODUCT_ID STRING, PRODUCT_VARIANT_ID STRING,
  ITEM STRING, SIZE STRING, CATEGORY STRING, GENDER STRING, SUB_CATEGORY STRING,
  PRICE NUMBER(12,2),
  PURCHASE_TIME TIMESTAMP_TZ, DELIVERY_TIME DATE, EXPIRATION_TIME DATE,
  DAYS NUMBER(1,0),
  REFUNDED BOOLEAN, REFUND_REASON STRING,
  REVIEW_SCORE NUMBER(1,0), REVIEW_TEXT STRING,
  NAME STRING, ADDRESS_STREET STRING, ADDRESS_CITY STRING, ADDRESS_POSTALCODE STRING,
  PHONE STRING, EMAIL STRING, DATE_OF_BIRTH DATE, SEX STRING,
  LOAD_FILE_NAME STRING DEFAULT METADATA$FILENAME,
  LOAD_TIME TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
);
```

### 5.3 SQL Modeling
- Temporary staging tables (natural keys, HT/VAT/TTC totals).  
- **MERGE** into:
  - **Dimensions:** `CLIENTS`, `PRODUCTS`, `PRODUCT_VARIANTS`  
  - **Facts:** `ORDERS`, `ORDER_LINES`  
  - **Auxiliary:** `ORDER_STATUS_HISTORY`, `REVIEWS`, `INVENTORY_MOVEMENTS`  
- **STOCK view** = `SUM(quantity_delta)` per variant.

---
# Appendix — 5. Data Structure

The generated data describes **customer orders**. Records first land in a **landing table**, then are modeled into **normalized analytical tables**.

---

## 5.A. Landing — `SALES_DATA.SALES_DATA.CLIENT_SUPPORT_ORDERS_PY_SNOWPIPE`

| Column                | Type            | Description |
|---|---|---|
| TXID                   | STRING          | Unique transaction ID (purchase event) |
| RFID                   | STRING          | Simulated radio/electronic identifier |
| PRODUCT_ID             | STRING          | General product ID |
| PRODUCT_VARIANT_ID     | STRING          | Variant ID (e.g., `PRODUCT_ID_size`) |
| ITEM                   | STRING          | Product name |
| SIZE                   | STRING          | Size (e.g., `30ml`, `100ml`) |
| CATEGORY               | STRING          | Category (floral, woody, spicy, sweet, fresh, amber) |
| SUB_CATEGORY           | STRING          | Sub-category |
| GENDER                 | STRING          | Product target (`f`, `m`, `u`) |
| PRICE                  | NUMBER(12,2)    | Price paid (EUR) |
| PURCHASE_TIME          | TIMESTAMP_TZ    | Purchase timestamp (Europe/Paris) |
| DELIVERY_TIME          | DATE            | Delivery date (D+1 to D+7) |
| EXPIRATION_TIME        | DATE            | Expiration date (purchase + 36 to 60 months) |
| DAYS                   | NUMBER(1,0)     | ISO weekday of purchase (1=Mon … 7=Sun) |
| REFUNDED               | BOOLEAN         | Whether the order was refunded |
| REFUND_REASON          | STRING          | Refund reason (if refunded) |
| REVIEW_SCORE           | NUMBER(1,0)     | Review score (1–5) |
| REVIEW_TEXT            | STRING          | Review text generated from the score |
| NAME                   | STRING          | Customer name |
| ADDRESS_STREET         | STRING          | Address – street |
| ADDRESS_CITY           | STRING          | Address – city |
| ADDRESS_POSTALCODE     | STRING          | Address – postal code |
| PHONE                  | STRING          | Phone (optional) |
| EMAIL                  | STRING          | Email (customer business key) |
| DATE_OF_BIRTH          | DATE            | Date of birth |
| SEX                    | STRING          | Customer sex (`f`, `m`, `x`) |
| LOAD_FILE_NAME         | STRING          | Ingested file name (metadata) |
| LOAD_TIME              | TIMESTAMP_TZ    | Ingestion timestamp (metadata) |

> This table is **denormalized** and serves as the **entry point** to the analytical model.

---

## 5.B. Analytical Model — `SALES_DATA.SALES_DATA.*`

### A) `CLIENTS`
| Column         | Type          | Description |
|---|---|---|
| CLIENT_ID      | STRING        | Customer ID (= `EMAIL`) |
| NAME           | STRING        | Customer name |
| EMAIL          | STRING        | Email (unique) |
| STREET_ADDRESS | STRING        | Street |
| CITY           | STRING        | City |
| POSTALCODE     | STRING        | Postal code |
| DATE_OF_BIRTH  | DATE          | Date of birth |
| SEX            | STRING        | Sex (`f`, `m`, `x`) |
| PHONE          | STRING        | Phone |

### B) `PRODUCTS`
| Column      | Type   | Description |
|---|---|---|
| PRODUCT_ID  | STRING | General product ID |
| NAME        | STRING | Name |
| CATEGORY    | STRING | Category |
| SUB_CATEGORY| STRING | Sub-category |
| GENDER      | STRING | Target (`f`,`m`,`u`) |

### C) `PRODUCT_VARIANTS`
| Column              | Type           | Description |
|---|---|---|
| PRODUCT_VARIANT_ID  | STRING         | Variant ID |
| PRODUCT_ID          | STRING         | FK → `PRODUCTS.PRODUCT_ID` |
| SIZE_LABEL          | STRING         | Size label (`30ml`, `100ml`) |
| SIZE_ML             | NUMBER(10,2)   | Size in ml |
| CATALOG_PRICE       | NUMBER(12,2)   | Catalog price (EUR) |
| CURRENCY            | STRING         | Currency (EUR) |
| ACTIVE              | BOOLEAN        | Whether the variant is active |

### D) `ORDERS`
| Column         | Type           | Description |
|---|---|---|
| ORDER_ID       | STRING         | Order identifier (often = `TXID`) |
| EXTERNAL_TXID  | STRING         | External reference (= `TXID`) |
| CLIENT_ID      | STRING         | FK → `CLIENTS.CLIENT_ID` (= email) |
| PURCHASE_TIME  | TIMESTAMP_TZ   | Purchase timestamp |
| PURCHASE_DOW   | NUMBER(1,0)    | ISO weekday (1–7) |
| DELIVERY_DATE  | DATE           | Delivery date |
| EXPIRATION_DATE| DATE           | Expiration date |
| CURRENCY       | STRING         | Currency (EUR) |
| TOTAL_HT       | NUMBER(12,2)   | Net total (ex-VAT) |
| TOTAL_VAT      | NUMBER(12,2)   | VAT amount |
| TOTAL_TTC      | NUMBER(12,2)   | Gross total (incl. VAT) |

### E) `ORDER_LINES`
| Column            | Type           | Description |
|---|---|---|
| ORDER_LINE_ID     | STRING         | Order line identifier |
| ORDER_ID          | STRING         | FK → `ORDERS.ORDER_ID` |
| PRODUCT_VARIANT_ID| STRING         | FK → `PRODUCT_VARIANTS.PRODUCT_VARIANT_ID` |
| QUANTITY          | NUMBER(10,0)   | Quantity (default 1) |
| UNIT_PRICE_PAID   | NUMBER(12,2)   | Unit price paid (EUR) |
| VAT_RATE          | NUMBER(6,4)    | VAT rate (e.g., 0.2000) |
| LINE_TOTAL_HT     | NUMBER(12,2)   | Net line total |
| LINE_TOTAL_VAT    | NUMBER(12,2)   | VAT line amount |
| LINE_TOTAL_TTC    | NUMBER(12,2)   | Gross line total |

### F) `ORDER_STATUS_HISTORY`
| Column          | Type           | Description |
|---|---|---|
| STATUS_EVENT_ID | STRING         | Status event identifier |
| ORDER_ID        | STRING         | FK → `ORDERS.ORDER_ID` |
| STATUS          | STRING         | `paid`, `delivered`, `refunded`, … |
| STATUS_TIME     | TIMESTAMP_TZ   | Event timestamp |
| REFUND_REASON   | STRING         | Reason if `refunded` |

### G) `REVIEWS`
| Column       | Type          | Description |
|---|---|---|
| REVIEW_ID    | STRING        | Review identifier |
| ORDER_ID     | STRING        | FK → `ORDERS.ORDER_ID` |
| REVIEW_SCORE | NUMBER(1,0)   | Score (1–5) |
| REVIEW_TEXT  | STRING        | Generated review text |

### H) `INVENTORY_MOVEMENTS`
| Column           | Type           | Description |
|---|---|---|
| MOVEMENT_ID      | STRING         | Movement ID |
| PRODUCT_VARIANT_ID | STRING       | FK → `PRODUCT_VARIANTS.PRODUCT_VARIANT_ID` |
| MOVEMENT_TIME    | TIMESTAMP_TZ   | Movement timestamp |
| QUANTITY_DELTA   | NUMBER(10,0)   | Stock delta (+/-) |
| MOVEMENT_TYPE    | STRING         | `IN`, `OUT`, `SALE`, `RETURN` |
| ORDER_ID         | STRING         | Order reference (if applicable) |
| NOTE             | STRING         | Comment |

### I) `STOCK` View (aggregated)
| Column              | Type           | Description |
|---|---|---|
| PRODUCT_VARIANT_ID  | STRING         | Variant |
| QUANTITY_ON_HAND    | NUMBER(10,0)   | Current stock (sum of movements) |
| LAST_MOVEMENT_TIME  | TIMESTAMP_TZ   | Last movement timestamp |

---

### Keys & Relationships
- **PK:** `CLIENTS.CLIENT_ID`, `PRODUCTS.PRODUCT_ID`, `PRODUCT_VARIANTS.PRODUCT_VARIANT_ID`, `ORDERS.ORDER_ID`, `ORDER_LINES.ORDER_LINE_ID`, `ORDER_STATUS_HISTORY.STATUS_EVENT_ID`, `REVIEWS.REVIEW_ID`, `INVENTORY_MOVEMENTS.MOVEMENT_ID`.  
- **FK:**  
  - `ORDERS.CLIENT_ID` → `CLIENTS.CLIENT_ID`  
  - `ORDER_LINES.ORDER_ID` → `ORDERS.ORDER_ID`  
  - `ORDER_LINES.PRODUCT_VARIANT_ID` → `PRODUCT_VARIANTS.PRODUCT_VARIANT_ID`  
  - `PRODUCT_VARIANTS.PRODUCT_ID` → `PRODUCTS.PRODUCT_ID`  
  - `ORDER_STATUS_HISTORY.ORDER_ID` → `ORDERS.ORDER_ID`  
  - `REVIEWS.ORDER_ID` → `ORDERS.ORDER_ID`  
  - `INVENTORY_MOVEMENTS.PRODUCT_VARIANT_ID` → `PRODUCT_VARIANTS.PRODUCT_VARIANT_ID` (and `ORDER_ID` when linked to a sale/return)


---
## 6) Streamlit Dashboards
Two **Streamlit** apps (Snowpark):

1. `streamlit_app_dashboard_ananalytics.py` — **Business Analytics**
   - KPIs: revenue (TTC/HT/VAT), order count, average basket, refund rate, avg. review.  
   - Time series by granularity (day/week/month/quarter/year).  
   - Products: top variants by revenue, size mix.  
   - Customers: age buckets, sex distribution.  
   - Operations: lead time & SLA, upcoming expirations, low stock.

2. `streamlit_app_dashboard_monitoring.py` — **Monitoring & Quality**
   - Freshness (recent `purchase_time`).  
   - Date coherence, negative amounts, duplicate TXIDs.  
   - Ingestion activity (counters, histories), quick sanity checks.

Both apps read from the logical schema `SALES_DATA.SALES_DATA`.

---

## 7) Run Book
**0) Minimum Grants**
```sql
GRANT USAGE  ON WAREHOUSE SALES_DATA            TO ROLE DATA_ANALYST;
GRANT USAGE  ON DATABASE  SALES_DATA            TO ROLE DATA_ANALYST;
GRANT USAGE  ON SCHEMA    SALES_DATA.SALES_DATA TO ROLE DATA_ANALYST;
GRANT SELECT ON ALL TABLES IN  SCHEMA SALES_DATA.SALES_DATA TO ROLE DATA_ANALYST;
GRANT SELECT ON ALL VIEWS  IN  SCHEMA SALES_DATA.SALES_DATA TO ROLE DATA_ANALYST;
GRANT SELECT ON FUTURE TABLES IN SCHEMA SALES_DATA.SALES_DATA TO ROLE DATA_ANALYST;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA SALES_DATA.SALES_DATA TO ROLE DATA_ANALYST;
```

**1) Create landing table** — see DDL above.  

**2) Ingestion**
- **INSERT:** run `py_insert` (reads JSONL from `stdin`).  
- **Parquet + COPY:** run `file_insert.py` (generate Parquet → `PUT` to `@%CLIENT_SUPPORT_ORDERS_PY_SNOWPIPE` → `COPY INTO ...`).  
- **Snowpipe:** stage files + notification (or `SimpleIngestManager`).

**3) Transformation**
- Run the staging + `MERGE` SQL to populate `CLIENTS`, `PRODUCTS`, `PRODUCT_VARIANTS`, `ORDERS`, `ORDER_LINES`, `ORDER_STATUS_HISTORY`, `REVIEWS`, `INVENTORY_MOVEMENTS`, then create the `STOCK` view.

**4) Launch Streamlit (Snowsight → Projects → Streamlit)**
- Create an app; paste `streamlit_app_dashboard_ananalytics.py` or `..._monitoring.py`.  
- App Settings: Role = `DATA_ANALYST`, Warehouse = `SALES_DATA`, DB/Schema = `SALES_DATA.SALES_DATA`.  
- Optionally set context at startup via Snowpark (`USE ROLE/WAREHOUSE/DATABASE/SCHEMA`).

---

## 8) Security & Governance
- **Access control:** least privilege (USAGE/SELECT for readers; separate ingest role for writes).  
- **Lineage:** clear separation landing → staging → modeled (versioned scripts).  
- **PII:** name/email/address present; production should apply masking/tokenization.

---

## 9) Data Quality & Monitoring
Validated/monitored rules:
- `PRICE >= 0`; `REVIEW_SCORE BETWEEN 1 AND 5`.  
- Temporal coherence: `DELIVERY_DATE > PURCHASE_DATE`, `EXPIRATION_DATE >= DELIVERY_DATE`.  
- Non‑nulls: `TXID`, `ITEM`, `PRICE`, `PURCHASE_TIME`, `EMAIL`, `NAME`, `ADDRESS_*`.  
- Duplicate detection on `TXID`.  
- Snowpipe/loads: history and refresh (usage/latency).

---

## 10) Future Work
- Orchestration with **Streams + Tasks** (automate landing → model).  
- Multi-line orders / promotions / seasonality in the generator.    
- Data contracts & schema registry.
