import socket
import sys
import os
from time import sleep
import _thread
import struct
import fcntl
import select
def sender():
    while True:
        try:
            s2.sendto(out_queue.pop(0), (otherend[2][0], otherend[2][1]))
            s1.sendto(out_queue.pop(0), (otherend[1][0], otherend[1][1]))
            s.sendto(out_queue.pop(0), (otherend[0][0], otherend[0][1]))
        except IndexError:
            sleep(0.0001)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print('problem in sender')
            print(sys.exc_info())
    sleep(0.001)
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
    print(s, s1, s2)
    nextsocket = 1
    try:
        inputs = [s, s1, s2]
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
        pass
        print('sblarf :(', sys.exc_info())
    except KeyboardInterrupt:
        sys.exit(0)
    except TimeoutError:
        print('bim, timeout')
        print(sys.exc_info())
        sleep(5)
        pass