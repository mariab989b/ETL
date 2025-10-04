/*LBE
Code for Stream and Task Workshop - Student Version
Interactive learning with exercises and questions

INSTRUCTIONS FOR STUDENTS:
==========================

1. PROGRESSIVE DIFFICULTY:
   - Section 1-2: BEGINNER (Basic setup and data ingestion)
   - Section 3-4: INTERMEDIATE (JSON parsing and streams)
   - Section 5-6: ADVANCED (Task orchestration and monitoring)
   - Section 7-8: EXPERT (Complex orchestration and optimization)
   - Section 9-10: MASTER LVL 100 BOSS (Data quality and PII protection)

2. LEARNING APPROACH:
   - Start with Section 1 and work sequentially
   - Each section builds on the previous one
   - Complete all YOUR CODE HERE sections
   - Answer all questions for deeper understanding
   - Use hints when needed - they're there to help!

3. HINTS SYSTEM:
   - All hints and solutions are in a separate file: snowflake_streams_tasks_hints.sql
   - Try to solve exercises first without looking at hints
   - When stuck, check the hints file for the corresponding exercise number
   - Hints are numbered to match exercise numbers (e.g., HINT 1.1, HINT 1.2, etc.)

4. ASSESSMENT:
   - Complete all sections for basic understanding
   - Master sections 1-6 for intermediate level
   - Complete sections 7-10 for advanced level
   - Bonus challenges for expert level

Good luck with your Snowflake learning !
*/

-- ===========================================
-- SECTION 1: SETUP AND PREPARATION (BEGINNER LEVEL)
-- ===========================================

-- Exercise 1.1: Create the necessary role and permissions
-- DIFFICULTY: BEGINNER
-- TODO: Complete the role creation and grant statements below
-- HINTS: Check hints file for HINT 1.1 through HINT 1.5

use role ACCOUNTADMIN;
set myname = current_user();

-- YOUR CODE HERE - Create role Data_ENG
CREATE OR REPLACE ROLE Data_ENG;
-- YOUR CODE HERE - Grant role to current user
GRANT ROLE Data_ENG TO USER IDENTIFIER($myname);
-- YOUR CODE HERE - Grant create database permission
GRANT CREATE DATABASE ON ACCOUNT TO ROLE Data_ENG;
-- YOUR CODE HERE - Grant task execution permissions
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE Data_ENG;
-- YOUR CODE HERE - Grant imported privileges on SNOWFLAKE database
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE Data_ENG;

-- Exercise 1.2: Create warehouse and database
-- DIFFICULTY: BEGINNER
-- TODO: Create a warehouse and database for this lab
-- HINTS: Check hints file for HINT 1.6 through HINT 1.9

-- YOUR CODE HERE - Create warehouse Orchestration_WH (XSMALL, auto-suspend 5 min)
CREATE OR REPLACE WAREHOUSE Orchestration_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;
-- YOUR CODE HERE - Grant warehouse privileges to Data_ENG role
GRANT USAGE ON WAREHOUSE Orchestration_WH TO ROLE Data_ENG;
-- YOUR CODE HERE - Create database Credit_card
CREATE OR REPLACE DATABASE Credit_card;
-- YOUR CODE HERE - Grant database privileges to Data_ENG role
GRANT ALL PRIVILEGES ON DATABASE Credit_card TO TOLE Data_ENG;

-- Switch to the new role and database
use role Data_ENG;
use database Credit_card;
use schema PUBLIC;
use warehouse Orchestration_WH;

-- ===========================================
-- SECTION 2: DATA INGESTION SETUP (BEGINNER LEVEL)
-- ===========================================

-- Exercise 2.1: Create staging infrastructure
-- DIFFICULTY: BEGINNER
-- TODO: Create the necessary objects for data ingestion
-- HINTS: Check hints file for HINT 2.1 through HINT 2.2

-- YOUR CODE HERE - Create internal stage CC_STAGE with JSON file format
CREATE OR REPLACE FILE FORMAT CC_JSON_FORMAT
  TYPE = 'JSON'
  COMPRESSION = 'AUTO';
-- YOUR CODE HERE - Create staging table CC_TRANS_STAGING with VARIANT column
CREATE OR REPLACE TABLE CC_TRANS_STAGING (
  DATA VARIANT,
  LOAD_TIMESTAMP TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP
);
-- Question 2.1: Why do we use a VARIANT column for JSON data?
-- Answer: Because if we need to store data with a flexible schema, VARIANT allows us to store semi-structured data like JSON without predefined columns.

-- Exercise 2.2: Create the data generation stored procedure
-- TODO: This is provided for you - study the Java code to understand how it works

create or replace procedure SIMULATE_KAFKA_STREAM(mystage STRING,prefix STRING,numlines INTEGER)
  RETURNS STRING
  LANGUAGE JAVA
  PACKAGES = ('com.snowflake:snowpark:latest')
  HANDLER = 'StreamDemo.run'
  AS
  $$
    import com.snowflake.snowpark_java.Session;
    import java.io.*;
    import java.util.HashMap;
    public class StreamDemo {
      public String run(Session session, String mystage,String prefix,int numlines) {
        SampleData SD=new SampleData();
        BufferedWriter bw = null;
        File f=null;
        try {
            f = File.createTempFile(prefix, ".json");
            FileWriter fw = new FileWriter(f);
	        bw = new BufferedWriter(fw);
            boolean first=true;
            bw.write("[");
            for(int i=1;i<=numlines;i++){
                if (first) first = false;
                else {bw.write(",");bw.newLine();}
                bw.write(SD.getDataLine(i));
            }
            bw.write("]");
            bw.close();
            return session.file().put(f.getAbsolutePath(),mystage,options)[0].getStatus();
        }
        catch (Exception ex){
            return ex.getMessage();
        }
        finally {
            try{
	            if(bw!=null) bw.close();
                if(f!=null && f.exists()) f.delete();
	        }
            catch(Exception ex){
	            return ("Error in closing:  "+ex);
	        }
        }
      }

      private static final HashMap<String,String> options = new HashMap<String, String>() {
        { put("AUTO_COMPRESS", "TRUE"); }
      };

      public static class SampleData {
      private static final java.util.Random R=new java.util.Random();
      private static final java.text.NumberFormat NF_AMT = java.text.NumberFormat.getInstance();
      String[] transactionType={"PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","REFUND"};
      String[] approved={"true","true","true","true","true","true","true","true","true","true","false"};
      static {
        NF_AMT.setMinimumFractionDigits(2);
        NF_AMT.setMaximumFractionDigits(2);
        NF_AMT.setGroupingUsed(false);
      }

      private static int randomQty(int low, int high){
        return R.nextInt(high-low) + low;
      }

      private static double randomAmount(int low, int high){
        return R.nextDouble()*(high-low) + low;
      }

      private String getDataLine(int rownum){
        StringBuilder sb = new StringBuilder()
            .append("{")
            .append("\"element\":"+rownum+",")
            .append("\"object\":\"basic-card\",")
            .append("\"transaction\":{")
            .append("\"id\":"+(1000000000 + R.nextInt(900000000))+",")
            .append("\"type\":"+"\""+transactionType[R.nextInt(transactionType.length)]+"\",")
            .append("\"amount\":"+NF_AMT.format(randomAmount(1,5000)) +",")
            .append("\"currency\":"+"\"USD\",")
            .append("\"timestamp\":\""+java.time.Instant.now()+"\",")
            .append("\"approved\":"+approved[R.nextInt(approved.length)]+"")
            .append("},")
            .append("\"card\":{")
                .append("\"number\":"+ java.lang.Math.abs(R.nextLong()) +"")
            .append("},")
            .append("\"merchant\":{")
            .append("\"id\":"+(100000000 + R.nextInt(90000000))+"")
            .append("}")
            .append("}");
        return sb.toString();
      }
    }
}
$$;

-- Question 2.2: What does this stored procedure simulate?
-- Answer: It simulates a Kafka stream by generating JSON files with random credit card transactions and storing them in a Snowflake stage.

-- Exercise 2.3: Test data generation
-- DIFFICULTY: BEGINNER
-- TODO: Call the stored procedure and verify the results
-- HINTS: Check hints file for HINT 2.3 through HINT 2.6

-- YOUR CODE HERE - Call SIMULATE_KAFKA_STREAM with appropriate parameters
CALL SIMULATE_KAFKA_STREAM('CC_STAGE','cc_data_',10);
-- YOUR CODE HERE - List files in the stage to verify creation
LIST @CC_STAGE;
-- YOUR CODE HERE - Copy data from stage to staging table
COPY INTO CC
-- YOUR CODE HERE - Check row count in staging table
SELECT COUNT(*) AS ROW_COUNT FROM CC_TRANS_STAGING;

-- ===========================================
-- SECTION 3: JSON DATA EXPLORATION (INTERMEDIATE LEVEL)
-- ===========================================

-- Exercise 3.1: Explore JSON structure
-- DIFFICULTY: INTERMEDIATE
-- TODO: Write queries to explore the JSON data structure

-- YOUR CODE HERE - Select card numbers from the JSON data
SELECT DATA:card.number AS CARD_NUMBER
-- YOUR CODE HERE - Parse and display transaction details (id, amount, currency, approved, type, timestamp)
SELECT 
  DATA:transaction.id AS TRANSACTION_ID,
  DATA:transaction.amount AS AMOUNT,
  DATA:transaction.currency AS CURRENCY,
  DATA:transaction.approved AS APPROVED,
  DATA:transaction.type AS TYPE,
  DATA:transaction.timestamp AS TIMESTAMP
-- YOUR CODE HERE - Filter transactions with amount < 600
SELECT 
  DATA:transaction.id AS TRANSACTION_ID,
  DATA:transaction.amount AS AMOUNT,
  DATA:transaction.currency AS CURRENCY,
  DATA:transaction.approved AS APPROVED,
  DATA:transaction.type AS TYPE,
  DATA:transaction.timestamp AS TIMESTAMP
FROM CC_TRANS_STAGING
WHERE DATA:transaction.amount < 600;
-- Question 3.1: What is the advantage of using VARIANT columns for JSON data?
-- Answer: Thew allow for flexible schema and easy parsing of semi-structured data.

-- Exercise 3.2: Create a normalized view
-- DIFFICULTY: INTERMEDIATE
-- TODO: Create a view that flattens the JSON structure into columns

-- YOUR CODE HERE - Create view CC_TRANS_STAGING_VIEW with proper column mapping
CREATE OR REPLACE VIEW CC_TRANS_STAGING_VIEW AS
SELECT
  DATA:transaction.id::STRING AS TRANSACTION_ID,
  DATA:transaction.amount::FLOAT AS AMOUNT,
  DATA:transaction.currency::STRING AS CURRENCY,
  DATA:transaction.approved::BOOLEAN AS APPROVED,
  DATA:transaction.type::STRING AS TYPE,
  DATA:transaction.timestamp::TIMESTAMP_LTZ AS TIMESTAMP,
  DATA:card.number::STRING AS CARD_NUMBER,
  DATA:merchant.id::STRING AS MERCHANT_ID,
  LOAD_TIMESTAMP  AS LOAD_TIMESTAMP
-- YOUR CODE HERE - Enable change tracking on table and view
ALTER TABLE CC_TRANS_STAGING SET CHANGE_TRACKING = TRUE;
ALTER VIEW CC_TRANS_STAGING_VIEW SET CHANGE_TRACKING = TRUE;
-- YOUR CODE HERE - Test the view with sample queries
SELECT * FROM CC_TRANS_STAGING_VIEW LIMIT 5;
SELECT COUNT(*) AS TOTAL_RECORDS FROM CC_TRANS_STAGING_VIEW;

-- Question 3.2: Why do we need to enable change tracking?
-- Answer: We need to enable change tracking to let streams captures changes made to the table or the view.

-- ===========================================
-- SECTION 4: STREAMS AND CHANGE DATA CAPTURE (INTERMEDIATE LEVEL)
-- ===========================================

-- Exercise 4.1: Create and test streams
-- DIFFICULTY: INTERMEDIATE
-- TODO: Create a stream on the view and explore its behavior

-- YOUR CODE HERE - Create stream CC_TRANS_STAGING_VIEW_STREAM on the view
CREATE OR REPLACE STREAM CC_TRANS_STAGING_VIEW_STREAM ON VIEW CC_TRANS_STAGING_VIEW
  SHOW_INITIAL_ROWS = TRUE;
-- YOUR CODE HERE - Check initial stream content
SELECT * FROM CC_TRANS_STAGING_VIEW_STREAM;
-- YOUR CODE HERE - Generate more data using the stored procedure
CALL SIMULATE_KAFKA_STREAM('CC_STAGE','cc_data_',5);
-- YOUR CODE HERE - Count records in the stream
SELECT COUNT(*) AS STREAM_RECORD_COUNT FROM CC_TRANS_STAGING_VIEW_STREAM;

-- Question 4.1: What does SHOW_INITIAL_ROWS=true do in stream creation?
-- Answer: It allows the stream to capture existing rows in the source object as initial inserts.

-- Exercise 4.2: Create analytical table
-- DIFFICULTY: INTERMEDIATE
-- TODO: Create a normalized table for analytics

-- YOUR CODE HERE - Create table CC_TRANS_ALL with proper schema
CREATE OR REPLACE TABLE CC_TRANS_ALL (
  TRANSACTION_ID STRING,
  AMOUNT FLOAT,
  CURRENCY STRING,
  APPROVED BOOLEAN,
  TYPE STRING,
  TIMESTAMP TIMESTAMP_LTZ,
  CARD_NUMBER STRING,
  MERCHANT_ID STRING,
  LOAD_TIMESTAMP TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP
);
-- YOUR CODE HERE - Insert data from stream into analytical table
INSERT INTO CC_TRANS_ALL
SELECT
  TRANSACTION_ID,
  AMOUNT,
  CURRENCY,
  APPROVED,
  TYPE,
  TIMESTAMP,
  CARD_NUMBER,
  MERCHANT_ID,
  LOAD_TIMESTAMP
-- YOUR CODE HERE - Verify data in analytical table
SELECT COUNT(*) AS ANALYTICAL_TABLE_COUNT FROM CC_TRANS_ALL;

-- Question 4.2: What is the difference between the staging table and analytical table?
-- Answer: The difference is that the staging table holds raw data, while the analytical table holds processed and structured data ready for analysis.

-- ===========================================
-- SECTION 5: TASK ORCHESTRATION (ADVANCED LEVEL)
-- ===========================================

-- Exercise 5.1: Create your first task
-- DIFFICULTY: ADVANCED
-- TODO: Create a task that generates data automatically

-- YOUR CODE HERE - Create task GENERATE_TASK with 1-minute schedule
CREATE OR REPLACE TASK GENERATE_TASK
  WAREHOUSE = Orchestration_WH
  SCHEDULE = '1 MINUTE'
-- YOUR CODE HERE - Describe the task to see its definition
DESC TASK GENERATE_TASK;
-- YOUR CODE HERE - Execute the task manually
EXECUTE TASK GENERATE_TASK;
-- YOUR CODE HERE - Resume the task to run on schedule
ALTER TASK GENERATE_TASK RESUME;

-- Question 5.1: What are the benefits of using tasks vs manual execution?
-- Answer: Tasks allow for automation, scheduling and dependencies, reducing effort and ensuring timely data processing.

-- Exercise 5.2: Create data processing task
-- DIFFICULTY: ADVANCED
-- TODO: Create a task that processes files from stage to staging table

-- YOUR CODE HERE - Create task PROCESS_FILES_TASK with 3-minute schedule
CREATE OR REPLACE TASK PROCESS_FILES_TASK
  WAREHOUSE = Orchestration_WH
  SCHEDULE = '3 MINUTE'
-- YOUR CODE HERE - Execute task manually and verify results  
EXECUTE TASK PROCESS_FILES_TASK;
-- YOUR CODE HERE - Resume the task
ALTER TASK PROCESS_FILES_TASK RESUME;

-- Exercise 5.3: Create data refinement task
-- DIFFICULTY: ADVANCED
-- TODO: Create a task that processes stream data into analytical table

-- YOUR CODE HERE - Create task REFINE_TASK with stream condition
CREATE OR REPLACE TASK REFINE_TASK
  WAREHOUSE = Orchestration_WH
  WHEN SYSTEM$STREAM_HAS_DATA('CC_TRANS_STAGING_VIEW_STREAM')
-- YOUR CODE HERE - Execute task manually and verify results
EXECUTE TASK REFINE_TASK;
-- YOUR CODE HERE - Resume the task
ALTER TASK REFINE_TASK RESUME;

-- Question 5.2: What does SYSTEM$STREAM_HAS_DATA() do?
-- Answer: It checks if there are any new changes in the stream since the last offset.

-- ===========================================
-- SECTION 6: MONITORING AND REPORTING (ADVANCED LEVEL)
-- ===========================================

-- Exercise 6.1: Monitor task execution
-- DIFFICULTY: ADVANCED
-- TODO: Create monitoring queries

-- YOUR CODE HERE - Query load history from INFORMATION_SCHEMA
SELECT * FROM INFORMATION_SCHEMA.LOAD_HISTORY
  WHERE TABLE_NAME = 'CC_TRANS_STAGING'
-- YOUR CODE HERE - Query load history from ACCOUNT_USAGE
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.LOAD_HISTORY
  WHERE TABLE_NAME = 'CC_TRANS_STAGING'
-- YOUR CODE HERE - Check task execution history
SELECT * FROM INFORMATION_SCHEMA.TASK_HISTORY
  WHERE TASK_NAME IN ('GENERATE_TASK', 'PROCESS_FILES_TASK', 'REFINE_TASK')

-- Question 6.1: What is the difference between INFORMATION_SCHEMA and ACCOUNT_USAGE?
-- Answer: INFORMATION_SCHEMA provides metadata for the current database, while ACCOUNT_USAGE provides account-level usage data across all databases.

-- Exercise 6.2: Analyze data flow
-- DIFFICULTY: ADVANCED
-- TODO: Create queries to understand data flow

-- YOUR CODE HERE - Count records in each table (staging, view, stream, analytical)
SELECT 
  (SELECT COUNT(*) FROM CC_TRANS_STAGING) AS STAGING_COUNT,
  (SELECT COUNT(*) FROM CC_TRANS_STAGING_VIEW) AS VIEW_COUNT,
  (SELECT COUNT(*) FROM CC_TRANS_STAGING_VIEW_STREAM) AS STREAM_COUNT,
  (SELECT COUNT(*) FROM CC_TRANS_ALL) AS ANALYTICAL_COUNT;
-- YOUR CODE HERE - Find the latest transaction timestamp
SELECT MAX(TIMESTAMP) AS LATEST_TRANSACTION FROM CC_TRANS_ALL;
-- YOUR CODE HERE - Analyze transaction patterns (approved vs rejected)
SELECT APPROVED, COUNT(*) AS COUNT FROM CC_TRANS_ALL
  GROUP BY APPROVED;

-- ===========================================
-- SECTION 7: ADVANCED ORCHESTRATION (EXPERT LEVEL)
-- ===========================================

-- Exercise 7.1: Create task dependencies
-- DIFFICULTY: EXPERT
-- TODO: Create a sequential task pipeline

-- YOUR CODE HERE - Create tasks for pipeline 2
CREATE OR REPLACE TASK PIPELINE_TASK_1
  WAREHOUSE = Orchestration_WH
  SCHEDULE = '5 MINUTE'
-- YOUR CODE HERE - Set up task dependencies using ALTER TASK ... ADD AFTER
ALTER TASK PIPELINE_TASK_1 ADD AFTER GENERATE_TASK;
-- YOUR CODE HERE - Create a root task that triggers the pipeline
CREATE OR REPLACE TASK ROOT_TASK
  WAREHOUSE = Orchestration_WH
  SCHEDULE = '10 MINUTE'
-- Question 7.1: How do task dependencies work in Snowflake?
-- Answer: Task dependencies allow tasks to be executed in a specific order based on the completion of other tasks.

-- Exercise 7.2: Parallel processing
-- DIFFICULTY: EXPERT
-- TODO: Create tasks that can run in parallel

-- YOUR CODE HERE - Create a wait task for parallel processing
CREATE OR REPLACE TASK WAIT_TASK
  WAREHOUSE = Orchestration_WH
  SCHEDULE = '5 MINUTE'
-- YOUR CODE HERE - Set up parallel task execution
ALTER TASK WAIT_TASK ADD AFTER GENERATE_TASK;
-- YOUR CODE HERE - Monitor task dependencies
SELECT * FROM INFORMATION_SCHEMA.TASK_DEPENDENCIES
  WHERE TASK_NAME IN ('WAIT_TASK', 'PIPELINE_TASK_1', 'ROOT_TASK');

-- ===========================================
-- SECTION 8: CLEANUP AND BEST PRACTICES (EXPERT LEVEL)
-- ===========================================

-- Exercise 8.1: Task management
-- DIFFICULTY: EXPERT
-- TODO: Properly manage task lifecycle

-- YOUR CODE HERE - Suspend all running tasks
ALTER TASK GENERATE_TASK SUSPEND;
ALTER TASK PROCESS_FILES_TASK SUSPEND;
ALTER TASK REFINE_TASK SUSPEND;
ALTER TASK PIPELINE_TASK_1 SUSPEND;
ALTER TASK WAIT_TASK SUSPEND;
ALTER TASK ROOT_TASK SUSPEND;
-- YOUR CODE HERE - Show all tasks and their states
SHOW TASKS;
-- YOUR CODE HERE - Create a cleanup script
CREATE OR REPLACE PROCEDURE CLEANUP_ENVIRONMENT()
  RETURNS STRING
  LANGUAGE SQL
  EXECUTE AS CALLER
AS
$$
BEGIN
  -- Suspend all tasks
  ALTER TASK IF EXISTS GENERATE_TASK SUSPEND;
  ALTER TASK IF EXISTS PROCESS_FILES_TASK SUSPEND;
  ALTER TASK IF EXISTS REFINE_TASK SUSPEND;
  ALTER TASK IF EXISTS PIPELINE_TASK_1 SUSPEND;
  ALTER TASK IF EXISTS WAIT_TASK SUSPEND;
  ALTER TASK IF EXISTS ROOT_TASK SUSPEND;

  -- Drop tasks
  DROP TASK IF EXISTS ROOT_TASK;
  DROP TASK IF EXISTS WAIT_TASK;
  DROP TASK IF EXISTS PIPELINE_TASK_1;
  DROP TASK IF EXISTS REFINE_TASK;
  DROP TASK IF EXISTS PROCESS_FILES_TASK;
  DROP TASK IF EXISTS GENERATE_TASK;

  -- Drop streams
  DROP STREAM IF EXISTS CC_TRANS_STAGING_VIEW_STREAM;

  -- Drop views
  DROP VIEW IF EXISTS CC_TRANS_STAGING_VIEW;

  -- Drop tables
  DROP TABLE IF EXISTS CC_TRANS_ALL;
  DROP TABLE IF EXISTS CC_TRANS_STAGING;

  -- Drop file format and stage
  DROP FILE FORMAT IF EXISTS CC_JSON_FORMAT;
  DROP STAGE IF EXISTS CC_STAGE;

  RETURN 'Environment cleanup completed successfully';
END;
$$;


-- Question 8.1: Why is it important to suspend tasks when not needed?
-- Answer: To avoid unnecessary compute costs and resources usage

-- Exercise 8.2: Performance analysis
-- DIFFICULTY: EXPERT
-- TODO: Analyze the performance of your pipeline

-- YOUR CODE HERE - Calculate total processing time
SELECT 
  TASK_NAME,
  START_TIME,
  END_TIME,
  DATEDIFF('second', START_TIME, END_TIME) AS DURATION_SECONDS
FROM INFORMATION_SCHEMA.TASK_HISTORY
  WHERE TASK_NAME IN ('GENERATE_TASK', 'PROCESS_FILES_TASK', 'REFINE_TASK')
  ORDER BY START_TIME DESC;
-- YOUR CODE HERE - Analyze data volume processed
SELECT 
  TASK_NAME,
  SUM(ROWS_PROCESSED) AS TOTAL_ROWS_PROCESSED
FROM INFORMATION_SCHEMA.TASK_HISTORY
  WHERE TASK_NAME IN ('GENERATE_TASK', 'PROCESS_FILES_TASK', 'REFINE_TASK')
  GROUP BY TASK_NAME;
-- YOUR CODE HERE - Identify potential bottlenecks
SELECT 
  TASK_NAME,
  AVG(DATEDIFF('second', START_TIME, END_TIME)) AS AVG_DURATION_SECONDS
FROM INFORMATION_SCHEMA.TASK_HISTORY
  WHERE TASK_NAME IN ('GENERATE_TASK', 'PROCESS_FILES_TASK', 'REFINE_TASK')
  GROUP BY TASK_NAME
  ORDER BY AVG_DURATION_SECONDS DESC;

-- ===========================================
-- SECTION 9: COMPREHENSIVE DATA QUALITY CHECKS (MASTER LEVEL)
-- ===========================================

-- Exercise 9.1: Basic data quality validation
-- DIFFICULTY: INTERMEDIATE
-- TODO: Implement comprehensive data quality checks

-- YOUR CODE HERE - Check for duplicate transactions
SELECT TRANSACTION_ID, COUNT(*) AS DUPLICATE_COUNT  FROM CC_TRANS_ALL
  GROUP BY TRANSACTION_ID
  HAVING COUNT(*) > 1;
-- YOUR CODE HERE - Validate data types and ranges
SELECT * FROM CC_TRANS_ALL
  WHERE AMOUNT < 0 OR AMOUNT > 10000;
-- YOUR CODE HERE - Check for missing values
SELECT * FROM CC_TRANS_ALL
  WHERE TRANSACTION_ID IS NULL OR CARD_NUMBER IS NULL OR MERCHANT_ID IS NULL;
-- YOUR CODE HERE - Validate card number format
SELECT * FROM CC_TRANS_ALL
  WHERE CARD_NUMBER NOT RLIKE '^[0-9]{13,19}$';
-- YOUR CODE HERE - Check for data anomalies
SELECT * FROM CC_TRANS_ALL
  WHERE APPROVED = FALSE AND TYPE = 'PURCHASE';

-- Exercise 9.2: Advanced data quality metrics
-- DIFFICULTY: ADVANCED
-- TODO: Create comprehensive data quality dashboard

-- YOUR CODE HERE - Create data quality metrics table
CREATE OR REPLACE TABLE DATA_QUALITY_METRICS (
  METRIC_NAME STRING,
  METRIC_VALUE FLOAT,
  LAST_UPDATED TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP
);
-- YOUR CODE HERE - Calculate completeness metrics
INSERT INTO DATA_QUALITY_METRICS (METRIC_NAME, METRIC_VALUE)
SELECT 'COMPLETENESS',
  1.0 - (COUNT(*) FILTER (WHERE TRANSACTION_ID IS NULL OR CARD_NUMBER IS NULL OR MERCHANT_ID IS NULL) * 1.0 / COUNT(*))
FROM CC_TRANS_ALL;
-- YOUR CODE HERE - Calculate validity metrics
INSERT INTO DATA_QUALITY_METRICS (METRIC_NAME, METRIC_VALUE)
SELECT 'VALIDITY',
  1.0 - (COUNT(*) FILTER (WHERE AMOUNT < 0 OR AMOUNT > 10000 OR CARD_NUMBER NOT RLIKE '^[0-9]{13,19}$') * 1.0 / COUNT(*))
FROM CC_TRANS_ALL;
-- YOUR CODE HERE - Calculate consistency metrics
INSERT INTO DATA_QUALITY_METRICS (METRIC_NAME, METRIC_VALUE)
SELECT 'CONSISTENCY',
  1.0 - (COUNT(*) FILTER (WHERE APPROVED = FALSE AND TYPE = 'PURCHASE') * 1.0 / COUNT(*))
FROM CC_TRANS_ALL;
-- YOUR CODE HERE - Create data quality dashboard
SELECT * FROM DATA_QUALITY_METRICS;

-- Exercise 9.3: Data quality monitoring and alerting
-- DIFFICULTY: EXPERT
-- TODO: Implement automated data quality monitoring

-- YOUR CODE HERE - Create data quality monitoring procedure
CREATE OR REPLACE PROCEDURE MONITOR_DATA_QUALITY()
  RETURNS STRING
  LANGUAGE SQL
  EXECUTE AS CALLER
AS
$$
DECLARE
  completeness FLOAT;
  validity FLOAT;
  consistency FLOAT;
BEGIN
  SELECT METRIC_VALUE INTO completeness FROM DATA_QUALITY_METRICS WHERE METRIC_NAME = 'COMPLETENESS';
  SELECT METRIC_VALUE INTO validity FROM DATA_QUALITY_METRICS WHERE METRIC_NAME = 'VALIDITY';
  SELECT METRIC_VALUE INTO consistency FROM DATA_QUALITY_METRICS WHERE METRIC_NAME = 'CONSISTENCY';
-- YOUR CODE HERE - Create automated quality check task
  IF completeness < 0.95 OR validity < 0.95 OR consistency < 0.95 THEN
    RETURN 'ALERT: Data quality metrics below threshold - Completeness: ' || completeness || ', Validity: ' || validity || ', Consistency: ' || consistency;
  ELSE
    RETURN 'Data quality metrics are within acceptable range.';
  END IF;
END;
$$;
-- YOUR CODE HERE - Schedule the monitoring task
CREATE OR REPLACE TASK DATA_QUALITY_MONITOR_TASK
  WAREHOUSE = Orchestration_WH
  SCHEDULE = '15 MINUTE'
  AS CALL MONITOR_DATA_QUALITY();
-- YOUR CODE HERE - Implement quality alerting system
ALTER TASK DATA_QUALITY_MONITOR_TASK RESUME;
-- YOUR CODE HERE - Create quality trend analysis
SELECT * FROM DATA_QUALITY_METRICS
  ORDER BY LAST_UPDATED DESC;

-- ===========================================
-- SECTION 10: PII PROTECTION AND DATA MASKING (MASTER LEVEL)
-- ===========================================

-- Exercise 10.1: Identify PII in credit card data
-- DIFFICULTY: INTERMEDIATE
-- TODO: Identify and categorize PII fields

-- YOUR CODE HERE - Identify PII fields in the data
-- YOUR CODE HERE - Create PII classification table
CREATE OR REPLACE TABLE PII_CLASSIFICATION (
  FIELD_NAME STRING,
  SENSITIVITY_LEVEL STRING,
  MASKING_REQUIRED BOOLEAN
);
-- YOUR CODE HERE - Classify all fields by sensitivity
INSERT INTO PII_CLASSIFICATION (FIELD_NAME, SENSITIVITY_LEVEL, MASKING_REQUIRED) VALUES
  ('CARD_NUMBER', 'HIGH', TRUE),
  ('TRANSACTION_ID', 'LOW', FALSE),
  ('AMOUNT', 'LOW', FALSE),
  ('CURRENCY', 'LOW', FALSE),
  ('APPROVED', 'LOW', FALSE),
  ('TYPE', 'LOW', FALSE),
  ('TIMESTAMP', 'MEDIUM', TRUE),
  ('MERCHANT_ID', 'LOW', FALSE);
-- YOUR CODE HERE - Determine masking requirements
SELECT * FROM PII_CLASSIFICATION;

-- Exercise 10.2: Implement data masking for PII
-- DIFFICULTY: ADVANCED
-- TODO: Create masked views for different user roles

-- YOUR CODE HERE - Create masked view for analysts
CREATE OR REPLACE VIEW CC_TRANS_ANALYST_VIEW AS
SELECT
  TRANSACTION_ID,
  AMOUNT,
  CURRENCY,
  APPROVED,
  TYPE,
  TIMESTAMP,
  'XXXX-XXXX-XXXX-' || RIGHT(CARD_NUMBER, 4) AS CARD_NUMBER,
  MERCHANT_ID
FROM CC_TRANS_ALL;
-- YOUR CODE HERE - Create masked view for auditors
CREATE OR REPLACE VIEW CC_TRANS_AUDITOR_VIEW AS
SELECT
  TRANSACTION_ID,
  AMOUNT,
  CURRENCY,
  APPROVED,
  TYPE,
  TIMESTAMP,
  'MASKED' AS CARD_NUMBER,
  MERCHANT_ID
FROM CC_TRANS_ALL;
-- YOUR CODE HERE - Implement role-based access control
GRANT SELECT ON CC_TRANS_ANALYST_VIEW TO ROLE ANALYST_ROLE;
-- YOUR CODE HERE - Test masking effectiveness
GRANT SELECT ON CC_TRANS_AUDITOR_VIEW TO ROLE AUDITOR_ROLE;


-- Exercise 10.3: Advanced PII protection strategies
-- DIFFICULTY: EXPERT
-- TODO: Implement advanced PII protection mechanisms

-- YOUR CODE HERE - Create dynamic masking policy
CREATE OR REPLACE MASKING POLICY CARD_NUMBER_MASKING_POLICY
  AS (VAL STRING) 
  RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('ANALYST_ROLE') THEN 'XXXX-XXXX-XXXX-' || RIGHT(VAL, 4)
      WHEN CURRENT_ROLE() IN ('AUDITOR_ROLE') THEN 'MASKED'
      ELSE 'REDACTED'
    END;
-- YOUR CODE HERE - Apply masking to sensitive columns
ALTER TABLE CC_TRANS_ALL
  MODIFY COLUMN CARD_NUMBER SET MASKING POLICY CARD_NUMBER_MASKING_POLICY;
-- YOUR CODE HERE - Implement data retention policy
CREATE OR REPLACE PROCEDURE IMPLEMENT_RETENTION_POLICY()
  RETURNS STRING
  LANGUAGE SQL
  EXECUTE AS CALLER
AS
$$
BEGIN
  -- Delete transactions older than 90 days
  DELETE FROM CC_TRANS_ALL 
  WHERE TIMESTAMP < DATEADD('day', -90, CURRENT_TIMESTAMP());
  
  -- Archive deleted records to a separate table
  CREATE TABLE IF NOT EXISTS CC_TRANS_ARCHIVE AS 
  SELECT * FROM CC_TRANS_ALL WHERE 1=0;
  
  INSERT INTO CC_TRANS_ARCHIVE
  SELECT * FROM CC_TRANS_ALL 
  WHERE TIMESTAMP < DATEADD('day', -90, CURRENT_TIMESTAMP());
  
  -- Create task to run retention policy daily
  CREATE OR REPLACE TASK RETENTION_POLICY_TASK
    WAREHOUSE = Orchestration_WH
    SCHEDULE = 'USING CRON 0 0 * * *'  -- Run daily at midnight
    AS CALL IMPLEMENT_RETENTION_POLICY();
    
  RETURN 'Retention policy implemented successfully';
END;
$$;
-- YOUR CODE HERE - Create data anonymization procedure
CREATE OR REPLACE PROCEDURE ANONYMIZE_PII_DATA()
  RETURNS STRING
  LANGUAGE SQL
  EXECUTE AS CALLER
AS
$$
BEGIN
  -- Create anonymized table if it doesn't exist
  CREATE TABLE IF NOT EXISTS CC_TRANS_ANONYMIZED AS 
  SELECT * FROM CC_TRANS_ALL WHERE 1=0;

  -- Insert anonymized data
  INSERT INTO CC_TRANS_ANONYMIZED
  SELECT 
    SHA2(TRANSACTION_ID) AS TRANSACTION_ID,
    ROUND(AMOUNT, -1) AS AMOUNT, -- Round to nearest 10
    CURRENCY,
    APPROVED,
    TYPE,
    DATE_TRUNC('HOUR', TIMESTAMP) AS TIMESTAMP, -- Remove minutes/seconds
    CONCAT('ANON-', RIGHT(CARD_NUMBER, 4)) AS CARD_NUMBER,
    SHA2(MERCHANT_ID) AS MERCHANT_ID,
    LOAD_TIMESTAMP
  FROM CC_TRANS_ALL;

  RETURN 'Data anonymization completed successfully';
END;
$$;
-- YOUR CODE HERE - Test PII protection mechanisms
CALL ANONYMIZE_PII_DATA();

-- Question 10.1: What are the key principles of PII protection in data systems?
-- Answer: Minimisation, purpose limitation, data accuracy, storage limitation, integrity and confidentiality

-- Question 10.2: How would you implement GDPR compliance for this credit card data?
-- Answer: Implement data subject rights, data protection by design, data breach notification, appoint a DPO, and ensure lawful basis for processing.

-- Question 10.3: What are the trade-offs between data utility and privacy protection?
-- Answer: Higher privacy protection can reduce data utility by limiting access to sensitive information, while higher data utility can increase privacy risks.

-- ===========================================
-- BONUS CHALLENGES
-- ===========================================

-- Challenge 1: Dagster integration
-- DIFFICULTY: EXPERT
-- Implements Dagster orchestration for the credit card pipeline

-- First create a Snowflake integration user and role
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE ROLE DAGSTER_ROLE;
CREATE OR REPLACE USER DAGSTER_USER
  PASSWORD = '<your_secure_password>'
  DEFAULT_ROLE = DAGSTER_ROLE;

-- Grant necessary privileges
GRANT ROLE DAGSTER_ROLE TO USER DAGSTER_USER;
GRANT USAGE ON WAREHOUSE Orchestration_WH TO ROLE DAGSTER_ROLE;
GRANT USAGE ON DATABASE Credit_card TO ROLE DAGSTER_ROLE;
GRANT USAGE ON SCHEMA Credit_card.PUBLIC TO ROLE DAGSTER_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA Credit_card.PUBLIC TO ROLE DAGSTER_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA Credit_card.PUBLIC TO ROLE DAGSTER_ROLE;

-- Create stored procedure for Dagster to call
CREATE OR REPLACE PROCEDURE DAGSTER_PIPELINE()
  RETURNS STRING
  LANGUAGE SQL
  EXECUTE AS CALLER
AS
$$
BEGIN
  -- Generate new data
  CALL SIMULATE_KAFKA_STREAM('CC_STAGE','cc_data_',10);
  
  -- Process files
  COPY INTO CC_TRANS_STAGING FROM @CC_STAGE
    FILE_FORMAT = CC_JSON_FORMAT
    ON_ERROR = 'CONTINUE';
    
  -- Process stream data
  INSERT INTO CC_TRANS_ALL
  SELECT * FROM CC_TRANS_STAGING_VIEW_STREAM;
  
  RETURN 'Pipeline executed successfully';
END;
$$;

-- Grant execute permission
GRANT USAGE ON PROCEDURE DAGSTER_PIPELINE() TO ROLE DAGSTER_ROLE;

/* 
Note: The following Python code would go in your Dagster project:

from dagster import job, op, schedule
from dagster_snowflake import SnowflakeResource

@op
def run_snowflake_pipeline(context, snowflake):
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CALL DAGSTER_PIPELINE()")
        return cursor.fetchone()[0]

@job(resource_defs={"snowflake": SnowflakeResource})
def credit_card_pipeline():
    run_snowflake_pipeline()

@schedule(
    cron_schedule="*/10 * * * *",  # Runs every 10 minutes
    job=credit_card_pipeline,
    execution_timezone="UTC")
def credit_card_schedule():
    return {}
*/


-- Challenge 2: Implement data partitioning
-- TODO: Add partitioning to improve query performance
CREATE OR REPLACE TABLE CC_TRANS_ALL (
  TRANSACTION_ID STRING,
  AMOUNT FLOAT,
  CURRENCY STRING,
  APPROVED BOOLEAN,
  TYPE STRING,
  TIMESTAMP TIMESTAMP_LTZ,
  CARD_NUMBER STRING,
  MERCHANT_ID STRING,
  LOAD_TIMESTAMP TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP
)
CLUSTER BY (TIMESTAMP);


-- Challenge 3: Create a data lineage tracking system
-- TODO: Track data flow from source to analytics
CREATE OR REPLACE TABLE DATA_LINEAGE (
  STEP_ID STRING,
  STEP_NAME STRING,
  INPUT_SOURCE STRING,
  OUTPUT_DESTINATION STRING,
  TIMESTAMP TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP
);

-- Challenge 4: Implement real-time alerting
-- TODO: Create alerts for data anomalies
CREATE OR REPLACE PROCEDURE ALERT_ON_ANOMALIES()
  RETURNS STRING
  LANGUAGE SQL
  EXECUTE AS CALLER
AS
$$
DECLARE
  anomaly_count INT;
BEGIN
  SELECT COUNT(*) INTO anomaly_count FROM CC_TRANS_ALL
  WHERE APPROVED = FALSE AND TYPE = 'PURCHASE';

-- Challenge 5: Optimize for cost
-- TODO: Implement cost optimization strategies
  IF anomaly_count > 10 THEN
    RETURN 'ALERT: High number of anomalies detected - ' || anomaly_count;
  ELSE
    RETURN 'No anomalies detected.';
  END IF;
END;
$$;
GRANT USAGE ON PROCEDURE ALERT_ON_ANOMALIES() TO ROLE Data_ENG;

-- ===========================================
-- LAB COMPLETION CHECKLIST
-- ===========================================

-- □ Created all necessary roles and permissions
-- □ Set up warehouse and database
-- □ Created staging infrastructure
-- □ Implemented data generation procedure
-- □ Created and tested streams
-- □ Built analytical tables
-- □ Created and configured tasks
-- □ Implemented task orchestration
-- □ Set up monitoring and reporting
-- □ Understood data flow and dependencies
-- □ Implemented proper cleanup procedures
-- □ Completed all exercises and questions
-- □ Attempted bonus challenges

-- Congratulations! You have completed the Snowflake Streams and Tasks workshop!
-- You now understand how to build real-time data pipelines using Snowflake's
-- streaming and orchestration capabilities.
