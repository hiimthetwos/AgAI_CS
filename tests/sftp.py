import requests

url = 'http://66.175.223.220:8080/upload'  # replace with the correct endpoint on your server
file_path = '/home/ryanbert/code/AgAI_CS/tests/file.txt'

with open(file_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)

if response.status_code == 200:
    print('File uploaded successfully!')
else:
    print(f'Error uploading file. Status code: {response.status_code}')

