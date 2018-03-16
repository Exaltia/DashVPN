import socket
import sys
import os
from time import sleep, time
import _thread
import struct
import fcntl
import select
import binascii
def sender():
    print('sender ready')
        # print('sent!!')


        # s2.sendto(out_queue.pop(0), (otherend[2][0], otherend[2][1]))
        # s1.sendto(out_queue.pop(0), (otherend[1][0], otherend[1][1]))
        # s.sendto(out_queue.pop(0), (otherend[0][0], otherend[0][1]))
        # print('really sent!!')
    while True:

        try:
            sx2 = sx
            next = sx2.pop(0)
            # print(sx)
            sx2.append(next)
            next[0].sendto(out_queue.pop(0), next[1])
        except IndexError:
            sleep(0.0001)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print('problem in sender')
            print(sys.exc_info())
    sleep(0.001)
def taphandling():

    inputs = [tap]
    outputs = [tap]
    print('tap handling ready!')
    while True:
        try:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            if readable:
                try:
                    #This code works ONLY in tap mode and ipv6 communication inside the tunnel
                    #Todo : Tun mode, where we need to remove 14 bytes of ethernet header
                    #Todo : ipv4 mode, where we need to remove another 20 bytes of ip header and look at the 9th byte for "Protocol"(called next header in IPv6) instead of the 6th byte, but still wanting to find 6 in either cases(TCP)
                    packet = tap.read(1500)
                    headerLength = 74 #14(ethernet)+40(ipv6)+20(something else, including tcp, because we want to search in tcp header without options)
                    headerBytes = packet[0:headerLength] #We are getting an ethernet frame containing ip(v6) then something else
                      # We get the service type
                    version = headerBytes[14:15]
                    version = int.from_bytes(version, 'big')
                    version = '{0:0{1}b}'.format(version,1*8)  # IP version number is 4 bytes, we must transforme the byte in bits to ensure correct calculation of Ip version
                    version = version[0:4]
                    version = int(version, 2)
                    # print('version', version)
                    if version == 6:
                        isittcp = int(list(headerBytes[20:21])[0])
                        if isittcp == 6:
                            seqnumber = headerBytes[58:62]  # tcp sequence number position, in bytes
                            seqnumber = binascii.hexlify(seqnumber)
                            if seqnumber:  # Because it trow a value error if seqnumber is empty
                                seqnumber = int(seqnumber, 16) #base16, input is hex, and we want a plain number
                                # print('seqnumber ipv6', seqnumber)
                                out_queue.append(bytes(str(seqnumber) + '&', 'ascii') + packet)  # because packets are sent over unequal links, and tcp doesn't like unordered packets
                        else:
                            # just in case something was wrong with the seqnumber, better send an out of order packet than to loose it
                            out_queue.append(bytes('other&', 'ascii') + packet)
                    if version == 4:
                        # 14 from ethernet header then 9 for the start of the protocol
                        isittcp = int(list(headerBytes[23:24])[0])
                        if isittcp == 6:
                            # Because ipv4 header lengh is variable, if it's not calculated right we could miss the sequence number
                            ihl = headerBytes[14:15]
                            ihl = int.from_bytes(ihl, 'big')
                            ihl = '{0:0{1}b}'.format(ihl,1*8)
                            ihl = ihl[4:8]
                            ihl = int(ihl, 2)
                            ihl = ihl * 4  # because it's half a byte
                            seqnumber = headerBytes[14+ihl+4:14+ihl+8]  # tcp sequence number position, in bytes
                            seqnumber = binascii.hexlify(seqnumber)
                            if seqnumber:  # Because it trow a value error if seqnumber is empty
                                seqnumber = int(seqnumber, 16) #base16, input is hex, and we want a plain number
                            # print('seqnumber ipv4', seqnumber)
                            out_queue.append(bytes(str(seqnumber) + '&', 'ascii') + packet)  # because packets are sent over unequal links, and tcp doesn't like unordered packets
                        else:
                            # just in case something was wrong with the seqnumber, better send an out of order packet than to loose it
                            out_queue.append(bytes('other&', 'ascii') + packet)
                    else:
                        out_queue.append(bytes('other&', 'ascii') + packet)  # We don't care of the order if this is not tcp
                        # print('out_queue', out_queue)
                except:
                    print('error form tap ipv4 handling', sys.exc_info())

            # if writable:
            else:
                try:
                    # print('try to write')
                    # stuckcounter = 0
                    # while stuckcounter >= 3:
                    # if bytes(next_one_in) + b'&' not in min(tcp_in_queue):
                    #     sleep(0.0001)
                    #     stuckcounter +=1
                    # stuckcounter = 0
                    # print('queues, tcp and other', tcp_in_queue, other_in_queue)
                    if tcp_in_queue:
                        # print('writing tcp')
                        in_queue_index = tcp_in_queue.index(min(tcp_in_queue)) #can't do in one line because it's bytes
                        to_write = tcp_in_queue.pop(in_queue_index)
                        to_write = to_write.split(b'&', 1)
                        # next_one_in = int(to_write[0])
                        tap.write(to_write[1])
                    if other_in_queue:
                        # print('writing other')
                        to_write = other_in_queue.pop()
                        to_write = to_write.split(b'&', 1)
                        # print('to write other', to_write)
                        tap.write(to_write[1])
                    sleep(0.0001)
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
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    sleep(10)
        except KeyboardInterrupt:
            sys.exit(0)
        except ValueError:
            sys.exit(1)
            sleep(0.001)
        except:
            print('error from taphandling')
            print(sys.exc_info())
    sleep(0.001)
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
    print('otherend'), otherend
if __name__ == "__main__":
    sx = []
    lasttime = float()
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
    # s.settimeout(my_timeout_value)
    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s1.bind(('0.0.0.0', int(config['localport2'])))
    # s1.settimeout(my_timeout_value)
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
    sx = [(s2, (otherend[2][0], otherend[2][1])),
          (s1, (otherend[1][0], otherend[1][1])),
          (s, (otherend[0][0], otherend[0][1]))]
    print(s, s1, s2)
    nextsocket = 1
    try:
        connstate = [2, 2, 2] # Assuming that all links are working at the client start
        inputs = [s, s1, s2]
        outputs = []
        exception_sockets = []
        out_queue = []
        tcp_in_queue = []
        other_in_queue = []
        while True:
            readable, writable, exceptional = select.select(inputs, outputs, inputs, 5)
            # print('readable', readable)
            # sleep(0.3)
            diff = set(readable) ^ set(inputs)
            if readable:
                # print('timeout value', s.gettimeout())
                # print('still readable!')
                # sleep(0.3)
                for each in readable:
                    try:
                        preprocess = each.recvfrom(1500)
                        if preprocess[0] == b'RECONNECT':
                            print('reconnecting')
                            if each == s:
                                otherend[0] = preprocess[1]
                                # otherend[0][1] = preprocess[1][1]
                                sx.append((s, (otherend[0][0],  otherend[0][1])))
                            if each == s1:
                                otherend[1] = preprocess[1]
                                # otherend[1][1] = preprocess[1][1]
                                sx.append((s1, (otherend[1][0],  otherend[1][1])))
                            if each == s2:
                                otherend[2] = preprocess[1]
                                # otherend[2][1] = preprocess[1][1]
                                sx.append((s2, (otherend[2][0],  otherend[2][1])))
                            # sx.append((each, (clientconfig['remotehost1'], int(clientconfig['remoteport1']))))

                        if preprocess[0] == b'PING':
                            # print('ping')
                            if each == s and connstate[0] <= 2:
                                print('pong from s')
                                connstate[0] = 2
                            elif each == s1 and connstate[1] <= 2:
                                print('pong from s')
                                connstate[1] = 2
                            elif each == s2 and connstate[2] <= 2:
                                print('pong from s')
                                connstate[0] = 2
                        # The & check is to be sure that it's not a control or a malformed packet, and packets received with an 'id' of other are not tcp
                        if b'&' in preprocess[0] and not preprocess[0].startswith(b'other'):
                            tcp_in_queue.append(preprocess[0])
                        else:
                            other_in_queue.append(preprocess[0])
                    except UnicodeDecodeError:
                        sleep(0.0001)
                for each in diff:
                    # unlike on client, we don't remove inputs
                    try:
                        if lasttime < time() - my_timeout_value:
                            lasttime = time()
                            if each == s and connstate[0] == 2:
                                print('ping from s')
                                # if each not in sx:
                                each.sendto(bytes('PONG', 'ascii'), (otherend[0][0], otherend[0][1]))
                                connstate[0] = 1
                            elif each == s1 and connstate[1] == 2:
                                each.sendto(bytes('PONG', 'ascii'), (otherend[1][0], otherend[1][1]))
                                connstate[1] = 1
                            elif each == s2 and connstate[2] == 2:
                                print('connstate', connstate)
                                each.sendto(bytes('PONG', 'ascii'), (otherend[2][0], otherend[2][1]))
                                connstate[2] = 1
                            elif connstate[0] == 1:
                                if lasttime < time() - my_timeout_value *2:
                                    print('removing socket s')
                                    sx.pop(sx.index(s))
                                    connstate[0] = 0
                            elif connstate[1] == 1:
                                if lasttime < time() - my_timeout_value *2:
                                    print('removing socket s1')
                                    sx.pop(sx.index(s1))
                                    connstate[1] = 0
                            elif connstate[2] == 1:
                                if lasttime < time() - my_timeout_value *2:
                                    print('removing socket s2')
                                    sx.pop(sx.index(s2))
                                    connstate[2] = 0
                    except ValueError:
                        sleep(0.001)
                    except:
                        print(sys.exc_info())
                        pass
                # if exceptional:
                #     for each in exceptional:
                #         if each == s and connstate[0] > 0:
                #             inputs.append(exception_sockets.pop(exception_sockets.index(s)))
                #             each.sendto(bytes('RECONNECT', 'ascii'), (clientconfig['remotehost1'], int(clientconfig['remoteport1'])))
                #         elif each == s1 and connstate[1] > 0:
                #             # sx.append((s1, (clientconfig['remotehost2'], int(clientconfig['remoteport2']))))
                #             inputs.append(exception_sockets.pop(exception_sockets.index(s1)))
                #             each.sendto(bytes('RECONNECT', 'ascii'), (clientconfig['remotehost2'], int(clientconfig['remoteport2'])))
                #         elif each == s2 and connstate[2] > 0:
                #             # sx.append((s2, (clientconfig['remotehost3'], int(clientconfig['remoteport3']))))
                #             inputs.append(exception_sockets.pop(exception_sockets.index(s2)))
                #             each.sendto(bytes('RECONNECT', 'ascii'), (clientconfig['remotehost3'], int(clientconfig['remoteport3'])))
            sleep(0.0001)
            if not readable:
                for each in inputs:
                    if lasttime < time() - my_timeout_value / 2:
                        lasttime = time()
                        if each == s:
                            each.sendto(bytes('PONG', 'ascii'), (otherend[0][0], otherend[0][1]))
                        elif each == s1:
                            each.sendto(bytes('PONG', 'ascii'), (otherend[1][0], otherend[1][1]))
                        elif each == s2:
                            each.sendto(bytes('PONG', 'ascii'), (otherend[2][0], otherend[2][1]))
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
        print('global error', sys.exc_info())