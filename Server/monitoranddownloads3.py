import boto3
import time
import os

bucket_name = "agaicamstorage"
new_bucket_name = "agaidata"
local_folder = "/tmp/downloadtest/"
source_folder = "uploaded"
destination_folder = "stored"

# Create an S3 client
s3 = boto3.client("s3")

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
            print(f"File {file_key} found in {source_folder} folder")
            # Download the file
            local_file_path = f"{local_folder}{os.path.basename(file_key)}"
            s3.download_file(bucket_name, file_key, local_file_path)

            # Extract file details from the file name
            file_name = os.path.basename(file_key)
            file_parts = file_name.split("-")
            client_id, camera_id, date_part, time_part = file_parts[0], file_parts[1], file_parts[2][:8], file_parts[2][8:]
            year, month, day = date_part[:4], date_part[4:6], date_part[6:8]

            # Move the file to the destination bucket with the desired folder structure
            new_key = f"{client_id}/{camera_id}/{year}/{month}/{day}/{file_name}"
            move_file_to_new_bucket(bucket_name, file_key, new_bucket_name, new_key)

            print(f"File {file_key} downloaded and moved to {new_key}")

        break

    # Wait for some time before checking again
    time.sleep(60)  # Adjust the sleep interval as needed

