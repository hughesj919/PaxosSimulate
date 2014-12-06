__author__ = 'jhughesdimberman'

import click
import socket

tcpPort = 5000
bufferSize = 1024
s1 = '54.173.225.121'
s2 = '54.172.165.23'
s3 = '54.173.208.22'
s4 = '54.174.138.236'
s5 = '54.172.233.23'
servers = [s1, s2, s3, s4, s5]

@click.command()
@click.option('-n', default=0, help='This is the target server.')
@click.option('-f', is_flag=True, help='This will simulate a node failure.')
@click.option('-u', is_flag=True, help='This will unfail a node that has been previously failed.')
@click.option('-b', is_flag=True, help='This will return the account balance.')
@click.option('-d', default=0.0, help='This will make a deposit.')
@click.option('-w', default=0.0, help='This will make a withdrawal.')
def main(n, f, u, b, d, w):
    if n <= 0:
        print('Please enter a valid node.')
    elif f:
        talk(n, "f")
    elif u:
        talk(n, "u")
    elif b:
        talk(n, "b")
    elif d:
        talk(n, "d "+str(d))
    elif w:
        talk(n, "w "+str(w))


def talk(n, msg):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((servers[n-1], tcpPort))
    s.send(msg)
    data = s.recv(bufferSize)
    s.close()
    print("Message sent: " + str(n) + msg)
    print(data)

if __name__ == '__main__':
    main()