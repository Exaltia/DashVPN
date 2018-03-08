import socket,sys,os, io
import multiprocessing.queues
from time import sleep
import multiprocessing as mp
import struct, asyncio
import fcntl, select
def starting():
    # mycard = io.BytesIO()

    # s2.setblocking(0)
    i = 0
    print('je suis main')
    # try:
    print('je try hard.')
    # q = mp.Queue()
    # global bordel_a_paquets
    # bordel_a_paquets = {}
    # bordel_a_paquets['coucou'] = ''
    # q = Queue()

    print('ok')

    # while b'#Balancetonport' not in rawotherend:
    # while len(rawotherend) < 3:
    try:
        print(clientconfig['remotehost1'])
        s.sendto(bytes('#Balancetonport', 'ascii'), (clientconfig['remotehost1'], int(clientconfig['remoteport1'])))
        print('sent')
        sleep(1)
        s1.sendto(bytes('#Balancetonport', 'ascii'), (clientconfig['remotehost2'], int(clientconfig['remoteport2'])))
        sleep(1)
        s2.sendto(bytes('#Balancetonport', 'ascii'), (clientconfig['remotehost3'], int(clientconfig['remoteport3'])))
        sleep(1)
        print('deux', s, s1, s2)
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print(sys.exc_info())
    # print(rawotherend)
    # sleep(3)
    # for row in rawotherend:
    #     # print('row', row[1])
    #     otherend.append(row[1])
    #     print(otherend)
    #     # sleep(3)
    # print('other end is', otherend)
if __name__ == "__main__":
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
    rawotherend = []
    otherend = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.bind((clientconfig['localbind1'], 0))

    # s.settimeout(0.1)
    # s.setblocking(0)
    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s1.bind((clientconfig['localbind2'], 0))
    # s1.setblocking(0)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s2.bind((clientconfig['localbind3'], 0))
    print(s, s1, s2)
    TUNSETIFF = 0x400454ca
    TUNSETOWNER = TUNSETIFF + 2
    IFF_TUN = 0x0001
    IFF_TAP = 0x0002
    IFF_NO_PI = 0x1000
    tap = open("/dev/net/tun", "r+b",  buffering=0) #os.open is for python 2 ONLY!, it's open in python3
    # readtap = open("/dev/net/tun", "rb")
    ifr = struct.pack('16sH', 'pyvpn0'.encode(), IFF_TAP | IFF_NO_PI)
    funcreturn = fcntl.ioctl(tap, TUNSETIFF, ifr)
    print('funcreturn', funcreturn)
    second_func_return = fcntl.ioctl(tap, TUNSETOWNER, 1000)
    fl = fcntl.fcntl(tap.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(tap.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
    starting()
    print(s, s1, s2)
    nextsocket = 1
    try:
        inputs = [s, s1, s2, tap]
        outputs = [s, s1, s2]
        out_queue = []
        while True:
            # print('je tru(elle)')
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            # print('results!', readable, writable, exceptional)
            # sleep(10)
            if readable:
                # print('yep, readable but...')
                # sleep(1)
                for each in readable:
                    if 'socket' in str(each):
                        # print('this is a socket')
                        tap.write(each.recv(1500))
                    if 'FileIO' in str(each):
                        # print('this is a file')
                        out_queue.append(each.read(1500))
                        # print(each.read(1500))
            # print(writable)
            if writable:
                if len(out_queue) >= 1:

                    # testtype = str(writable)
                    # print(type(testtype))
                    # sleep(10)
                    # print("j'ai un truc a envoyer")
                    # sleep(1)
                    # for row in writable:
                    try:
                        # print(writable)
                        if nextsocket == 1:#"""if str(clientconfig['remoteport1']) in str(writable) and"""
                            s.sendto(out_queue.pop(0), (clientconfig['remotehost1'], int(clientconfig['remoteport1'])))
                            nextsocket = 2
                            # print('sock1')
                            # print('sent from 4242!')
                            # sleep(1)
                        if nextsocket == 2:#"""if str(clientconfig['remoteport2']) in str(writable) and """
                            s1.sendto(out_queue.pop(0), (clientconfig['remotehost2'], int(clientconfig['remoteport2'])))
                            nextsocket = 3
                            # print(otherend[1][0], otherend[1][1])
                            # print('sock2')
                        if nextsocket == 3:#"""if str(clientconfig['remoteport3']) in str(writable) and"""
                            s2.sendto(out_queue.pop(0), (clientconfig['remotehost3'], int(clientconfig['remoteport3'])))
                            nextsocket = 1
                            # print(otherend[2][0], otherend[2][1])
                            # print('sock3')
                    except IndexError:
                        pass
                    except KeyboardInterrupt:
                        sys.exit(0)
                    except:
                        print(sys.exc_info())
                    # sleep(5)
            sleep(0.001)

            # sleep(1)
    except BlockingIOError:
        print('sblarf1 :(', sys.exc_info())
        sleep(4)
        pass
        print('sblarf :(', sys.exc_info())
        sleep(5)
    except KeyboardInterrupt:
        sys.exit(0)