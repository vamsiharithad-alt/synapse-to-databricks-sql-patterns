Markdown
# Synapse T-SQL to Databricks Spark SQL Migration Guide

## Overview
This repository serves as a reference guide for migrating legacy **Azure Synapse (T-SQL)** workloads to **Databricks (Spark SQL)**.

As a Data Engineer specializing in modern cloud migrations, I have documented common patterns, syntax changes, and performance optimization techniques required when moving from a traditional Data Warehouse to a Lakehouse architecture.

---

## 1. Syntax Differences: The "Gotchas"

### limiting Rows
Synapse uses `TOP` at the start of the query. Databricks uses `LIMIT` at the end.

**Synapse (T-SQL):**
```sql
SELECT TOP 10 * FROM Sales.Orders 
ORDER BY OrderDate DESC;
Databricks (Spark SQL):

SQL
SELECT * FROM Sales.Orders 
ORDER BY OrderDate DESC
LIMIT 10;
Date Functions
Date math syntax differs slightly. Synapse uses DATEADD; Spark SQL uses interval syntax or specific functions.

Synapse (T-SQL):

SQL
SELECT DATEADD(day, -7, GETDATE()) AS LastWeek;
Databricks (Spark SQL):

SQL
-- Option 1: Interval (Preferred)
SELECT current_date() - INTERVAL 7 DAYS AS LastWeek;

-- Option 2: Function
SELECT date_add(current_date(), -7) AS LastWeek;
Dealing with NULLs in Strings
In T-SQL, concatenating a NULL often yields a NULL. In Spark SQL, concat can sometimes handle it differently, but concat_ws (With Separator) is safer for skipping nulls.

Databricks (Spark SQL):

SQL
-- Skips null values automatically
SELECT concat_ws('-', FirstName, LastName, MiddleName) FROM Customers;
2. Converting Stored Procedure Logic
Synapse Procedures often rely heavily on variables (DECLARE @MyVar). In Databricks Notebooks, we handle this using Widgets or Session Variables.

Pattern: Dynamic Filtering
Synapse (Legacy):

SQL
DECLARE @RegionName VARCHAR(50) = 'APAC';
SELECT * FROM Sales WHERE Region = @RegionName;
Databricks (Modern):

SQL
-- Step 1: Create a widget for user input (at the top of the notebook)
CREATE WIDGET TEXT RegionName DEFAULT 'APAC';

-- Step 2: Use the widget value in standard SQL
SELECT * FROM Sales WHERE Region = getArgument("RegionName");
3. The "UPSERT" Pattern (MERGE)
Databricks fully supports ANSI standard MERGE INTO, which is critical for migrating Type 1 and Type 2 SCD logic from Synapse.

Spark SQL Pattern:

SQL
MERGE INTO silver_sales AS target
USING updates_view AS source
ON target.SalesID = source.SalesID
WHEN MATCHED THEN
  UPDATE SET 
    target.Amount = source.Amount,
    target.UpdatedDate = current_timestamp()
WHEN NOT MATCHED THEN
  INSERT (SalesID, Amount, UpdatedDate) 
  VALUES (source.SalesID, source.Amount, current_timestamp());
4. Performance Optimization (The "Senior" Section)
In Synapse, performance is managed via Distribution Keys and Clustered Indexes. In Databricks, we use Delta Lake Optimization.

Replacing Indexes
Synapse Concept: CREATE CLUSTERED COLUMNSTORE INDEX...

Databricks Replacement (Z-Order): Z-Ordering collocates related information in the same set of files, dramatically speeding up queries that filter by these columns.

SQL
-- Run this after major data loads
OPTIMIZE sales_orders 
ZORDER BY (CustomerID, OrderDate);
Partitioning
For tables larger than 1TB, we replace Synapse Round-Robin/Hash distribution with directory-based partitioning.

SQL
CREATE TABLE sales_orders (
  OrderID INT,
  OrderDate DATE,
  ...
)
USING DELTA
PARTITIONED BY (OrderDate); -- Physical folder separation
5. The "Python Bridge" (Handling Flat Files)
Sometimes SQL cannot easily read a complex raw file. In these cases, I use a lightweight PySpark "wrapper" to load the data into a Temporary View, allowing the rest of the logic to remain in SQL.

Python
# %python block in Databricks Notebook
# 1. Read the raw file with specific options
df = spark.read.format("csv") \
  .option("header", "true") \
  .option("inferSchema", "true") \
  .load("/mnt/raw/sales_dump.csv")

# 2. Register as a Temp View so SQL can see it
df.createOrReplaceTempView("raw_sales_view")
SQL
-- Now we can switch back to SQL immediately
SELECT * FROM raw_sales_view WHERE Amount > 1000;