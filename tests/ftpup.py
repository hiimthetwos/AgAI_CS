import ftplib

def upload_file(host, port, username, password, local_file, remote_file):
    try:
        ftp = ftplib.FTP()
        ftp.connect(host=host, port=port)
        ftp.login(user=username, passwd=password)
        with open(local_file, 'rb') as file:
            ftp.storbinary(f'STOR {remote_file}', file)
        ftp.quit()
        return True
    except ftplib.all_errors as e:
        print(f"FTP error: {e}")
        return False

filename = '/home/ryanbert/code/AgAI_CS/tests/file.txt'
host = 'agaiapp.com'
port = 21
username = 'user'
password = 'pass'
remote_filename = 'testtest.txt'

success = upload_file(host, port, username, password, filename, remote_filename)
if success:
    print("Upload successful")
else:
    print("Upload failed")
