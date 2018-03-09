#v0.0.4!
import socket
import sys
import os
import _thread
from time import sleep
import struct
import fcntl
import select
def sender():
    print('sender ready')
    while True:
        try:
            s2.sendto(out_queue.pop(0), (clientconfig['remotehost3'], int(clientconfig['remoteport3'])))
            s1.sendto(out_queue.pop(0), (clientconfig['remotehost2'], int(clientconfig['remoteport2'])))
            s.sendto(out_queue.pop(0), (clientconfig['remotehost1'], int(clientconfig['remoteport1'])))
            sleep(0.001)
        except IndexError:
            sleep(0.0001)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print(sys.exc_info())
def taphandling():
    next_one_out = 0
    next_one_in = 0
    inputs = [tap]
    outputs = [tap]
    print('tap handling ready!')
    while True:
        if next_one_out >= 255:
            next_one_out = 0
        if next_one_in >= 255:
            next_one_in = 0
        try:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            if readable:
                out_queue.append(bytes(str(next_one_out) + '&', 'ascii') + tap.read(1500))
                next_one_out += 1
            else:
                try:
                    print('next one in is', min(orderer_dict), 'next one out is', next_one_out, end='\r' )
                    tap.write(orderer_dict.pop(min(orderer_dict)))
                except KeyError:
                    sleep(0.0001)
                except ValueError:
                    sleep(0.001)
                except ValueError:
                    sleep(0.001)
                except IndexError:
                    sleep(0.0001)
                except:
                    print(sys.exc_info())

        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print('error from taphandling')
            print(sys.exc_info())
def starting():
    print('Initializing')
    try:
        print(clientconfig['remotehost1'])
        s.sendto(bytes('#Balancetonport', 'ascii'), (clientconfig['remotehost1'], int(clientconfig['remoteport1'])))
        s1.sendto(bytes('#Balancetonport', 'ascii'), (clientconfig['remotehost2'], int(clientconfig['remoteport2'])))
        s2.sendto(bytes('#Balancetonport', 'ascii'), (clientconfig['remotehost3'], int(clientconfig['remoteport3'])))
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print(sys.exc_info())
if __name__ == "__main__":
    orderer_dict = {}
    clientconfig = {}
    with open('clientconfig.cfg') as clientclientconfig:
        for line in clientclientconfig:
            line = line.strip()  #Not only for white space but also line return
            line = line.replace(' ', '')
            line = line.split('=')
            if clientconfig.get(line[0]):
                print('Duplicate clientconfig entry ' + str(line[0]) + ' quitting')
                sys.exit()
            else:
                clientconfig[line[0]] = line[1]
        print('Configuration OK')
    rawotherend = []
    otherend = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.bind((clientconfig['localbind1'], 0))
    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s1.bind((clientconfig['localbind2'], 0))
    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s2.bind((clientconfig['localbind3'], 0))
    TUNSETIFF = 0x400454ca
    TUNSETOWNER = TUNSETIFF + 2
    IFF_TUN = 0x0001
    IFF_TAP = 0x0002
    IFF_NO_PI = 0x1000
    tap = open("/dev/net/tun", "r+b",  buffering=0) #os.open is for python 2 ONLY!, it's open in python3
    ifr = struct.pack('16sH', 'pyvpn0'.encode(), IFF_TAP | IFF_NO_PI)
    funcreturn = fcntl.ioctl(tap, TUNSETIFF, ifr)
    second_func_return = fcntl.ioctl(tap, TUNSETOWNER, 1000)
    fl = fcntl.fcntl(tap.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(tap.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
    starting()
    print('Init ok, starting threads')
    mysender = _thread.start_new_thread(sender, ())
    mytaphandler = _thread.start_new_thread(taphandling, ())
    nextsocket = 1
    try:
        inputs = [s2, s1, s]
        outputs = []
        out_queue = []
        in_queue = []
        while True:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            if readable:
                for each in readable:
                    try:
                        preprocess = each.recv(1500)
                        preprocess = preprocess.split(b'&', 1)
                        pos_zero = preprocess[0]
                        preprocess[0] = pos_zero.decode()
                        orderer_dict[preprocess[0]] = preprocess[1]
                    except UnicodeDecodeError:
                        sleep(0.0001)
            sleep(0.0001)
    except BlockingIOError:
        print('sblarf1 :(', sys.exc_info())
        sleep(4)
        pass
        print('sblarf :(', sys.exc_info())
        sleep(5)
    except KeyboardInterrupt:
        sys.exit(0)