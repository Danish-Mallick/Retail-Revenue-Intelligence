-- PostgreSQL 14+. Start with the USER-SUPPLIED 13-column filtered extract.
-- psql from the repository root:
--   \i sql/00_schema_and_date_repair.sql
-- Note: this does NOT reconstruct cancellations / missing-customer transactions
-- absent from the uploaded extract.
CREATE SCHEMA IF NOT EXISTS retail;
DROP VIEW IF EXISTS retail.lines CASCADE;
DROP TABLE IF EXISTS retail.raw_extract CASCADE;
CREATE TABLE retail.raw_extract (
    invoice_no BIGINT, stock_code TEXT, description TEXT, quantity INTEGER,
    unit_price NUMERIC(14,2), customer_id BIGINT, country TEXT,
    invoice_date_text TEXT, original_year INTEGER, original_month INTEGER,
    original_week INTEGER, original_day INTEGER, original_weekday INTEGER
);
-- Copy is a psql command, run from the root folder after placing the input at data/raw/Online Retail.csv.
\copy retail.raw_extract FROM 'data/raw/Online Retail.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE VIEW retail.lines AS
WITH parse AS (
    SELECT r.*, r.invoice_date_text::timestamp AS parsed_ts
    FROM retail.raw_extract AS r
), corrected AS (
    SELECT p.*,
       CASE WHEN EXTRACT(MONTH FROM parsed_ts) <= 12
                 AND EXTRACT(DAY FROM parsed_ts) <= 12
                 AND EXTRACT(MONTH FROM parsed_ts) <> EXTRACT(DAY FROM parsed_ts)
            THEN MAKE_TIMESTAMP(
                EXTRACT(YEAR FROM parsed_ts)::int,
                EXTRACT(DAY FROM parsed_ts)::int,
                EXTRACT(MONTH FROM parsed_ts)::int,
                EXTRACT(HOUR FROM parsed_ts)::int,
                EXTRACT(MINUTE FROM parsed_ts)::int,
                EXTRACT(SECOND FROM parsed_ts)::double precision)
            ELSE parsed_ts END AS fixed_date
    FROM parse p
)
SELECT invoice_no, stock_code, description, quantity, unit_price,
       customer_id, country, invoice_date_text, parsed_ts,
       fixed_date AS invoice_date, DATE_TRUNC('month', fixed_date)::date AS invoice_month,
       quantity*unit_price AS revenue
FROM corrected;
