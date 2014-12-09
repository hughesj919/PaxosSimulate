__author__ = 'jhughesdimberman'

import socket
import click
import pickle
import os
import errno
import json
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
potentialExtras = []
myProposal = None
modMyProposal = None
nodeid = 0
prepAckCount = 0
origConn = None
failure = False
repropose = True
appenders = []
useAppenders = False
needsUpdate = False

s1 = '54.173.225.121'
s2 = '54.172.165.23'
s3 = '54.173.208.22'
s4 = '54.174.138.236'
s5 = '54.172.233.23'
s6 = '127.0.0.1'
servers = [s1, s2, s3, s4, s5]


@click.command()
@click.option('-mod', help='Runs program using modified ISPaxos implementation.')
def main(mod):
    global m
    m = mod
    getnodeid()
    setfailure(False)
    loadlog()
    # updateLog()  #this needs to be the first thing done since a node could be recovering from crash failure
    listen()  # fire up the server

# this listens continually on the main thread
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
    global ballotNum, acceptNum, acceptVal, prepAckCount, origConn, acceptors, appenders
    while True:
            data = conn.recv(bufferSize)
            # this is where we should do different things based on the data received, i.e. if balance request, then return balance, etc.
            # right now it just echoes the data back
            if not data:
                break
            print('Message Received from ' + addr[0] + ': '+data)
            cmd = data.split()
            if cmd[0] == 'f':
                setfailure(True)
                conn.send('Node simulating failure mode.')
            elif cmd[0] == 'u':
                setfailure(False)
                conn.send('Node revived from failure mode.')
            elif not failure:
                if cmd[0] == 'b':
                    conn.send('Current Balance: ' + str(balancerequest()))
                elif cmd[0] == 'p':
                    printLog(conn)
                elif cmd[0] == 'w' or cmd[0] == 'd':
                    origConn = conn
                    transactionRequest(cmd[0], cmd[1])
                elif cmd[0] == 'prepare':
                    handlePrepare(cmd, addr)
                elif cmd[0] == 'ack':
                    handleAck(cmd)
                elif cmd[0] == 'accept':
                    handleAccept(cmd)
                elif cmd[0] == 'accepted':
                    handleAccepted(addr)
                elif cmd[0] == 'decide':
                    if m: modifiedHandleDecide(cmd)
                    else: handleDecide(cmd)
                elif cmd[0] == 'update':
                    handleUpdate(cmd[1])
                elif cmd[0] == 'updating':
                    updateLog(cmd[1])
    conn.close()


def handlePrepare(cmd,addr):
    global ballotNum, acceptNum, acceptVal
    if float(cmd[1]) > ballotNum:
        ballotNum = float(cmd[1])
        msg = 'ack' + ' ' + str(ballotNum) + ' ' + str(acceptNum) + ' ' + str(acceptVal)+' '+str(getnodeid())
        talk(addr[0], msg)

def handleAck(cmd):
    global prepAckCount, acceptValues, ballotNum
    priorMajority = (prepAckCount >= (len(servers) // 2 + 1))
    prepAckCount += 1
    if cmd[2] != 'None' and cmd[3] != 'None':
        acceptValues.append((cmd[2], cmd[3] + ' ' + cmd[4] + ' '+cmd[5]))
        # vif we have a quorum start accept phase
    if (prepAckCount >= (len(servers) // 2 + 1)) and not priorMajority:
        if m: prop = modifiedGetProposalValue()
        else: prop = getProposalValue()
        print 'Quorum received, starting acceptance phase with proposal: ' + prop
        accept(ballotNum, prop)




def handleAccept(cmd):
    global ballotNum, acceptNum, acceptVal
    if float(cmd[1]) >= ballotNum:
        print 'Proposal accepted with ballot: ' + cmd[1] + ' and value: ' + cmd[2] + ' ' + cmd[3] + ' ' + cmd[4]
        acceptNum = float(cmd[1])
        acceptVal = cmd[2] + ' ' + cmd[3] + ' ' + cmd[4]
        accepted(acceptNum, acceptVal)


def handleAccepted(addr):
    global acceptors, acceptVal, ballotNum, acceptNum, repropose
    if ballotNum == acceptNum and acceptVal == myProp() and addr[0] not in acceptors:
        priorMajority = (len(acceptors) >= (len(servers) // 2 + 1))
        acceptors.append(addr[0])
        if len(acceptors) >= (len(servers) // 2 + 1) and not priorMajority:
            print 'Quorum received, decided: ' + acceptVal
            repropose = False
            decide(acceptVal)





def loadlog():
    global log
    if not os.path.isfile('log.txt'):
        open('log.txt', 'wb+')
    try:
        log = json.load(open('log.txt', 'rb+'))
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

def requestUpdate():
    global needsUpdate
    for server in servers:
        talk(server, 'update ' + nodeid)
        needsUpdate = True

def updateLog(lg):
    global needsUpdate, log
    if not needsUpdate:
        tmp = json.load(lg)
        if len(tmp)>len(log):
            log = tmp
            needsUpdate=False


def decide(val):
    for server in servers:
        if m: talk(server, 'decide ' + val + ' ' + json.dumps(potentialExtras) + ' ' + json.dumps(appenders))
        else: talk(server, 'decide ' + val)


def handleDecide(val):
    global origConn, acceptVal, myProposal, repropose
    decision = val.split()[1:]
    writeDecision(decision)
    if decision[0] == 'd' and origConn is not None:
        origConn.send('Deposit ' + str(decision[1]) + ' added to log.')
    elif decision[0] == 'w' and origConn is not None:
        origConn.send('Withdraw ' + str(decision[1]) + ' added to log.')
    resetPaxosValues()
    if repropose and (myProposal is not None):
        potentialExtras = []
        appenders = []
        transactionRequest(myProposal[0], myProposal[1])
    else:
        myProposal = None
        origConn = None
        repropose = True

def modifiedHandleDecide(val):
    global origConn, acceptVal, myProposal, repropose, potentialExtras, appenders
    decision = val.split()[1:]
    modifiedWriteDecision(decision)
    if decision[0] == 'd' and origConn is not None:
        origConn.send('Deposit ' + str(decision[1]) + ' added to log with appended values: ' + potentialExtras)
    elif decision[0] == 'w' and origConn is not None:
        origConn.send('Withdraw ' + str(decision[1]) + ' added to log.')
    resetPaxosValues()
    if repropose and (myProposal is not None):
        transactionRequest(myProposal[0], myProposal[1])
    else:
        myProposal = None
        origConn = None
        repropose = True


def modifiedWriteDecision(val):
    global potentialExtras, appenders
    potentialExtras = json.loads(val[3])
    appenders = json.loads(val[4])
    if(val[0]=='d'):
        logposition = int(val[2])
        log[logposition] = (val[0], float(val[1]))
        logposition+=1
        for i in potentialExtras:
            log[logposition] = (val[0], float(i.split()[1]))
            logposition+=1
    else:
        logposition = int(val[2])
        log[logposition] = (val[0], float(val[1]))
    pickle.dump(log, open('log.txt', 'wb+'))







def writeDecision(val):
    print 'Decide val:' + val[0] + ' ' + val[1] + ' ' + val[2]
    # if this is the first decide message make space in the log, otherwise just update
    log[int(val[2])] = (val[0], float(val[1]))
    pickle.dump(log, open('log.txt', 'wb+'))


def resetPaxosValues():
    global acceptValues, acceptors, prepAckCount, acceptNum, acceptVal, modvalues
    acceptValues = []
    acceptors = []
    prepAckCount = 0
    acceptNum = None
    appenders = []
    potentialExtras = []
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
    global myProposal, appenders
    if type == 'w' and float(amount) > balancerequest():
        origConn.send('Transaction would result in overdraft. Rejected.')
    elif m:
        modvalues.append((amount,getnodeid()))
        myProposal = (type, modvalues, appenders, str(len(log)))
    else:
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
        # if m:
        #     if appenders == None: add = ''
        #     else: add = ' ' + appenders
        #     talk(server, 'accept' + str(acceptNum) + ' ' + acceptVal[0] + ' ' + str(len(log)) + add)
        # else:
            talk(server, 'accept ' + str(acceptNum) + ' ' + str(acceptVal) + ' ' + str(len(log)))


def accepted(acceptNum, acceptVal):
    for server in servers:
        # if m: talk(server, 'accepted ' + str(acceptNum) + ' ' + acceptVal[0] + add)
        # else:
        talk(server, 'accepted ' + str(acceptNum) + ' ' + str(acceptVal))




def getProposalValue():
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

def modifiedGetProposalValue():
    if len(acceptValues) > 0:
        maxIsDep = False
        maxBal = acceptValues[0][0]
        maxVal = acceptValues[0][1]
        for val in acceptValues:
            if myProposal[1][0]=='d' and val[0]=='d':
                potentialExtras.append(val)
                appenders.append(val.split(' ')[5])
            if val[0]>=maxBal:
                if val[0]=='d':
                    maxIsDep =True
                else: maxIsDep = False
                maxBal = val[0]
                maxVal = val[1]
        if maxIsDep:
            useAppenders = True
        else:
            useAppenders = False
        return maxVal
    return myProposal[0] + ' ' + myProposal[1]

def handleUpdate(requester):
    talk(requester,'updating ' + json.dump(log))

def printLog(conn):
    logstr=''
    for val in log:
        logstr += str(val) + '\n'
    conn.send('Log Transactions: \n' + logstr)


if __name__ == '__main__':
    main()