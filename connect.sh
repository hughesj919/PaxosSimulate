#!/user/bin/env bash

if [ $1 -eq 1 ]; then
ssh -i Server1Key.pem ec2-user@ec2-54-173-225-121.compute-1.amazonaws.com
fi

if [ $1 -eq 2 ]; then
ssh -i Server1Key.pem ec2-user@ec2-54-172-165-23.compute-1.amazonaws.com
fi

if [ $1 -eq 3 ]; then
ssh -i Server1Key.pem ec2-user@ec2-54-173-208-22.compute-1.amazonaws.com
fi

if [ $1 -eq 4 ]; then
ssh -i Server1Key.pem ec2-user@ec2-54-174-138-236.compute-1.amazonaws.com
fi


if [ $1 -eq 5 ]; then
ssh -i Server1Key.pem ec2-user@ec2-54-172-233-23.compute-1.amazonaws.com
fi

