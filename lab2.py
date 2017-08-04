# Jason Koan
# ID Number: 1000693638
# July 24th 2017
# CSE 4340 Lab 2 Wifi Summer 2017


import socket
import threading
import struct
import fcntl
import bluetooth
import random
import os
import re
from time import sleep

class LabTwo(object):

  data = None

  #Set the directory to the Current Working Directory
  dir = os.listdir(os.getcwd())

  #Boolean to controls which one connected as what for Wifi
  connectedAsClientWifi = False
  connectedAsServerWifi = False

  #Boolean to controls which one connected as what for Bluetooth
  connectedAsClientBluetooth = False
  connectedAsServerBluetooth = False

  #The Wifi Sockets
  sWifi = None
  cWifi = None
  sToCWifi = None

  #The Bluetooth sockets
  sBluetooth = None
  cBluetooth = None
  sToCBluetooth = None

  #The Mac Address that connects VIA Bluetooth
  bluetoothMacToConnect = None

  #A list of nearvy Bluetooth Devices
  nearbyDevicesBluetooth = None

  #Used for file transfer
  fileNames = None
  fileToDownload = None

  #This is used to stop message recieve threading
  isDownloadingFile = False

  #HostIP is the IP address of this Computer
  hostIP = None
  #Other PC IP is the IP address of the other PC
  otherPCIP = None

  #The ports
  portBluetooth = 6
  portWifi = 6196

  ## This function starts the Wifi Server and sets the sTOCWifi
  ## socket if no exceptions are throwned.
  def serverSocketWifi(self):

    print("Starting Server Wifi")
    try:
      self.sWifi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sWifi.bind(('',self.portWifi))
      randNum = random.randint(5,10)
      self.sWifi.settimeout(randNum)
      self.sWifi.listen(1)

    except socket.error, e:
      print("Error in the serverSocket")
      return

    try:
      self.sToCWifi, addr = self.sWifi.accept()
      self.connectedAsServerWifi = True
      sleep(1)
      tMsg = threading.Thread(target=self.getMessageWIFI)
      tMsg.start()
      incoming_ip = str(addr[0])
      print("Connected as Server over WIFI!")
    except:
      print("Server timed out")


  ## This fucntion starts the WIFI client and attempts to connect to the
  ## server. If success it sets the cWIFI socket
  def clientSocketWifi(self):
    print("Starting Client Wifi")
    #self.otherPCIP = "192.168.0.7"

    self.cWifi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    randNum = random.randint(5, 10)
    attempt = 0
    for attempt in range(0, randNum):
      try:
        #Here I attempt to connect to the IP I got from the BT connection
        self.cWifi.connect((self.otherPCIP, self.portWifi))
        self.connectedAsClientWifi = True
        sleep(1)
        #Starts the message thread.
        tMsg = threading.Thread(target=self.getMessageWIFI)
        tMsg.start()
        print("Connected as Client over WIFI!")
        return
      except Exception, e:
        print("failed to connect, retying.")
        sleep(1)
        if(attempt == randNum):
          return


  # This fucntion works like the server one but it's BT
  def serverSocketBluetooth(self):
    backlog = 1
    self.sBluetooth = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    self.sBluetooth.bind((self.read_local_bdaddr(), self.portBluetooth))

    randNum = random.randint(3,8)

    try:
      self.sBluetooth.settimeout(randNum)
      self.sBluetooth.listen(backlog)
      self.sToCBluetooth, clientInfo = self.sBluetooth.accept()
      self.connectedAsServerBluetooth = True
      print("\nConnected as a Bluetooth Server\n")
      #Once connected call the Exchange IP function
      self.exchangeIPOverBluetooth()

    except bluetooth.BluetoothError as e:
      sleep(1)
      print("Bluetooth server timed out")

  # This function starts the client for BT and connects the the MAC
  # that was obtained from the scan For nearby devices
  def clientSocketBluetooth(self):

    self.cBluetooth = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    #self.cBluetooth.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    randNum = random.randint(4, 10)
    attempt = 0
    for attempt in range(0, randNum):
      try:
        self.cBluetooth.connect((self.bluetoothMacToConnect, self.portBluetooth))
        self.connectedAsClientBluetooth = True
        print("Connected as a Bluetooth Client\n")
        #Once connected call the Exchange IP function
        self.exchangeIPOverBluetooth()
        break
      except bluetooth.BluetoothError as e:
       sleep(1)
       print("client timed out")
       if(attempt == randNum):
         return

  # This function exchnages the IP Address to the other PC over BT
  def exchangeIPOverBluetooth(self):
    #Retrieve and set the Host IP
    self.getHostIP()

    # This is set up so server is ready to recieve, the Client
    # Will wait 1 second then send. The server will then wait one
    # second then send.

    if(self.connectedAsServerBluetooth == True):
      self.otherPCIP = self.sToCBluetooth.recv(1024)
      sleep(1)
      self.sToCBluetooth.send(self.hostIP)
      print("The IP the Server got was: "+self.otherPCIP)
      self.sBluetooth.close()
      self.sToCBluetooth.close()

    elif(self.connectedAsClientBluetooth == True):
      sleep(1)
      self.cBluetooth.send(self.hostIP)
      self.otherPCIP = self.cBluetooth.recv(1024)
      print("The IP the client got was: "+self.otherPCIP)
      self.cBluetooth.close()




  # This fuction is used to get the local IP Address comes from Stack OverFlow
  # https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python
  # I slightly modified it to handle exceptions
  def get_ip_address(self, ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      return socket.inet_ntoa(fcntl.ioctl(
          s.fileno(),
          0x8915,  # SIOCGIFADDR
          struct.pack('256s', ifname[:15])
      )[20:24])
    except:
      pass


  # This fucntion handles sending strings to the client or server
  def sendMessageWifi(self, text):

    # If you're an client, then you send messages using Sock
    if(self.connectedAsClientWifi == True):
      if(text != ""):

        self.cWifi.send(text)

        #If you send a "ls" call this function
        if(text == "ls"):
          self.getLs()

        parseText = text.split(" ")
        if(parseText[0] == "download"):

          try:
            self.fileToDownload = parseText[1]
            self.isDownloadingFile = True
            sleep(1)

          except:
            print("Need to specify the file to download. I.e download test.txt")

    # If you're an Server, then you send messages using client
    elif(self.connectedAsServerWifi == True):
      if(text != ""):

        self.sToCWifi.send(text)

        if(text == "ls"):
          self.getLs()

        parseText = text.split(" ")
        if(parseText[0] == "download"):

          try:
            self.fileToDownload = parseText[1]

            self.isDownloadingFile = True

          except:
            print("Need to specify the file to download. I.e download test.txt")


  # This fucntion deals with recieveing strings.
  # depending on the type of string receive, it will do different things
  def getMessageWIFI(self):

    while (self.connectedAsClientWifi == True or self.connectedAsServerWifi == True):

      # If you're an client, then you recieve messages using cWifi
      if(self.connectedAsClientWifi == True):

          data = self.cWifi.recv(1024)
          if(self.isDownloadingFile == True):

            downloadingFile = open(self.fileToDownload, "wb")

            self.cWifi.settimeout(1)
            print("Downloading...")
            while (data):

              downloadingFile.write(data)

              try:
                data = self.cWifi.recv(1024)
              except:
                self.cWifi.settimeout(60)
                break


            downloadingFile.close()
            print("Download Complete")
            self.isDownloadingFile = False
            continue

          if data:
            parseText = data.split(" ")

            if(data == "ls"):
              self.sendLs()


            elif(parseText[0] == "download"):
              parseText[0] = "blank"
              fileName = parseText[1]
              try:
                if(fileName is not None):
                  print("Sending " + fileName)
                  self.sendFile(fileName)

              except:
                print("Need a name of the file to Download. I.E download test.txt")


            print(data)


      # If you're an Server, then you recieve messages using sToCWifi
      elif(self.connectedAsServerWifi == True):

          data = self.sToCWifi.recv(1024)

          if(self.isDownloadingFile == True):

            downloadingFile = open(self.fileToDownload, "wb")

            self.sToCWifi.settimeout(1)
            print("Downloading...")
            while (data):

              downloadingFile.write(data)

              try:
                data = self.sToCWifi.recv(1024)
              except:
                self.sToCWifi.settimeout(60)
                break


            downloadingFile.close()
            print("Download Complete")
            self.isDownloadingFile = False
            continue

          if data:

            parseText = data.split(" ")
            if(data == "ls"):

              self.sendLs()

            elif(parseText[0] == "download"):
                parseText[0] = "blank"

                try:
                  fileName = parseText[1]
                  if(fileName is not None):
                    print("Sending " + fileName)
                    self.sendFile(fileName)
                except:
                  print("Need a name of the file to Download. I.E download test.txt")

            print(data)

  # Sends the directory to the other PC
  def sendLs(self):
      self.dir = os.listdir(os.getcwd())
      for fileName in self.dir:
        if(self.connectedAsClientWifi == True):
          self.cWifi.send(fileName)
        elif(self.connectedAsServerWifi == True):
          self.sToCWifi.send(fileName)

  # Receives and parses the Directory
  def getLs(self):
    if(self.connectedAsClientWifi == True):

      self.fileNames = self.cWifi.recv(1024)
      if(self.fileNames is not None):
        self.fileNames = re.sub(r"(\.+txt|\.+pdf|\.+mp3|\.+mp4|\.+jpg|\.+png|\.+gif|\.+py|\.+cpp|\.+java|\.+pyc|\.+c)", r"\1 ", self.fileNames)
        print(self.fileNames)

    elif(self.connectedAsServerWifi == True):

      self.fileNames = self.sToCWifi.recv(1024)
      if(self.fileNames is not None):
        self.fileNames = re.sub(r"(\.+txt|\.+pdf|\.+mp3|\.+mp4|\.+jpg|\.+png|\.+gif|\.+py|\.+cpp|\.+java|\.+pyc|\.+c)", r"\1 ", self.fileNames)
        print(self.fileNames)

  # Looks for for the file is the dir and sends it over
  def sendFile(self, fileName):

    if(fileName in self.dir):
      fileToSend = open (fileName, "rb")
    else:
      if(self.connectedAsClientWifi == True):
        self.cWifi.send("File not found!")
        return
      elif(self.connectedAsServerWifi == True):
        self.sToCWifi.send("File not found")
        return

    data = fileToSend.read(1024)
    while (data):
      if(self.connectedAsClientWifi == True):
        self.cWifi.send(data)
      elif(self.connectedAsServerWifi == True):
        self.sToCWifi.send(data)

      data = fileToSend.read(1024)

    fileToSend.close()
    print("File Sent!!!")


# This function comes from https://github.com/karulis/pybluez/commit/38634a16f8ecb2dbcac3e6cc4a12ec713d5f7b8b
# This function returns the MAC address from BlueTooth. I use this to get the host Mac Address of the BT Adaptor
# Without this, my program won't be as portable. I really don't understand this code but I understand that it
# does return the correct host bluetooth MAC address as a string.
  def read_local_bdaddr(self):
    get_byte = str
    import bluetooth._bluetooth as _bt
    hci_sock = _bt.hci_open_dev(0)
    old_filter = hci_sock.getsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, 14)
    flt = _bt.hci_filter_new()
    opcode = _bt.cmd_opcode_pack(_bt.OGF_INFO_PARAM,
              _bt.OCF_READ_BD_ADDR)
    _bt.hci_filter_set_ptype(flt, _bt.HCI_EVENT_PKT)
    _bt.hci_filter_set_event(flt, _bt.EVT_CMD_COMPLETE);
    _bt.hci_filter_set_opcode(flt, opcode)
    hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, flt )

    _bt.hci_send_cmd(hci_sock, _bt.OGF_INFO_PARAM, _bt.OCF_READ_BD_ADDR )

    pkt = hci_sock.recv(255)

    status,raw_bdaddr = struct.unpack("xxxxxxB6s", pkt)
    assert status == 0

    t = [ "%X" % ord(get_byte(b)) for b in raw_bdaddr ]
    t.reverse()
    bdaddr = ":".join(t)

    # restore old filter
    hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, old_filter )
    return bdaddr

  # This function scans for nearby BT devices
  def scanForDevices(self):

    self.nearbyDevicesBluetooth = bluetooth.discover_devices()

    count = 0
    for bdaddr in self.nearbyDevicesBluetooth:
      if(bluetooth.lookup_name(bdaddr) != None):
        print(str(count) + " <--- Device name: " + bluetooth.lookup_name(bdaddr) + "Address: " + bdaddr)
      else:
        print(str(count) + " <--- No Name listed: Address: " + bdaddr)

      count = count + 1

  # This will set the HostIP address. It has 3 for loop to
  # make it portable. I tested on 3 devices and each one uses a different for loop
  def getHostIP(self):
  #This loop will set the local IP Address. It can be different on each laptop
  #So I for loop through them. For WIFI#So I for loop through them. For WIFI
    count = 0
    for count in range(0, 9):
      adaptor = "wlp"+str(count)+"s0"
      self.hostIP = self.get_ip_address(adaptor)
      count = count + 1
      if(self.hostIP != None):
        break

    #This is for wireless raspberry pi
    if(self.hostIP == None):
      count = 0
      for count in range(0, 9):
        adaptor = "wlan"+str(count)
        self.hostIP = self.get_ip_address(adaptor)
        count = count + 1
        if(self.hostIP != None):
          break

    #This is set the local IP address if the laptop is on wire instead of Wifi
    if(self.hostIP == None):
      count = 0
      for count in range(0, 9):
        adaptor = "enp"+str(count)+"s0"
        self.hostIP = self.get_ip_address(adaptor)
        count = count + 1
        if(self.hostIP != None):
          break



if __name__ == "__main__":
  labTwo = LabTwo()

  print("Welcome, type Scan to start looking for BT devices.")
  while(labTwo.bluetoothMacToConnect == None):
    cmd = raw_input()

    if(cmd == "scan"):
      print("Scanning... takes about 10 seconds")
      labTwo.scanForDevices()

      if(labTwo.nearbyDevicesBluetooth):
        print("Type \"connect\" and the number next to the device to connect to it. I.E connect 0")
      else:
        print("No devices found, please check the visibility of the device")

    #This is the connect command, Devices must be found so that you can connect to them
    if(labTwo.nearbyDevicesBluetooth != None):
      #You can only connect if you are not already connected, and the second arg for "connect" is a number listed in the scan display
      cmdList = cmd.split(" ")
      if(cmdList[0] == "connect" and (int(cmdList[1]) <= len(labTwo.nearbyDevicesBluetooth))):
        #checks to see if the arg for the device you want to connect to is in the list of nearby devices
        if(labTwo.nearbyDevicesBluetooth[int(cmdList[1])] in labTwo.nearbyDevicesBluetooth):
          #assign that MAC to the address
          labTwo.bluetoothMacToConnect = labTwo.nearbyDevicesBluetooth[int(cmdList[1])]
          print("you selected : "+labTwo.nearbyDevicesBluetooth[int(cmdList[1])])



  #This is the peer to peer connection loop for Bluetooth
  i = 0
  for i in range(0,5):
    if(labTwo.connectedAsClientBluetooth == False and labTwo.connectedAsServerBluetooth == False):
      tsB = threading.Thread(target=labTwo.serverSocketBluetooth)
      tsB.start()

      tsB.join()
    if(labTwo.connectedAsClientBluetooth == False and labTwo.connectedAsServerBluetooth == False):
      tcB = threading.Thread(target=labTwo.clientSocketBluetooth)
      tcB.start()

      tcB.join()

  #This is done to increase the chances that both devices do not start the
  # Wifi P2P connections at the same time. If they start at the same time
  # They will both connect as a client which doesn't work.
  randNum = random.randint(1 ,5)
  sleep(randNum)
  randNum = random.randint(1 ,4)
  sleep(randNum)
  randNum = random.randint(1 ,3)
  sleep(randNum)
  randNum = random.randint(1 ,2)
  sleep(randNum)


  #This is the peer to peer connection loop for Wifi
  i = 0
  for i in range(0,5):
    if(labTwo.connectedAsClientWifi == False and labTwo.connectedAsServerWifi == False):
      tsW = threading.Thread(target=labTwo.serverSocketWifi)
      tsW.start()

      tsW.join()


    if(labTwo.connectedAsClientWifi == False and labTwo.connectedAsServerWifi == False):
      tcW = threading.Thread(target=labTwo.clientSocketWifi)
      tcW.start()

      tcW.join()


  #Once conected, this is the main loop
  print("Connected!!! Type help to see a list of commands\n")
  while(labTwo.connectedAsClientWifi == True or labTwo.connectedAsServerWifi == True):
    text = raw_input()

    if(text == "q"):
      if(labTwo.connectedAsClientWifi == True):
        labTwo.cWifi.close()
      elif(labTwo.connectedAsServerWifi == True):
        labTwo.sToCWifi.close()
        labTwo.sWifi.close()
      labTwo.connectedAsClientWifi = False
      labTwo.connectedAsServerWifi = False
      print("Safe to quit with ctr+z")

    elif(text == "help"):
      print("ls  <=== see the directory of the connected PC")
      print("download [FILE NAME] <=== downloads the file from connected PC")
      print("q <=== Quit the program")

    else:
      labTwo.sendMessageWifi(text)



