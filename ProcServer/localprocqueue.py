import pika
import numpy as np
import cv2
import os
import subprocess
import GPUtil
import time
from concurrent.futures import ThreadPoolExecutor

# Set up RabbitMQ to monitor GPU usage
GPUs = GPUtil.getGPUs()

# Set up RabbitMQ connection
try:
    credentials = pika.PlainCredentials('agai', 'agai')
    parameters = pika.ConnectionParameters('beartooth', credentials=credentials)
    connection = pika.BlockingConnection(parameters)
except Exception as e:
    print("Error connecting to RabbitMQ server: %s" % e)
channel = connection.channel()
channel.queue_declare(queue='file_queue')

# Define callback function for handling new messages
def process_message(file_path):
    print("Received message: %s" % file_path)

    # Check if there is enough memory to start a new subprocess
    while True:
        GPUs = GPUtil.getGPUs()
        available_memory = min([gpu.memoryFree for gpu in GPUs])
        total_memory = min([gpu.memoryTotal for gpu in GPUs])
        available_memory_percentage = available_memory / total_memory * 100

        if available_memory_percentage >= 10:
            break
        time.sleep(1)  # Wait for 1 second before checking again

    # Print available GPU memory before starting the subprocess
    print(f"Available GPU memory before starting subprocess: {available_memory} MB")

    try:
        script_path = '/home/agai/code/AgAI_CS/ProcServer/localprocserver.py'
        result = subprocess.run(['python', script_path, file_path], check=True)

        print(f"Successfully processed {file_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error in procserver.py: {e.stderr}")
    except FileNotFoundError as e:
        print("File not found: %s" % file_path)
    except Exception as e:
        print("Error occurred while processing file: %s" % e)

def consume_message(ch, method, properties, body):
    file_path = body.decode()
    with ThreadPoolExecutor(max_workers=5) as executor:
        future = executor.submit(process_message, file_path)
        future.result()
        channel.basic_ack(delivery_tag=method.delivery_tag)

# Start consuming messages from file_queue
channel.basic_consume(queue='file_queue', on_message_callback=consume_message)
print("Waiting for messages...")
channel.start_consuming()
