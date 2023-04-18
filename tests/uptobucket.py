import boto3
import os
import gzip

# Local folder, S3 bucket name, and S3 folder name
local_folder = '/home/ryanbert/Documents/uptobucket'
bucket_name = 'agaicamstorage'
s3_folder = 'collected'

# Initialize the boto3 client with an anonymous session
s3 = boto3.client('s3')

# Iterate through files in the local folder and upload them to the S3 bucket
for root, _, files in os.walk(local_folder):
    for file in files:
        local_file_path = os.path.join(root, file)
        s3_key = os.path.join(s3_folder, file)

        # Create a new file name by replacing 'aa11' with 'a1'
        new_file_name = file.replace('aa11', 'a1')

        # Open the local file for reading and create a gzipped version of the file
        with open(local_file_path, 'rb') as f_in, gzip.open(os.path.join(root, new_file_name + '.gz'), 'wb') as f_out:
            f_out.write(f_in.read())

        # Upload the gzipped file to the S3 bucket
        s3.upload_file(os.path.join(root, new_file_name + '.gz'), bucket_name, os.path.join(s3_folder, new_file_name + '.gz'))
        print(f"Uploaded {local_file_path} to {bucket_name}/{new_file_name + '.gz'}")

        # Remove the gzipped file from the local directory
        os.remove(os.path.join(root, new_file_name + '.gz'))
