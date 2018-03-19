#v0.0.4!
import socket
import sys
import os
import _thread
from time import sleep
import struct
import fcntl
import select
import binascii
import configparser
from time import time
def sender():
    print('sender ready')
    # output_sockets = all_sockets
    while True:
        #Take one connexion pop it and send it, allowing better tolerance against a link loss or flap
        try:
            sx = output_sockets
            # print('sender sx', len(sx))
            # print('sender sx2', len(sx2))
            # sleep(0.7)
            next = sx.pop(0)
            # next = sx[0]
            # print('sx lenght', len(sx), end='\r')
            # print('next!', next)
            # sleep(0.3)
            # print('next', next[1], 'type', type(next[1]))
            # sleep(10)
            sx.append(next)
            # print('next', next)
            # sleep(3)
            next[0].sendto(out_queue.pop(0), next[1])
        except IndexError:
            # print('index error!')
            sleep(0.0001)
        except KeyboardInterrupt:
            sys.exit(0)
        except:

            print(sys.exc_info())
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            sleep(10)
def taphandling():
    next_one_out = 0
    next_one_in = 0
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
                    # print('at the beggining', packet)
                    headerLength = 74 #14(ethernet)+40(ipv6)+20(something else, including tcp, because we want to search in tcp header without options)
                    headerBytes = packet[0:headerLength] #We are getting an ethernet frame containing ip(v6) then something else
                    # We get the service type
                    version = headerBytes[14:15]
                    version = int.from_bytes(version, 'big')
                    version = '{0:0{1}b}'.format(version,1*8)  # IP version number is 4 bytes, we must transforme the byte in bits to ensure correct calculation of Ip version
                    version = version[0:4]
                    version = int(version, 2)
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
                            out_queue.append(bytes(str(seqnumber) + '&', 'ascii') + packet)  # because packets are sent over unequal links, and tcp doesn't like unordered packets
                        else:
                            # just in case something was wrong with the seqnumber, better send an out of order packet than to loose it
                            out_queue.append(bytes('other&', 'ascii') + packet)
                    else:
                        out_queue.append(bytes('other&', 'ascii') + packet) # We don't care of the order if this is not tcp
                except:
                    print('error form tap ipv4 handling', sys.exc_info())
            else:
                try:
                    if tcp_in_queue:
                        in_queue_index = tcp_in_queue.index(min(tcp_in_queue)) #can't do in one line because it's bytes
                        to_write = tcp_in_queue.pop(in_queue_index)
                        to_write = to_write[0].split(b'&', 1)  # We receive data from recvfrom function, who is a tuple with the data then the sender, and we don't care of the later here
                        tap.write(to_write[1])
                    if other_in_queue:
                        to_write = other_in_queue.pop(0)
                        print('to write', to_write)
                        # sleep(15)
                        to_write = to_write[0].split(b'&', 1)
                        tap.write(to_write[1])
                    sleep(0.0001)
                except KeyError:
                    sleep(0.0001)
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
            sleep(0.001)
        except:
            print('error from taphandling')
            print(sys.exc_info())
    sleep(0.001)
def starting():
    print('Initializing')
    try:
        outputs = all_sockets
        inputs = all_sockets
        # print('ca try')
        # print('len connstate', len(connstate))
        while len(connstate) < 3:
            for startsocket in all_sockets:
                for configentry in myconfig.sections():
                    if myconfig[configentry]['localbind'] in startsocket.getsockname()[0]:
                        startsocket.sendto(bytes('#Blanacetonport', 'ascii'), (myconfig[configentry]['remotehost'], int(myconfig[configentry]['remoteport'])))
                        print('still doing init...')
                        sleep(0.1)
                        startpacket = startsocket.recvfrom(1500)
                        if b'Got#Blanacetonport' in startpacket[0]:
                            # print('got packet')
                            # sleep(1)
                            connstate[configentry] = [2, startpacket[1]]
                            output_sockets.append((startsocket, startpacket[1]))
                            # startsocket.connect(startpacket[1])
                            # print('len connstate', len(connstate))
                        else:
                            print('debug', startpacket)
                            # sleep(10)
    except:
        print('global error starting')
        print(sys.exc_info())
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        sleep(1)
            # try:
            #     print('boucle true')
            #     # sleep(1)
            #     print('inputs', inputs)
            #     # sleep(1)
            #     readable, writable, exceptional = select.select(inputs, outputs, inputs)
            #     for startsocket in all_sockets:
            #         for configentry in myconfig.sections():
            #             print('configentry', configentry)
            #             # sleep(1)
            #             if myconfig[configentry]['localbind'] in str(startsocket.getsockname()[0]):
            #                 print('send message')
            #                 startsocket.sendto(bytes('#Blanacetonport', 'ascii'), (myconfig[configentry]['remotehost'], int(myconfig[configentry]['remoteport'])))
            #                 print('connstate from send', connstate)
            #                 sleep(0.001)
            #         while readable:
            #             print('readable')
            #             for mysocket in readable: #Don't use each, shadowed!
            #                 packet = mysocket.recvfrom(1500)
            #                 for configentry in myconfig.sections():
            #                     print('entry')
            #                     try:
            #                         print('type', type(connstate))
            #                         # sleep(10)
            #                         print('packet type', type(packet[1][1]))
            #                         sleep(5)
            #                         if connstate[configentry]['remoteport'] in str(packet[1][1]):#Can't reuse entry as first parameter for for, it is shadowed
            #
            #                             print('there is something')
            #                             print(connstate[entry])
            #                             # sleep(5)
            #                             # pass
            #                     except KeyError:
            #                         sleep(0.001)
            #                     except TypeError:
            #                         print('type error :(', print(packet))
            #                         sleep(30)
            #                     if packet[0] == b'Got#Blanacetonport':
            #                         print('got answer')
            #                         connstate[configentry] = 2, packet[1]


                # else:
                    # for each in all_sockets:
                    #     for configentry in myconfig.sections():
                    #         print('configentry', configentry)
                    #         # sleep(1)
                    #         if myconfig[configentry]['localbind'] in str(each.getsockname()[0]):
                    #             print('send message')
                    #             each.sendto(bytes('#Blanacetonport', 'ascii'), (myconfig[configentry]['remotehost'], int(myconfig[configentry]['remoteport'])))
                    #             print('connstate from send', connstate)
                    #             sleep(0.001)
            # print('end')
    #         except KeyboardInterrupt:
    #             sys.exit(0)
    #         except OSError:
    #             sleep(0.001)
    # except KeyboardInterrupt:
    #     sys.exit(0)
    # except:
    #     print('global error starting')
    #     print(sys.exc_info())
    #     exc_type, exc_obj, exc_tb = sys.exc_info()
    #     fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    #     print(exc_type, fname, exc_tb.tb_lineno)
    #     sleep(1)
    #     pass
if __name__ == "__main__":
    output_sockets = []
    myconfig = configparser.ConfigParser()
    myconfig.read('clientconfig.cfg')
    all_sockets = []
    # print('myconfig', myconfig.sections())
    for each in myconfig.sections():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.bind((myconfig[each]['localbind'], 0))
        all_sockets.append(s)
    # print('all sockets', all_sockets)
    # print('configtest', myconfig[each])
    out_queue = []
    tcp_in_queue = []
    other_in_queue = []
    lasttime = float()
    my_timeout_value = 3
    rawotherend = []
    otherend = []
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
    connstate = {}
    starting()
    # print('len consnstate main', len(connstate))
    print('Init ok, starting threads')
    mysender = _thread.start_new_thread(sender, ())
    mytaphandler = _thread.start_new_thread(taphandling, ())
    nextsocket = 1
    try:
        inputs = all_sockets
        outputs = []
        exception_sockets = []
        out_queue = []
        tcp_in_queue = []
        other_in_queue = []
        while True:
            readable, writable, exceptional = select.select(inputs, outputs, inputs, 5)
            diff = set(readable) ^ set(inputs)
            if readable:
                for each in readable:
                    try:
                        preprocess = each.recvfrom(1500)
                        if preprocess[0] == b'PONG':
                            for each in myconfig.sections():
                                # print(connstate)
                                #like the server, connstate is a tuple inside a dict entry
                                if str(preprocess[1][1]) in myconfig[each]['remoteport'] and connstate[each][0] <= 2:
                                    # print('pong from s')
                                    connstate[each] = [2, preprocess[1]]
                        elif preprocess[0] == b'PING':
                            for each in myconfig.sections():
                                if str(preprocess[1][1]) in myconfig[each]['remoteport'] and connstate[each][0] <= 2:
                                    # print('pong from s')
                                    connstate[each] = [2, preprocess[1]]
                        elif preprocess[0] == b'RECONNECTED':
                            print('got reconnected')
                            output_sockets.append(each)
                        # The & check is to be sure that it's not a control or a malformed packet, and packets received with an 'id' of other are not tcp
                        if b'&' in preprocess and not preprocess.startswith(b'other'):
                            tcp_in_queue.append(preprocess)
                        elif preprocess[0].startswith(b'other'):
                            other_in_queue.append(preprocess)
                        else:
                            sleep(0.001)
                            pass
                    except UnicodeDecodeError:
                        sleep(0.0001)
            if lasttime < time() - my_timeout_value /2 :
                lasttime = time()
                for each in inputs:
                    # We want to not remove the link from the available ones too fast, so we need 2 passes before removing the connection from the list of the available ones, will still poping it out at the setted up time delay
                    try:

                            for entry in myconfig.sections():
                                if myconfig[entry]['localbind'] in str(each.getsockname()[0]):
                                    if connstate[entry][0] <= 2 and connstate[entry][0] > 0:
                                        each.sendto(bytes('PING', 'ascii'), (myconfig[entry]['remotehost'], int(myconfig[entry]['remoteport'])))
                                        # print('found entry', entry)
                                        connstate[entry][0] -= 1
                                    else:
                                        print('removing socket', connstate[entry])
                                        connstate[entry][0] = 0
                                        print(each)
                                        output_sockets.pop(output_sockets.index((each, connstate[entry][1])))
                                        print('reconnecting')
                                        each.sendto(bytes('RECONNECT', 'ascii'), myconfig[entry]['remotehost'], int(myconfig[entry]['remoteport']))

                    except ValueError:
                        sleep(0.001)
                    except:
                        print(sys.exc_info())
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print(exc_type, fname, exc_tb.tb_lineno)
                        sleep(10)
                        pass

            sleep(0.0001)
            # if not readable:
            #     print('not readable')
            #     for each in inputs:
            #         if lasttime < time() - my_timeout_value / 2:
            #             lasttime = time()
            #             for entry in myconfig.sections():
            #                 # forsubentry in myconfig[entry]['remoteport']:
            #                 if myconfig[entry]['localbind'] in str(each.getsockname()[0]):
            #                     each.sendto(bytes('PING', 'ascii'), (myconfig[entry]['remotehost'], int(myconfig[entry]['remoteport'])))
    except TimeoutError:
        print('timeout error!')
    except BlockingIOError:
        print('sblarf1 :(', sys.exc_info())
        sleep(4)
        pass
        print('sblarf :(', sys.exc_info())
        sleep(5)
    except KeyboardInterrupt:
        sys.exit(0)