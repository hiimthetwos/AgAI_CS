import pika
import numpy as np
import cv2
import os
import subprocess
import GPUtil
import time

# Set up RabbitMQ to monitor GPU usage
GPUs = GPUtil.getGPUs()

# Set up RabbitMQ connection
try:
    credentials = pika.PlainCredentials('username', 'password')
    parameters = pika.ConnectionParameters('linuxlapserver', credentials=credentials)
    connection = pika.BlockingConnection(parameters)
except Exception as e:
    print("Error connecting to RabbitMQ server: %s" % e)
channel = connection.channel()
channel.queue_declare(queue='file_queue')

# Define callback function for handling new messages
def process_message(ch, method, properties, body):
    file_path = body.decode()
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
        # Run testimg.py script with the file name as an argument
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testimg.py')
        result = subprocess.Popen(['python', script_path, file_path])

        # Check if the subprocess completed successfully
        if result.returncode == 0:
            print(f"testimg.py successfully processed {file_path}")
        else:
            print(f"Error in testimg.py: {result.stderr}")

        # Delete file after processing
        # os.remove(file_path)
        # print("File %s deleted" % file_path)

    except FileNotFoundError as e:
        print("File not found: %s" % file_path)
    except Exception as e:
        print("Error occurred while processing file: %s" % e)

    # Acknowledge message
    channel.basic_ack(delivery_tag=method.delivery_tag)
    channel.basic_consume(queue='file_queue', on_message_callback=process_message, auto_ack=False)

    # Start the next subprocess immediately if there is a file in the queue
    method_frame, header_frame, body = channel.basic_get(queue='file_queue')
    if method_frame:
        process_message(channel, method_frame, header_frame, body)

# Start consuming messages from file_queue
channel.basic_consume(queue='file_queue', on_message_callback=process_message)
print("Waiting for messages...")
channel.start_consuming()
