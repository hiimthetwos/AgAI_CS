import ftplib

filename = '/home/ryanbert/code/AgAI_CS/tests/file.txt'
ftp = ftplib.FTP()
ftp.connect(host='66.175.223.220', port=21)
ftp.login(user='user', passwd='pass')
with open(filename, 'rb') as file:
    ftp.storbinary(f'STOR test.txt', file)
ftp.quit()
