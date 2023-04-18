import boto3
import time
import os
import pika

bucket_name = "agaicamstorage"
new_bucket_name = "agaidata"
local_folder = "/tmp/downloadtest/"
source_folder = "collected"
destination_folder = "stored"

# RabbitMQ settings
rabbitmq_host = "mission"  # Replace with your RabbitMQ host
queue_name = "file_queue"

# Create an S3 client
s3 = boto3.client("s3")

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()

# Declare a RabbitMQ queue
channel.queue_declare(queue=queue_name)

def list_files_in_folder(bucket, folder):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=folder + "/")
    if "Contents" in response:
        return [obj["Key"] for obj in response["Contents"] if obj["Key"] != folder + "/"]
    else:
        return []

def move_file_to_new_bucket(src_bucket, src_key, dst_bucket, dst_key):
    # Copy the file to the new location
    s3.copy_object(Bucket=dst_bucket, CopySource={"Bucket": src_bucket, "Key": src_key}, Key=dst_key)
    
    # Delete the file from the original location
    s3.delete_object(Bucket=src_bucket, Key=src_key)

while True:
    files = list_files_in_folder(bucket_name, source_folder)

    if files:
        for file_key in files:
            # Download the file from S3
            local_file_name = os.path.basename(file_key)
            local_file_path = os.path.join(local_folder, local_file_name)
            s3.download_file(bucket_name, file_key, local_file_path)

            # Wait for the file to finish downloading
            while not os.path.exists(local_file_path):
                time.sleep(1)

            print(f"Downloaded {file_key} to {local_file_path}")

            # Move the file to the new S3 bucket
            destination_key = file_key.replace(source_folder, destination_folder)
            move_file_to_new_bucket(bucket_name, file_key, new_bucket_name, destination_key)

            # Publish the local file path to the RabbitMQ queue
            channel.basic_publish(exchange="", routing_key=queue_name, body=local_file_path)
            print(f"Published {local_file_path} to the RabbitMQ queue")

    # Wait for some time before checking again
    time.sleep(5)  # Adjust the sleep interval as needed

# Close the RabbitMQ connection
connection.close()
