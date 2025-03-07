# Socket programming for Image/video transfer
# Store the video/Image into the storage device
# Provide a user interface over HTTPS to view the video/images

import os
import io
import datetime
import socket
SW_VERSION = '1.0.0'
# Directory path for storing captured data
dir_pth = '/mnt/hd/Seagate/KSHome/capture/'
cctvPort = 1234

# Create TCP socket
cctvSocket = socket.socket()
cctvSocket.bind(('', cctvPort))
cctvSocket.listen(5)
print(SW_VERSION)
print("Socket started listening")

def getStorageDst(clientAdd):
    fullPath = ' '
    if os.path.isdir('/mnt/hd/Seagate'):
        if not os.path.isdir(dir_pth):
            os.mkdir(dir_pth)
        subDir = os.path.join(dir_pth, clientAdd)
        if not os.path.isdir(subDir):
            os.mkdir(subDir)
        subDir1 = os.path.join(subDir, datetime.datetime.now().strftime("%m_%d_%y"))
        if not os.path.isdir(subDir1):
            os.mkdir(subDir1)
        fullPath = os.path.join(subDir1, datetime.datetime.now().strftime("%H_%M_%S") + '.h264')
    return fullPath

# Accept client connections and handle data transfer
while True:
    try:
        clientCnx, add = cctvSocket.accept()
        with clientCnx.makefile('rb') as cnx:
            print("Connection arrived")
            print(add)
            print(add[0])
            # Read data from socket and store in disk
            filePath = getStorageDst(add[0])
            if filePath:
                with io.open(filePath, 'wb') as fp:
                    fp.write(cnx.read())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        clientCnx.close()




