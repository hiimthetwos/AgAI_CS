import boto3
from botocore.exceptions import ClientError

def upload_file_to_minio(file_path, bucket_name, object_name):
    minio_endpoint = "http://66.175.223.220:9000"
    access_key = "user"
    secret_key = "password"

    session = boto3.session.Session()
    client = session.client(
        "s3",
        endpoint_url=minio_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=boto3.session.Config(signature_version="s3v4"),
    )

    try:
        # Check if the bucket exists
        try:
            client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                client.create_bucket(Bucket=bucket_name)

        # Upload the file
        with open(file_path, "rb") as file:
            client.upload_fileobj(file, bucket_name, object_name)

        print(f"File '{file_path}' uploaded to MinIO as '{object_name}' in bucket '{bucket_name}'")

    except ClientError as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    file_path = "/home/ryanbert/code/AgAI_CS/tests/file.txt"
    bucket_name = "my-bucket"
    object_name = "file.txt"

    upload_file_to_minio(file_path, bucket_name, object_name)

