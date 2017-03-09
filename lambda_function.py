# Copyright 2017 Centrify Corporation
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function

import os
import json
import boto3
import pprint
import paramiko
import time
import datetime
from botocore.client import Config

print('Loading function')
s3_bucket_name = None
clean_centrifydc = None
clean_centrifycc = None

krb5_cache_lifetime = '10m'
max_delay_start_time = 90
command_left_time = 0

ssm_client = boto3.client("ssm")


def load_lambda_variables():
    global s3_bucket_name 
    global clean_centrifydc 
    global clean_centrifycc 

    if 's3_bucket_name' in os.environ:
        s3_bucket_name = os.environ['s3_bucket_name']
    if 'clean_centrifydc' in os.environ:
        clean_centrifydc = os.environ['clean_centrifydc']
        if not clean_centrifydc in ['yes', 'no']:
            return False
    if 'clean_centrifycc' in os.environ:
        clean_centrifycc = os.environ['clean_centrifycc']
        if not clean_centrifycc in ['yes', 'no']:
            return False
    return True

def get_command_content(command_for):
    global s3_bucket_name
    global krb5_cache_lifetime 
    print("Will get command content for " + command_for)
    if command_for == 'centrifydc':
        return [
            "s3_bucket_name='" + s3_bucket_name + "'", 
            "krb5_cache_lifetime='" + krb5_cache_lifetime + "'",
            "aws s3 cp s3://" + s3_bucket_name + "/login.keytab /tmp/",
            "r1=$?;[ $r1 -ne 0 ] && echo 'aws s3 cp login.keytab failed'",
            "if [ $r1 -eq 0 ];then",
            "  echo 'aws s3 cp login.keytab successfully'",
            "  r1=0",
            "  if /usr/bin/adinfo ;then",
            "    join_user=`/usr/share/centrifydc/kerberos/bin/klist -k /tmp/login.keytab | grep @ | awk '{print $2}' | sed -n '1p' `",
            "    /usr/share/centrifydc/kerberos/bin/kinit -kt /tmp/login.keytab -l $krb5_cache_lifetime $join_user",
            "    /usr/sbin/adleave -r",
            "    r1=$?",
            "  else",
            "    echo 'centrifydc is not installed or the ec2 did not adjoin, skip adleave'",
            "  fi",
            "  [ $r1 -ne 0 ] && echo 'adleave failed'",
            "fi"
        ]
    elif command_for == 'centrifycc':
        return [
            "r2=0",
            "if /usr/bin/cinfo ;then",
            "  /usr/sbin/cunenroll -m -d",
            "  r2=$?",
            "else",
            "  echo 'centrifycc is not installed or the ec2 did not cenroll, skip cunenroll'",
            "fi",
            "[ $r2 -ne 0 ] && echo 'cunenroll failed'"
        ]
    else:
        print("Invalid GET_command_content parameter!")
        return None

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def check_response(response_json):
    if response_json['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False

def send_command(instance_id, commands):
    global max_delay_start_time
    global command_left_time
    global ssm_client
    print("Will send_command")
    response = ssm_client.send_command(
        InstanceIds = [ instance_id ], 
        DocumentName = 'AWS-RunShellScript',
        TimeoutSeconds = max_delay_start_time,
        Parameters={
                'commands': commands,
                'executionTimeout': [str(command_left_time)] # Seconds all commands have to complete in
            }
        )
    if check_response(response):
        print("Command sent: " + json.dumps(response, indent=2, default=myconverter))       
        return response['Command']['CommandId']
    else:
        print("Command could not be sent: " + json.dumps(response, indent=2, default=myconverter))
        return None

def check_command(command_id, instance_id):
    global ssm_client
    timewait = 1
    max_wait_once = 8
    while True:
        response_iterator = ssm_client.list_commands(
            CommandId = command_id, 
            InstanceId = instance_id, 
            )
        if check_response(response_iterator):
            print("list_commands response: " + json.dumps(response_iterator, indent=2, default=myconverter))    
            response_iterator_status = response_iterator['Commands'][0]['Status']
            if response_iterator_status == 'Pending' or response_iterator_status == 'InProgress':
                print( "Status: " + response_iterator_status)
            elif response_iterator_status == 'Success':
                print("Received command response[:" + response_iterator_status + "] " + \
                    json.dumps(response_iterator, indent=2, default=myconverter))
                break
            else:
                print("Received command response[:" + response_iterator_status + "] " + \
                    json.dumps(response_iterator, indent=2, default=myconverter))
                break
        time.sleep(timewait)
        timewait *= 2
        if timewait > max_wait_once:
            timewait = max_wait_once

    if response_iterator_status in ['Success','Failed'] :
        response = ssm_client.list_command_invocations(
            CommandId = command_id, 
            InstanceId = instance_id, 
            Details=True
            )
        if check_response(response):
            output = response['CommandInvocations'][0]['CommandPlugins'][0]['Output']
            if output:
                print("Command output: " + output) 
    if response_iterator_status == 'Success':
        return True
    else:
        return False


def run_cmd(instance_id):
    global clean_centrifydc 
    global clean_centrifycc 

    ret = load_lambda_variables()
    if not ret:
        print("Load lambda environment variables failed")
        return False
    commands = ["r1=0", "r2=0"]
    skipped = True
    if clean_centrifydc == 'yes':
        commands = commands + get_command_content('centrifydc')
        skipped = False
    if clean_centrifycc == 'yes':
        commands = commands + get_command_content('centrifycc')
        skipped = False
    if skipped:
        print("No any clean action specified, skip send_command")
        return True
    else:
        commands = commands + ["if [ $r1 -ne 0 -o $r2 -ne 0 ];then echo 'clean action failed[adleave exit code='$r1'] [cunenroll exit code='$r2']' ; exit 1; fi; exit 0"]
        
 
    command_id = send_command(instance_id, commands)
    if command_id:
        if check_command(command_id, instance_id):
            print("Lambda executed correctly")
            return True
        else:
            print("check_command failed")
    else:
        print("send_command failed")
    return False



def lambda_handler_stop(parsed_message, context):
    global command_left_time 
    print("Will parse the event message and get the instance id")
    instanceId = parsed_message['EC2InstanceId']

    # Get Public IP address of the terminating instance
    print("Will get the boto3.resource('ec2')")
    ec2 = boto3.resource('ec2')
    print("Parse instance object from ec2 resource")
    instance = ec2.Instance(instanceId)
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(instance)
    if instance.instance_id != instanceId:
        print("instance id not equal msg:" + instanceId + " instance said:" + instance.instance_id)
        return 0
    print("instance id :" + instanceId)
    command_left_time = context.get_remaining_time_in_millis() / 1000 - max_delay_start_time - 2
    ret =  run_cmd(instanceId)
    print("Finish running the remote commands[result=" + str(ret) + "]")
    return 0



def lambda_handler(event, context):
    print("Received event:  " + json.dumps(event, indent=2, default=myconverter))
    message = event['Records'][0]['Sns']['Message']
    parsed_message = json.loads(message) 
    if parsed_message.has_key('LifecycleTransition'):
        msg_type = parsed_message['LifecycleTransition']
        if msg_type and msg_type == "autoscaling:EC2_INSTANCE_TERMINATING":
            lambda_handler_stop(parsed_message, context)
    print("Finished the message")
    return 0
