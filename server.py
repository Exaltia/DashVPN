import socket
import sys
import os
from time import sleep, time
import _thread
import struct
import fcntl
import select
import random
import binascii
def sender():
    while True:

        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        try:
            # print('out_queue len', len(out_queue), end='\r')
            # print('out queue', out_queue)
            s2.sendto(out_queue.pop(0), (otherend[2][0], otherend[2][1]))
            #Was : s2.sendto(out_queue.pop(out_queue.index(min(out_queue))), (otherend[2][0], otherend[2][1]))
            # sleep(0.03)
            s.sendto(out_queue.pop(0), (otherend[0][0], otherend[0][1]))
            s1.sendto(out_queue.pop(0), (otherend[1][0], otherend[1][1]))
            # sleep(1)
        except ValueError:
            sleep(0.001)
        except IndexError:
            sleep(0.001)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print('problem in sender')
            print(sys.exc_info())
    sleep(0.001)
def taphandling():
    next_needed = []
    # next_one_out = 0
    # next_one_in = 0
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
                sequence = int(tcpheaderBin[32:64], 2)
                out_queue.append(bytes(str(sequence) + '&', 'ascii') + pktBytes)
            else:
                try:
                    # pass
                    # tap.write(in_queue.pop(in_queue.index(random.choice(in_queue))))
                    # print('Dict len', len(orderer_dict), end='\r')
                    # print('why writable?')
                    next_pkt = in_queue.pop(in_queue.index(min(in_queue)))
                    next_pkt = next_pkt.split(b'&', 1)
                    sequence = int(tcpheaderBin[64:128], 2)
                    tap.write(next_pkt[1])
                    # sleep(0.01)
                    # print('next_pkt written', next_pkt)
                except KeyError:
                    print('key error')
                    sleep(0.001)
                except ValueError:
                    # print('value error here1')
                    sleep(0.05)
                except IndexError:
                    sleep(0.001)
                except:
                    print('else error?')
                    print(sys.exc_info())
        # except struct.error:
        #     out_queue.append(bytes(str(time()) + '&', 'ascii'))
        #     sleep(0.001)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print('error from taphandling')
            print(sys.exc_info())
def liststate():
    allseq = []
    while True:
        for row in in_queue:
            lineresult = row.split(b'&',1)
            allseq.append(lineresult[0])
        print(allseq)
        sleep(5)
def starting():
    print('Initializing')
    print(rawotherend)
    while len(rawotherend) < 3:
        try:
            rawotherend.append(s.recvfrom(1500))
            rawotherend.append(s1.recvfrom(1500))
            rawotherend.append(s2.recvfrom(1500))
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print(sys.exc_info())
        print(rawotherend)
        sleep(3)
    for row in rawotherend:
        otherend.append(row[1])
if __name__ == "__main__":
    orderer_dict = {}
    config = {}
    with open('serverconfig.cfg') as serverconf:
        for line in serverconf:
            line = line.strip() #Not only for white space but also line return, Todo: "".join(sentence.split())
            line = line.replace(' ', '')
            line = line.split('=')
            if config.get(line[0]):
                print('Duplicate config entry ' + str(line[0]) + ' quitting')
                sys.exit()
            else:
                config[line[0]] = line[1]
        print('Configuration OK')

    my_timeout_value = 3
    retries = 4
    rawotherend = []
    otherend = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP,)
    # print(dir(s))
    s.bind(('0.0.0.0', int(config['localport1'])))
    print(s)
    s.settimeout(my_timeout_value)
    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s1.bind(('0.0.0.0', int(config['localport2'])))
    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s2.bind(('0.0.0.0', int(config['localport3'])))
    TUNSETIFF = 0x400454ca
    TUNSETOWNER = TUNSETIFF + 2
    IFF_TUN = 0x0001
    IFF_TAP = 0x0002
    IFF_NO_PI = 0x1000
    tap = open("/dev/net/tun", "r+b",  buffering=0) #os.open is for python 2 ONLY!, it's open in python3
    ifr = struct.pack('16sH', 'pyvpn0'.encode(), IFF_TAP | IFF_NO_PI)
    funcreturn = fcntl.ioctl(tap, TUNSETIFF, ifr)
    print('funcreturn', funcreturn)
    second_func_return = fcntl.ioctl(tap, TUNSETOWNER, 1000)
    fl = fcntl.fcntl(tap.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(tap.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
    starting()
    print('Init OK')
    mysender = _thread.start_new_thread(sender, ())
    mytaphandler = _thread.start_new_thread(taphandling, ())
    mystateresult = _thread.start_new_thread(liststate, ())
    print(s, s1, s2)
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
                        # preprocess[0] = float(pos_zero.decode())
                        # orderer_dict[preprocess[0]] = preprocess[1]
                        # print('newest dict entry', orderer_dict[preprocess[0]])
                        in_queue.append(each.recv(1500))#[preprocess[0], preprocess[1]]
                    except UnicodeDecodeError:
                        sleep(0.0001)

            sleep(0.0001)
    except BlockingIOError:
        print('sblarf1 :(', sys.exc_info())
        pass
        print('sblarf :(', sys.exc_info())
    except KeyboardInterrupt:
        sys.exit(0)
    except TimeoutError:
        print('bim, timeout')
        print(sys.exc_info())
        sleep(5)
        pass
    except:
        print('global error')
        print(sys.exc_info())