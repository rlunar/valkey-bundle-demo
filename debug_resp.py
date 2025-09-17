#!/usr/bin/env python3
"""
Debug script to show raw RESP protocol bytes
"""
import socket
import sys

def debug_resp_command(host='localhost', port=6379, command='PING'):
    """Send a command and show the raw RESP bytes"""
    
    # Create socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    
    # Encode command as RESP
    if command == 'PING':
        resp_command = b'*1\r\n$4\r\nPING\r\n'
    elif command.startswith('GET '):
        key = command[4:]
        resp_command = f'*2\r\n$3\r\nGET\r\n${len(key)}\r\n{key}\r\n'.encode()
    else:
        # Simple command encoding
        parts = command.split()
        resp_command = f'*{len(parts)}\r\n'.encode()
        for part in parts:
            resp_command += f'${len(part)}\r\n{part}\r\n'.encode()
    
    print(f"Sending RESP bytes:")
    print(f"Raw: {resp_command}")
    print(f"Hex: {resp_command.hex()}")
    print(f"Readable: {repr(resp_command)}")
    print()
    
    # Send command
    sock.send(resp_command)
    
    # Receive response
    response = sock.recv(1024)
    
    print(f"Received RESP bytes:")
    print(f"Raw: {response}")
    print(f"Hex: {response.hex()}")
    print(f"Readable: {repr(response)}")
    print()
    
    # Parse response
    if response.startswith(b'+'):
        print(f"Simple String: {response[1:-2].decode()}")
    elif response.startswith(b'-'):
        print(f"Error: {response[1:-2].decode()}")
    elif response.startswith(b':'):
        print(f"Integer: {response[1:-2].decode()}")
    elif response.startswith(b'$'):
        lines = response.split(b'\r\n')
        length = int(lines[0][1:])
        if length == -1:
            print("Null bulk string")
        else:
            print(f"Bulk String (length {length}): {lines[1].decode()}")
    elif response.startswith(b'*'):
        print("Array response (parsing not implemented)")
    
    sock.close()

if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'PING'
    debug_resp_command(command=command)
