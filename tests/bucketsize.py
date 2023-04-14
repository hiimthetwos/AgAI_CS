import boto3

# bucket_name = "agaicamstorage"
bucket_name = "agaidata"

# Create an S3 client
s3 = boto3.client('s3')

# Get the size of the bucket
response = s3.list_objects_v2(Bucket=bucket_name)

total_size = 0

for obj in response.get('Contents', []):
    total_size += obj['Size']

print(f"Bucket {bucket_name} size: {total_size / 1024 / 1024:.2f} MB")
