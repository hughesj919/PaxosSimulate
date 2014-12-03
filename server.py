__author__ = 'jhughesdimberman'

import socket,click
tcpPort = 5000
bufferSize = 1024
s1 = 'server1 ip here'
s2 = 'server2 ip here'
s3 = 'server3 ip here'
s4 = 'server4 ip here'
s5 = 'server5 ip here'


#we can use this flag to tell if node is currently in failure mode
failure = False

@click.command()
@click.option('-m', help='Runs program using modified ISPaxos implementation.')
def main(m):
    #updateLog()  #this needs to be the first thing done since a node could be recovering from crash failure
    listen()  #fire up the server

def listen():
    #start up the tcp server and begin listening for requests
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1',tcpPort))
    s.listen(5)
    print('Listening on port '+str(tcpPort) + '...')
    #loop indefinitely to keep listening for commands from client
    while True:
        conn, addr = s.accept()
        while True:
            data = conn.recv(bufferSize)
            # this is where we should do different things based on the data received, i.e. if balance request, then return balance, etc.
            #right now it just echoes the data back
            if not data: break
            print('Data Received: '+data)
            conn.send('Data Received: '+data)
        conn.close()

def updateLog():
    #this should loop until it receives a copy of a log from another node, at which point it can update its own log
    updateLog()


def balanceRequest():
    #this should loop through the serialized local log and send client a balance back
    balanceRequest()

def transactionRequest(type, amount):
    #this should start a paxos instance, if successful the transaction wins the spot, otherwise this should be called again
    transactionRequest()


if __name__ == '__main__':
    main()