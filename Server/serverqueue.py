import os
import pika
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

def get_rabbitmq_connection():
    try:
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters('mission', credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        return connection
    except Exception as e:
        print("Error connecting to RabbitMQ server: %s" % e)
        return None

# Set up RabbitMQ connection
connection = get_rabbitmq_connection()
while not connection:
    print("Retrying RabbitMQ connection...")
    time.sleep(5)
    connection = get_rabbitmq_connection()

channel = connection.channel()
channel.queue_declare(queue='file_queue')

class FileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = event.src_path

        # Wait for the file to stop being modified by adding a delay
        time.sleep(2)

        try:
            # Check if the file is complete by checking if it's been modified in the last 2 seconds
            if time.time() - os.path.getmtime(file_path) < 2:
                return
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return

        # Check if the file is newly created
        if not hasattr(self, 'published_files'):
            self.published_files = set()

        # Skip if the file is already published
        if file_path in self.published_files:
            return

        self.published_files.add(file_path)

        # Replace server file path with client file path
        file_path = file_path.replace('/srv/data/upload', '/mnt/data/upload')
        # file_path = '/tmp/downloadtest'
        channel.basic_publish(exchange='', routing_key='file_queue', body=file_path.encode())
        print("File %s published to queue" % file_path)


    def on_deleted(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        # Replace server file path with client file path
        file_path = file_path.replace('/srv/data/upload', '/mnt/data/upload')
        # file_path = '/tmp/downloadtest'
        try:
            method_frame, header_frame, body = channel.basic_get(queue='file_queue')
            while method_frame:
                if body.decode() == file_path:
                    channel.basic_ack(method_frame.delivery_tag)
                    print("File %s removed from queue" % file_path)
                method_frame, header_frame, body = channel.basic_get(queue='file_queue')
        except Exception as e:
            print("Error occurred while removing file from queue: %s" % e)

class FileObserver:
    def __init__(self, path):
        self.path = path
        self.event_handler = FileEventHandler()
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.path, recursive=False)

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        self.observer.start()
        self.observer.join()

# Start observer in a separate thread
# observer = FileObserver('/srv/nfs/data/data')
observer = FileObserver('/srv/data/upload')
observer.start()

# Start consuming messages in a separate thread
def consume_messages():
    channel.start_consuming()

consume_thread = threading.Thread(target=consume_messages, daemon=True)
consume_thread.start()

# # Check if there are existing files in the folder
# for filename in os.listdir('/srv/nfs/data/data'):
#     if filename.endswith('.csv'):
#         file_path = os.path.join('/srv/nfs/data/data', filename)
#         # Replace server file path with client file path
#         file_path = file_path.replace('/srv/nfs/data', '/mnt/nfs/data')
#         channel.basic_publish(exchange='', routing_key='file_queue', body=file_path.encode())
#         print("File %s published to queue" % file_path)
#         time.sleep(1)  # Add a delay of 1 second

for filename in os.listdir('/srv/data/upload'):
    if filename.endswith('.gz'):
        file_path = os.path.join('/srv/data/upload', filename)
        # Replace server file path with client file path
        file_path = file_path.replace('/srv/data/upload', '/mnt/data/upload')
        channel.basic_publish(exchange='', routing_key='file_queue', body=file_path.encode())
        print("File %s published to queue" % file_path)
        time.sleep(1)  # Add a delay of 1 second

try:
    # Wait for observer and consume threads to complete
    observer.thread.join()
    consume_thread.join

finally:
    print("Server stopped.")
