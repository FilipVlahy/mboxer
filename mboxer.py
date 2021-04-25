#!/usr/bin/env python3

import socket
import os
import sys
import signal
import hashlib

def header_split(header):

    header = header.strip()
    header = header.split(':')

    id = ''
    value = ''

    if (len(header) != 2):
        return id, value

    if not header[0].isascii():
        return id, value

    if (header[0].find(':') != -1):
        return id, value

    for char in header[0]:
        if (char.isspace()):
            return id, value

    if (header[1].find('/') != -1):
        return id, value
    
    id = header[0]
    value = header[1]

    return id, value

def method_write(headers, f):

    status_code = 100
    status_message = 'OK'

    f_content = ''
    f_name = ''

    m = hashlib.md5()

    try:
        f_content = f.read(int(headers['Content-length']))
        m.update(f_content.endoce('utf-8'))
        f_name= m.hexdigest()

        with open(f'{headers["Mailbox"]}/{f_name}','w') as file:
            file.write(f_content)
    
    except KeyError:
        status_code, status_message = (200, 'Bad request')

    except ValueError:
        status_code, status_message = (200, 'Bad request')

    except FileNotFoundError:
        status_code, status_message = (203, 'No such mailbox')

    return status_code, status_message, f_name, f_content

def method_read(headers):

    status_code = 100
    status_message = 'OK'

    reply_header = ''
    reply_content = ''

    try:
        with open(f'{headers["Mailbox"]}/{headers["Message"]}', 'r') as file:
            reply_content = file.read()
            reply_header = f'Content-length:{len(reply_content)}\n'
    
    except KeyError:
        status_code, status_message = (200, 'Bad request')

    except FileNotFoundError:
        status_code, status_message = (201, 'No such message')

    except OSError:
        status_code, status_message = (202, 'Read error')

    return status_code, status_message, reply_header, reply_header

def method_ls(headers):

    status_code = 100
    status_message = 'OK'

    reply_header = ''
    reply_content = ''

    try:
        dir = os.listdir(headers["Mailbox"])
        reply_header = f'Number-of-messages:{len(dir)}\n'
        reply_content = '\n'.join(dir)+ '\n'

    except KeyError:
        status_code, status_message = (200, 'Bad request')
    
    except FileNotFoundError:
        status_code, status_message = (203, 'No such mailbox')
    
    return status_code, status_message, reply_header, reply_content

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 9999))
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
s.listen(5)

status_code = 100
status_message = 'OK'

method = ''

headers = {}
header = ''
header_id = ''
header_value = ''

reply_header = ''
reply_content = ''

while True:

    client_socket, client_adress = s.accept()
    print(f'Connection with {client_adress}')
    pid_child=os.fork()

    if pid_child == 0:
        s.close()
        f = client_socket.makefile('rw', encoding = 'utf-8')

        while True:

            method = f.readline()
            method = method.strip()

            if not method:
                break

            header = f.readline()

            while header != '\n':
                header_id, header_value = header_split(header)
                headers[header_id] = header_value

                header = f.readline()
            
            print(f'method: {method}')

            if method == 'WRITE':
                status_code, status_message, reply_header, reply_content = method_write(headers, f)
            elif method == 'READ':
                status_code, status_message, reply_header, reply_content = method_read(headers)
            elif method == 'LS':
                status_code, status_message, reply_header, reply_content = method_ls(headers)
            else:
                status_code, status_message = (204, 'Unknown method')

                f.write(f'{status_code} {status_message}\n\n')
                f.flush()
                print('\n\n')
                f.flush()
                sys.exit(0)
            
            f.write(f'{status_code} {status_message}\n')
            f.flush()
            f.write(f'{reply_header}\n')
            f.flush()
            f.write(f'{reply_content}')

        print(f'{client_adress} connection ended')
        sys.exit(0)

    else:
        client_socket.close()