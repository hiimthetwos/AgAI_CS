import boto3

bucket_name = "agaicamstorage"
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

def move_file_within_bucket(bucket, src_key, dst_key):
    # Copy the file to the new location
    s3.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": src_key}, Key=dst_key)
    
    # Delete the file from the original location
    s3.delete_object(Bucket=bucket, Key=src_key)

while True:
    files = list_files_in_folder(bucket_name, source_folder)

    if files:
        for file_key in files:
            print(f"File {file_key} found in {source_folder} folder")
            # Download the file
            local_file_path = f"{local_folder}{file_key.split('/')[-1]}"
            s3.download_file(bucket_name, file_key, local_file_path)

            # Move the file to the destination folder within the bucket
            new_key = file_key.replace(source_folder, destination_folder)
            move_file_within_bucket(bucket_name, file_key, new_key)

            print(f"File {file_key} downloaded and moved to {new_key}")

        break

    # Wait for some time before checking again
    time.sleep(60)  # Adjust the sleep interval as needed
