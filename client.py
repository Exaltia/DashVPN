#v0.0.4!
import socket
import sys
import os
import _thread
from time import sleep, time
import struct
import fcntl
import select
import random
import binascii
def sender():
    print('sender ready')
    print('with ipv4 packer check')
    while True:
        try:

            s2.sendto(out_queue.pop(0), (clientconfig['remotehost3'], int(clientconfig['remoteport3'])))
            # sleep(0.01)
            s.sendto(out_queue.pop(0), (clientconfig['remotehost1'], int(clientconfig['remoteport1'])))
            s1.sendto(out_queue.pop(0), (clientconfig['remotehost2'], int(clientconfig['remoteport2'])))
            # sleep(0.001)
        except ValueError:
            sleep(0.001)
        except IndexError:
            sleep(0.001)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print('problem in sender')
            print(sys.exc_info())
def taphandling():
    # next_one_out = 0
    # next_one_in = 0
    next_needed = []
    inputs = [tap]
    outputs = [tap]
    previous_sequence = 1 #not zero because zero is used by tcp for starting the sequence numbers
    print('tap handling ready!')
    while True:
        # if next_one_out >= 255:
        #     next_one_out = 0
        # if next_one_in >= 255:
        #     next_one_in = 0
        try:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            if readable:
                pktBytes = tap.read(1500)
                directihlbytes= pktBytes[0:1]
                directihlint = int.from_bytes(directihlbytes, 'big')
                directihlbin = '{0:0{1}b}'.format(directihlint,8)
                realdirectihl = int(directihlbin[4:8], 2) * 4
                tcpheader = pktBytes[realdirectihl:realdirectihl+20]
                #Tcp header start is variable due to possible options and padding in ip header, but what is of interest here, the sequence number, is always at the same position in the tcp header
                tcpheaderInt = int.from_bytes(tcpheader, 'big')
                tcpheaderBin = '{0:0{1}b}'.format(tcpheaderInt,20*8)
                # next_needed.append(int(tcpheaderBin[64:128], 2))
                sequence = (int(tcpheaderBin[32:64], 2))
                out_queue.append(bytes(str(sequence) + '&', 'ascii') + pktBytes)
            else:
                try:
                    # print('je write')
                    # print('next one in is', min(orderer_dict), 'next one out is', next_one_out, end='\r' )
                    # print('Dict len', len(orderer_dict), end='\r')
                    # next_pkt =orderer_dict.pop(min(orderer_dict))
                    # print(next_pkt)
                    next_pkt = in_queue.pop(in_queue.index(min(in_queue)))
                    next_pkt = next_pkt.split(b'&', 1)
                    tap.write(next_pkt[1])
                    # sleep(0.01)
                    # tap.write(in_queue.pop(in_queue.index(random.choice(in_queue))))
                # except struct.error:
                #     raise ValueError()
                    #
                    # sleep(0.001)
                    # print('struct error')
                except KeyError:
                    sleep(0.001)
                except ValueError:
                    # out_queue.append(bytes(str(time()) + '&', 'ascii'))
                    sleep(0.001)
                except ValueError:
                    sleep(0.05)
                except IndexError:
                    sleep(0.001)
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
                        # preprocess = each.recv(1500)
                        # print('preprocess', preprocess)
                        # preprocess = preprocess.split(b'&', 1)
                        # pos_zero = preprocess[0]
                        # # preprocess[0] = float(pos_zero.decode())
                        # orderer_dict[preprocess[0]] = preprocess[1]
                        # print('newest dict entry', orderer_dict[preprocess[0]])
                        in_queue.append(each.recv(1500))#[preprocess[0], preprocess[1]]
                        # print('received')
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