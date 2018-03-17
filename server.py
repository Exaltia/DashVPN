import socket
import sys
import os
from time import sleep, time
import _thread
import struct
import fcntl
import select
import binascii
import configparser
def sender():
    print('sender ready')
    output_sockets = all_sockets
    while True:
        try:
            sx = output_sockets
            next = sx.pop(0)
            sx.append(next)
            next.sendto(out_queue.pop(0), next[1])
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
                    if version == 6:
                        isittcp = int(list(headerBytes[20:21])[0])
                        if isittcp == 6:
                            seqnumber = headerBytes[58:62]  # tcp sequence number position, in bytes
                            seqnumber = binascii.hexlify(seqnumber)
                            if seqnumber:  # Because it trow a value error if seqnumber is empty
                                seqnumber = int(seqnumber, 16) #base16, input is hex, and we want a plain number
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
                        out_queue.append(bytes('other&', 'ascii') + packet)  # We don't care of the order if this is not tcp
                except:
                    print('error form tap ipv4 handling', sys.exc_info())
            else:
                try:
                    if tcp_in_queue:
                        in_queue_index = tcp_in_queue.index(min(tcp_in_queue)) #can't do in one line because it's bytes
                        to_write = tcp_in_queue.pop(in_queue_index)
                        to_write = to_write.split(b'&', 1)
                        tap.write(to_write[1])
                    if other_in_queue:
                        to_write = other_in_queue.pop()
                        to_write = to_write.split(b'&', 1)
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
if __name__ == "__main__":
    output_sockets = []
    connstate = {}
    myconfig = configparser.ConfigParser()
    myconfig.read('serverconfig.cfg')
    all_sockets = []
    print('myconfig', myconfig.sections())
    for each in myconfig.sections():
        connstate[each] = 0
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.bind((myconfig[each]['localbind'], int(myconfig[each]['localport'])))
        all_sockets.append(s)
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
    print('funcreturn', funcreturn)
    second_func_return = fcntl.ioctl(tap, TUNSETOWNER, 1000)
    fl = fcntl.fcntl(tap.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(tap.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
    #No more starting thread, you don't need to restart the server each time you loose the client
    print('Init OK')
    mysender = _thread.start_new_thread(sender, ())
    mytaphandler = _thread.start_new_thread(taphandling, ())
    nextsocket = 1
    connstate['initOK'] = 0
    try:
        inputs = all_sockets
        outputs = []
        exception_sockets = []
        out_queue = []
        tcp_in_queue = []
        other_in_queue = []
        while True:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            print('results', inputs, outputs)
            diff = set(readable) ^ set(inputs)
            if readable:
                for each in readable:
                    try:
                        print('readable')
                        preprocess = each.recvfrom(1500)
                        print('packet', preprocess)
                        if preprocess[0] == b'#Blanacetonport':
                            print('je balance')
                            for entry in myconfig.sections():
                                if myconfig[entry]['localport'] in str(each.getsockname()[1]):
                                    connstate[entry] = 2, preprocess[1]
                                    each.sendto(bytes('Got#Blanacetonport', 'ascii'), preprocess[1])
                                if len(connstate) == 3:
                                    connstate['initOK'] = 1
                        elif preprocess[0] == b'RECONNECT':
                            print('reconnecting')
                            for entry in myconfig.sections():
                                if str(each.getsockname()[1]) in myconfig[entry]['localport'] and connstate[entry][0] <= 2:
                                    connstate[entry] = 2, preprocess[1]
                                    output_sockets.append(each)
                                    each.send(bytes('RECONNECTED', 'ascii'))
                        elif preprocess[0] == b'PING':
                            for entry in myconfig.sections():
                                print(connstate[entry])
                                # sleep(10)
                                if str(each.getsockname()[1]) in myconfig[entry]['localport'] and connstate[entry][0] <= 2:
                                    print('pong from s')
                                    connstate[entry] = 2, preprocess[1]
                                    each.send(bytes('PONG', 'ascii'))
                        elif preprocess[0] == b'PONG':
                            for entry in myconfig.sections():
                                if str(each.getsockname()[1]) in myconfig[entry]['localport'] and connstate[entry][0] <= 2:
                                    print('pong from s')
                                    connstate[entry] = 2, preprocess[1]
                        # The & check is to be sure that it's not a control or a malformed packet, and packets received with an 'id' of other are not tcp
                        elif b'&' in preprocess[0] and not preprocess[0].startswith(b'other'):
                            tcp_in_queue.append(preprocess[0])
                        else:
                            other_in_queue.append(preprocess[0])
                    except UnicodeDecodeError:
                        sleep(0.0001)
                for each in diff:
                    if connstate['initOK'] == 1:
                        # We want to not remove the link from the available ones too fast, so we need 2 passes before removing the connection from the list of the available ones, will still poping it out at the setted up time delay
                        try:
                            if lasttime < time() - my_timeout_value / 2:
                                lasttime = time()
                                for entry in myconfig.sections():
                                    # for subentry in myconfig[entry]['remoteport']:
                                    if myconfig[entry]['localport'] in str(each.getsockname()[1]):
                                        print('connstate', connstate)
                                        sleep(10)
                                        if connstate[entry][0] <= 2 and connstate[entry][0] > 0:
                                            each.send(bytes('PING', 'ascii'))
                                            print('found entry', entry)
                                            connstate[entry][0] -= 1
                                        else:
                                            print('removing socket')
                                            connstate[entry][0] = 0
                                            output_sockets.pop(output_sockets.index(each))
                                            # each.send(bytes('RECONNECT', 'ascii'))
                        except ValueError:
                            sleep(0.001)
                        except:
                            print('global error', sys.exc_info())
                            print(sys.exc_info())
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            print(exc_type, fname, exc_tb.tb_lineno)
                            sleep(10)
                            pass
            sleep(0.0001)
            if not readable and connstate['initOK'] == 1:
                for each in inputs:
                    if lasttime < time() - my_timeout_value / 2:
                        lasttime = time()
                        for entry in myconfig.sections():
                            if myconfig[entry]['localport'] in str(each.getsockname()[1]):
                                each.send(bytes('PING', 'ascii'))
                                connstate[entry] =- 1
    except KeyError:
        sleep(0.001)
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
        print(sys.exc_info())
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        sleep(10)