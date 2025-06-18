from google.cloud import bigquery

client = bigquery.Client()
query = "SELECT 1 AS test_col"
query_job = client.query(query)
results = query_job.result()
for row in results:
    print(row)