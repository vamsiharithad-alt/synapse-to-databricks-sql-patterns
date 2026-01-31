# =============================================================================
# UTILITY SCRIPT: Raw Data Ingestion
# Purpose: Handles complex file formats (CSV/JSON) that SQL cannot read directly.
# Strategy: "Read in Python -> Expose to SQL"
# =============================================================================

from pyspark.sql.functions import current_timestamp

# 1. READ: Load the raw file using standard PySpark options
# (This handles headers, schemas, and messy formats better than SQL COPY INTO)
raw_df = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load("/mnt/landing_zone/incoming_sales_data.csv")

# 2. REGISTER: Create a Temporary View
# This is the "Bridge." Now, the rest of the logic can be written in pure SQL.
raw_df.createOrReplaceTempView("raw_sales_staging")

print("Success: 'raw_sales_staging' is now available for SQL querying.")

# 3. WRITE (Optional): If we just want to save it directly as a Delta table
# raw_df.write.format("delta").mode("append").saveAsTable("bronze.raw_sales")