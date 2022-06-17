#!/usr/bin/env python3.8
import socket
import sys
import os
import re

def TCP(filename,downloadServer,TCP_IP_ADDRESS,TCP_PORT_NO):
    getMessage = ("GET "+filename+" FSP/1.0\r\nHostname: "+downloadServer+"\r\nAgent: xbrnaf00\r\n\r\n").encode()
    BUFFER_SIZE = 16384
    TCPclientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # zasielanie validneho prikazu na server pomocou TCP protokolu 
    TCPclientSocket.connect((TCP_IP_ADDRESS, TCP_PORT_NO))                          
    TCPclientSocket.send(getMessage)
    buffer = b''
    while True:
        recievedData = TCPclientSocket.recv(BUFFER_SIZE)
        if recievedData:
            buffer += recievedData
        else:
            break
    TCPclientSocket.close()
    return buffer

def UDP(downloadServer,UDP_IP_ADDRESS, UDP_PORT_NO):
    Message = ("WHEREIS "+downloadServer).encode()                          # aky server sa vola ak neexistuje tak err 
    UDPclientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)      # zasielanie validneho prikazu na server pomocou UDP protokolu
    UDPclientSocket.sendto(Message, (UDP_IP_ADDRESS, UDP_PORT_NO))          # za cielom ziskat spravny port 
    recievedMessage, serverAdress = UDPclientSocket.recvfrom(2048)
    recievedMessage = recievedMessage.decode('latin-1')
    UDPclientSocket.close()
    return recievedMessage

def downloadAndWrite(filename,boolindex,recievedData,tmp):                  # otorenie subor na zapis "write bytes"
    fileToDownload = open(filename, "wb")                                   # oddelenie hlavicky a dat  
    recievedData = recievedData.split(b'\r\n\r\n',1)
    if boolindex :
        fileToDownload.write(recievedData[1][:-1])
    else:
        fileToDownload.write(recievedData[1])
    return


def GetTCPandDecode(filename,downloadServer,TCP_IP_ADDRESS,TCP_PORT_NO,path,boolindex):

    recievedData = TCP(filename,downloadServer,TCP_IP_ADDRESS,TCP_PORT_NO)
    
    tmp = recievedData.decode('latin-1').split("\r\n")                      # pripojenie a nasledne stahovanie pozadovanych dat
    result = tmp[0]
    lenght = tmp[1].split(":")
    lenght = int(lenght[1])

    if result ==  "FSP/1.0 Bad Request":                                    # na zaklade hlavicky, vyhodnetenie odpovede zo serveru 
        sys.exit("ERR Bad Request\n")
    elif result ==  "FSP/1.0 Not Found":
        sys.exit("ERR Not Found\n")
    elif result ==  "FSP/1.0 Server Error":
        sys.exit("ERR Server Error\n")
    elif result ==  "FSP/1.0 Success":
        prevDirectory = os.getcwd()
        if path != "":
            try:
                os.chdir(path)
                filename = filename.split("/")
                filename = filename[-1]
            except:
                os.makedirs( path, 493 )
        downloadAndWrite(filename,boolindex,recievedData,tmp)               # pokial je vsetko v poriadku nasleduje stiahnutie a zapisanie suborov
        os.chdir(prevDirectory)
    else:
        sys.exit("ERR Unknown response from server\n")
    return

def main():
    if len(sys.argv) != 5:                  # ak je na vstupe ine pocet ako 5 argumentov tak nastava chyba
        sys.exit("ERR Wrong arguments\n")

    if (str(sys.argv[4][:3]) == "fsp" ):    # zisti ktory argument je nameServer a SURL
        nameServer = sys.argv[2]
        SURL = sys.argv[4]
    elif (str(sys.argv[2][:3]) == "fsp" ):
        nameServer = sys.argv[4]
        SURL = sys.argv[2]
    else:                                     # ak nie je fsp protocol tak vracia chybu 
        sys.exit("ERR NOT FSP protocol\n")

    SURLsplitted = SURL.split("/")
    getAll = False

    if ( SURLsplitted[-1] == "index" ):
        boolindex = True
    elif ( SURLsplitted[-1] == "*" ):       # pokial je na vstupe GET ALL (*) tak sa najprv stiahne index a 
        boolindex = True                    # potom sa postupne stahuju vsetky files z indexu
        getAll = True
        SURLsplitted[-1] = "index"
    else:
        boolindex = False

    tmp = nameServer.split(":")
    UDP_IP_ADDRESS = tmp[0]
    UDP_PORT_NO = int(tmp[1])
    downloadServer = SURLsplitted[2]

    if re.fullmatch('[a-zA-Z0-9_.-]*',downloadServer) == None:      # konttola pomocou regexu ci je validny nazov servera
        sys.exit("ERR Syntax")

    if ( len(SURLsplitted) > 4):
        filename = SURLsplitted[3]
        path = SURLsplitted[3]
        for i in SURLsplitted[4:]:
            filename += "/"+i 
        for i in SURLsplitted[4:-2]:
            path += "/"+i
    else:
        filename = SURLsplitted[-1]
        path = ""
    
    recievedMessage = UDP(downloadServer,UDP_IP_ADDRESS, UDP_PORT_NO)  # volanie funkcie, ktorej ucelom je pripojenie na   
                                                                       # zadany server v snahe ziskat port pre pripojenie cez TCP
    status = recievedMessage[:2]
    if ( status == "OK" ):
        recievedMessage = recievedMessage[3:].split(":")            # Ak je odpoved serveru OK tak vsetko prebehlo v poriadku inak sa vypise chybna navratova sprava
        TCP_IP_ADDRESS = recievedMessage[-2]
        TCP_PORT_NO = int(recievedMessage[-1])
    else:
        sys.exit(recievedMessage)

    GetTCPandDecode(filename,downloadServer,TCP_IP_ADDRESS,TCP_PORT_NO,path,boolindex)  

    if getAll == True:
        FileIndex = open("index", "r")      # v pripade ze je zadane na vstupe Get All tak sa postupne stahuje kazdy subor z index filu daneho servera
        ReadFile = FileIndex.read()
        Index = ReadFile.splitlines()
        for fileFromIndex in Index:
            directories = fileFromIndex.split("/")
            path = ""
            for directory in directories [:-1]:
                path += directory+"/"
            boolindex = False
            GetTCPandDecode(fileFromIndex,downloadServer,TCP_IP_ADDRESS,TCP_PORT_NO,path,boolindex)
    return

main()
