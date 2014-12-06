__author__ = 'jhughesdimberman'

import socket
import click
import pickle
import os
import errno
import thread
import math
from socket import error as socket_error

log = []
acceptValues = []
acceptors = []
tcpPort = 5000
bufferSize = 1024
ballotNum = 0.0
acceptNum = None
acceptVal = None
myProposal = None
nodeid = 0
prepAckCount = 0
origConn = None
decided = False

s1 = '54.173.225.121'
s2 = '54.172.165.23'
s3 = '54.173.208.22'
s4 = '54.174.138.236'
s5 = '54.172.233.23'
s6 = '127.0.0.1'
servers = [s1, s2, s3, s4, s5]
#servers = [s6]
failure = False


# we can use this flag to tell if node is currently in failure mode


@click.command()
@click.option('-m', help='Runs program using modified ISPaxos implementation.')
def main(m):
    getnodeid()
    setfailure(False)
    loadlog()
    # updateLog()  #this needs to be the first thing done since a node could be recovering from crash failure
    listen()  # fire up the server

# this listens continunally on the main thread
def listen():
    # start up the tcp server and begin listening for requests
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', tcpPort))
    s.listen(5)
    print('Node ' + str(nodeid) + ' listening on port '+str(tcpPort) + '...')
    # loop indefinitely to keep listening for commands from client
    while True:
        conn, addr = s.accept()
        thread.start_new_thread(handledata, (conn, addr))

# this will use a new thread to handle incoming data everytime
def handledata(conn, addr):
    global ballotNum, acceptNum, acceptVal, prepAckCount, origConn
    while True:
            data = conn.recv(bufferSize)
            # this is where we should do different things based on the data received, i.e. if balance request, then return balance, etc.
            # right now it just echoes the data back
            if not data: break
            print('Message Received from ' + addr[0] + ': '+data)
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
            elif cmd[0] == 'w' or cmd[0] == 'd' and not failure:
                origConn = conn
                transactionRequest(cmd[0], cmd[1])
            elif cmd[0] == 'prepare' and not failure:
                if cmd[1] > ballotNum:
                    ballotNum = float(cmd[1])
                    msg = 'prepack' + ' ' + str(ballotNum) + ' ' + str(acceptNum) + ' ' + str(acceptVal)
                    talk(addr[0], msg)
            elif cmd[0] == 'prepack' and not failure:
                prepAckCount += 1
                if cmd[2] != 'None' and cmd[3] != 'None':
                    acceptValues.append((cmd[2], cmd[3]+' '+cmd[4]))
                # if we have a quorum start accept phase
                if prepAckCount >= (len(servers)//2 + 1):
                    prop = getProposalValue()
                    print 'Quorum received, starting acceptance phase with proposal: ' + prop
                    accept(ballotNum, prop)
            elif cmd[0] == 'accept' and not failure:
                if cmd[1] >= ballotNum:
                    print 'Proposal accepted with ballot: ' + cmd[1] + ' and value: ' + cmd[2] + ' ' + cmd[3]
                    prevAcceptNum = acceptNum
                    prevAcceptVal = acceptVal
                    acceptNum = float(cmd[1])
                    acceptVal = cmd[2] + ' ' + cmd[3] + ' ' + cmd[4]
                    if prevAcceptNum != acceptNum and prevAcceptVal != acceptVal:
                        accept(acceptNum, acceptVal)
                    if ballotNum == acceptNum and acceptVal == myProp() and addr[0] not in acceptors:
                        acceptors.append(addr[0])
                        if len(acceptors) >= (len(servers)//2 + 1):
                            print 'Quorum received, decided: ' + acceptVal
                            decide(acceptVal)
            elif cmd[0] == 'decide' and not failure:
                decision = acceptVal.split()
                writeDecision(decision)
                if decision[0] == 'd' and origConn is not None:
                    origConn.send('Deposit ' + str(decision[1]) + ' added to log.')
                elif decision[0] == 'w' and origConn is not None:
                    origConn.send('Withdraw ' + str(decision[1]) + ' added to log.')
    conn.close()


def loadlog():
    global log
    if not os.path.isfile('log.txt'):
        open('log.txt', 'wb+')
    try:
        log = pickle.load(open('log.txt', 'rb+'))
    except EOFError:
        print 'Log file currently empty...'

def myProp():
    if myProposal is not None:
        return myProposal[0] + ' ' + myProposal[1] + ' ' + myProposal[2]
    else:
        return '-1'


def getnodeid():
    global nodeid
    f = open('whoami.txt', 'r+')
    nodeid = int(f.readline())


def setfailure(val):
    global failure
    failure = val

#def updateLog():
    # this should loop until it receives a copy of a log from another node, at which point it can update its own log


def decide(val):
    for server in servers:
        talk(server, 'decide ' + val)

def writeDecision(val):
    print 'Decide val:' + val[0] + ' ' + val[1] + ' ' + val[2]
    # if this is the first decide message make space in the log, otherwise just update
    if len(log) <= val[2]:
        print 'append'
        log.append((val[0], float(val[1])))
    else:
        log[val[2]] = (val[0], float(val[1]))
    pickle.dump(log, open('log.txt', 'wb+'))
    #resetPaxosValues()


def resetPaxosValues():
    global acceptValues, acceptors, prepAckCount, acceptNum, acceptVal;
    acceptValues = []
    acceptors = []
    prepAckCount = 0
    acceptNum = None
    acceptVal = None


# loop through the serialized local log and send client a balance back
def balancerequest():
    bal = 0.0
    for tup in log:
        if tup[0] == 'd':
            bal = bal + tup[1]
        elif tup[0] == 'w':
            bal = bal - tup[1]
    return bal


def talk(srv, msg):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((srv, tcpPort))
        s.send(msg)
    except socket_error as serr:
        if serr.errno != errno.ECONNREFUSED:
            raise serr
    s.close()
    print('Message sent to ' + srv + ': ' + msg)
    #print('Message received: ' + data)
    #return data


def transactionRequest(type, amount):
    # this should start a paxos instance, if successful the transaction wins the spot, otherwise this should be called again
    global myProposal
    myProposal = (type, amount, str(len(log)))
    propose()


def propose():
    global ballotNum
    # ballot num increments current ballot num and then appends its nodeid, so first ballotnum is 1.6 for node 6
    ballotNum = float(str(int(math.floor(ballotNum+1))) + '.' + str(nodeid))
    for server in servers:
        talk(server, 'prepare ' + str(ballotNum))


def accept(acceptNum, acceptVal):
    for server in servers:
        talk(server, 'accept ' + str(acceptNum) + ' ' + str(acceptVal) + ' ' + str(len(log)))


def getProposalValue():
    print acceptValues
    if len(acceptValues) > 0:
        maxBal = acceptValues[0][0]
        maxVal = acceptValues[0][1]
        for val in acceptValues:
            if val[0]>=maxBal:
                maxBal = val[0]
                maxVal = val[1]
        print 'maxval' + str(maxVal)
        return maxVal
    else:
        return myProposal[0] + ' ' + myProposal[1]


if __name__ == '__main__':
    main()