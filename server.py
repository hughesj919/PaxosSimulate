__author__ = 'jhughesdimberman'

import socket
import click
import pickle
import os
import sys

log = []
tcpPort = 5000
bufferSize = 1024
s1 = 'server1 ip here'
s2 = 'server2 ip here'
s3 = 'server3 ip here'
s4 = 'server4 ip here'
s5 = 'server5 ip here'
failure = False


# we can use this flag to tell if node is currently in failure mode


@click.command()
@click.option('-m', help='Runs program using modified ISPaxos implementation.')
def main(m):
    setfailure(False)
    loadlog()
    #updateLog()  #this needs to be the first thing done since a node could be recovering from crash failure
    listen()  #fire up the server


def listen():
    #start up the tcp server and begin listening for requests
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', tcpPort))
    s.listen(5)
    print('Listening on port '+str(tcpPort) + '...')
    #loop indefinitely to keep listening for commands from client
    while True:
        conn, addr = s.accept()
        while True:
            data = conn.recv(bufferSize)
            # this is where we should do different things based on the data received, i.e. if balance request, then return balance, etc.
            # right now it just echoes the data back
            if not data: break
            print('Data Received: '+data)
            cmd = data.split()
            if cmd[0] == 'f':
                setfailure(True)
                conn.send('Node simulating failure mode.')
            elif cmd[0] == 'u':
                setfailure(False)
                conn.send('Node revived from failure mode.')
            elif cmd[0] == 'b' and not failure:
                b = balancerequest()
                conn.send('Current Balance: ' + str(b))
            elif cmd[0] == 'w' and not failure:
                log.append(('w', float(cmd[1])))
                pickle.dump(log, open('log.txt', 'wb+'))
                conn.send('Withdraw ' + str(cmd[1]) + ' added to log.')
            elif cmd[0] == 'd' and not failure:
                log.append(('d', float(cmd[1])))
                pickle.dump(log, open('log.txt', 'wb+'))
                conn.send('Deposit ' + str(cmd[1]) + ' added to log.')

            # conn.send('Data Received: '+data)
        conn.close()


def loadlog():
    global log
    if not os.path.isfile('log.txt'):
        open('log.txt', 'wb+')
    try:
        log = pickle.load(open('log.txt', 'rb+'))
    except EOFError:
        print "Log file currently empty..."


def setfailure(val):
    global failure
    failure = val

def updateLog():
    # this should loop until it receives a copy of a log from another node, at which point it can update its own log
    updateLog()


# loop through the serialized local log and send client a balance back
def balancerequest():
    bal = 0.0
    for tup in log:
        if tup[0] == 'd':
            bal = bal + tup[1]
        elif tup[0] == 'w':
            bal = bal - tup[1]
    return bal

def transactionRequest(type, amount):
    #this should start a paxos instance, if successful the transaction wins the spot, otherwise this should be called again
    transactionRequest()


if __name__ == '__main__':
    main()