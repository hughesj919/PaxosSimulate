__author__ = 'jhughes'

import click
import socket



@click.command()
@click.option('-f', default=0, help='This will simulate a node failure.')
@click.option('-u', default=0, help='This will unfail a node that has been previously failed.')
@click.option('-b', help='This will return the account balance.')
@click.option('-d', default=0, help='This will make a deposit.')
@click.option('-w', default=0, help='This will make a withdrawal.')
def main(f, u, b, d, w):
    if f > 0:
        print('Node Failure Simulated At Site ' + str(f))


if __name__ == '__main__':
    main()