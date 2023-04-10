import pika
import threading
import subprocess
import time
import os
import gpustat

rabbitmq_host = "localhost"
queue_name = "file_queue"
proc_script_path = "/home/ryanbert/code/AgAI_CS/ProcServer/procserver.py"

def get_gpu_memory():
    gpu_stats = gpustat.new_query()
    total_memory = gpu_stats.gpus[0].memory_total
    used_memory = gpu_stats.gpus[0].memory_used
    available_memory = total_memory - used_memory
    return available_memory / total_memory * 100


def run_subprocess(script_path, file_name, process_number):
    print(f"Running subprocess {process_number} with file {file_name}")
    start_time = time.time()
    result = subprocess.run(["python", script_path, file_name])
    end_time = time.time()
    duration = end_time - start_time
    print(f"Subprocess {process_number} completed, duration: {duration:.2f} seconds")

connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()

channel.queue_declare(queue=queue_name)

process_number = 0

while True:
    method_frame, header_frame, body = channel.basic_get(queue=queue_name)

    if method_frame:
        file_name = body.decode("utf-8")
        gpu_memory_available = get_gpu_memory()

        if gpu_memory_available >= 15:
            process_number += 1
            print(f"Taking file {file_name} from the queue, GPU memory is sufficient")

            proc_thread = threading.Thread(target=run_subprocess, args=(proc_script_path, file_name, process_number), name=f"run_subprocess-{process_number}")
            proc_thread.start()

        channel.basic_ack(method_frame.delivery_tag)
    else:
        time.sleep(5)  # Adjust the sleep interval as needed
