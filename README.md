# Introduction

This is the README file for using sample orchestration scripts to automatically
enroll Linux-based cloud instances to Centrify Identity Platform or
to automatically join the instance to Active Directory.

You need to set up your configuration by modifying the top part of the sample orchestration
script startup-userdata.sh.  When you launch the new Auto Scaling or EC2 instance, you 
need to upload the script as "user data".  

The following platforms are supported:
* Red Hat Enterprise Linux 6.5 or later for 32/64 bit
* Ubuntu Server 14.04 LTS for 32/64 bit
* Ubuntu Server 16.04 LTS
* Amazon Linux AMI 2014.09 for 32 bit
* Amazon Linux AMI 2016.09
* CentOS 7.x


#Prerequisite
- You need the following AWS permissions:
  - permisison to create, modify, read, list and delete IAM Policies and Roles.
  - Full permission to EC2
  - AWSLambdaFullAccess
- Create one or more subnets in your VPC for lambda functions to use. These subnets must be private subnets. The routing table of these private subnets must point to a NAT instance or AWS NAT instance that resides in the public subnet of the VPC.
- You need an EC2 instance that has AWS CLI commands installed.  Please refer to 
   http://docs.aws.amazon.com/cli/latest/userguide/installing.html#install-with-pip
   for more information about awscli installation.  Make sure that you have configured awscli 
   using the `aws configure` command. Please refer to 
   http://docs.aws.amazon.com/cli/latest/reference/configure/index.html#examples
   for more information about configuring AWS CLI commands.
- If you need to use Centrify Server Suite to join the AWS instance to Active Directory, 
  you also need the followings:
  -  An AD user who joins the EC2 instance for Linux to your centrify zone. 
     You need to make sure that the AD user has following two permissions at least:
    - Delegate `Join a computer to the domain` in `Active Directory Users and Computers`.
    - Delegate 'Join comupters to the zone' in `DirectManage Access Manager`.
  - Permission to create and upload files to a S3 bucket
  - An EC2 instance that has Centrify Server Suite installed and joined to your Active Directory.
  - An account in the Centrify Support website 
	 (http://www.centrify.com/support).   Follow the instruction in 
	 https://www.centrify.com/support/customer-support-portal/repos to generate the repo key. Use the string
	 before @repo.centrify.com to set up the parameter CENTRIFY_REPO_CREDENTIAL.  For example, if the repo key 
	 is 1111111122222233333333333333344444555555:777888880000099999991234567890abcdefghij@repo.centrify.com, set
	 CENTRIFY_REPO_CREDENIIAL=1111111122222233333333333333344444555555:777888880000099999991234567890abcdefghij

#Configuration parameters
You can specify the AWS deployment configuration in the `User Data` of the AWS instance.   You ned to download the file 
startup-userdata.sh and set up the parameter values in the top part of the file.  The whole file must be copied to 
the `User Data` of the new EC2 instance and/or Auto Scaling group launch configuration.

## Centrify Agent for Linux parameters
The following parameters are for enrolling the AWS instances to Centrify Identity Platform.

| Parameter | Description | Optional | Example |
| --- | --- | --- | --- | 
| DEPLOY_CENTRIFYCC | Specifies enroll to Centrify Identity Platform | no | yes |
| CENTRIFYCC_TENANT_URL | Centrify Identity Platform URL | no | *my-company.deployment.centrify.com* |
| CENTRIFYCC_ENROLLMENT_CODE | Enrollment code to use | no | *12345678-1234-5678-1234-ABCDEF123456* |
| CENTRIFYCC_AGENT_AUTH_ROLES | Roles where members can log in to the instance.  Specifies as a comma separated list | no | *my_login_role* |
| CENTRIFYCC_FEATURES | Features to enable for the agent.  Specifies as a comma separated list.  Valid values are: **agentauth**, **aapm**, **all** | no | agentauth,aapm |
| CENTRIFYCC_NETWORK_ADDR_TYPE | Value to use to as network address for the created resource.  Allowed values are PublicIP, PrivateIP, Hostname. | no | PublicIP |
| CENTRIFYCC_COMPUTER_NAME_PREFIX | Prefix to use for computer name | yes | *apac* |
| CENTRIFYCC_CENROLL_ADDITIONAL_OPTIONS | Additional options for cenroll command line | yes | --resource-setting ProxyUser:centrify | 

Notes:
- The AWS instance ID used as the computer name for the created resource.  If CENTRIFYCC_COMPUTER_NAME_PREFIX is specified, the computer name 
will be *\<CENTRIFYCC_COMPUTER_NAME_PREFIX\>*-*\<AWS Instance ID\>*.  Otherwise, it will be *\<AWS Instance ID\>*.



## Centrify Server Suite agent parameters
The following parameters are for joining to Active Directory using the Centrify Server Suite agent.

| Parameter | Description | Optional | Example |
| --- | --- | --- | --- | 
| DEPLOY_CENTRIFYDC | Install Centrify Server Suite agent | no | yes |
| CENTRIFY_REPO_CREDENTIAL | Credential required to access Centrify Repo | no | *a long string* |
| CENTRIFYDC_JOIN_TO_AD | Whether to join to Active Directory | no | yes |
| CENTRIFYDC_ZONE_NAME | Name of zone to join to | no | *my_zone* |
| CENTRIFYDC_HOSTNAME_FORMAT | How to generate host name to use in Active Directory.  Valid values are PRIVATE_IP, INSTANCE_ID. See note below | no | PRIVATE_IP |
| CENTRIFYDC_KEYTAB_S3_BUCKET | Name of S3 bucket where the login.keytab file for the enroller is stored | no | *my_s3_bucket* |
| CENTRIFYDC_ADDITIONAL_PACKAGES | Name of additional packages to install.  Allowed values are: **centrifydc-openssh**, **centrifydc--ldapproxy** | yes | |
| CENTRIFYDC_ADJOIN_ADDITIONAL_OPTIONS | Additional options for adjoin command | yes | |

Note that host name is limited to 15 characters.  If the instance ID is longer than 15 characters, the first 15 characters of instance ID will be used 
and there is a remote possibility of hostname conflicts.   We recommend to use PRIVATE-IP address for hostname.


#Deployment process
  1. If you do not need to install/deploy Centrify Server Suite agent to join to Active Directory,
     you can skip directly to step 3.  
	 </br>
	 Generate login.keytab using following command on your Linux/Unix that has joined
     to Active Directory:
     ```
     adkeytab -A -K login.keytab -u your_admin -p your_admin_password your_ad_user
     ```
     where 
	 - *your_admin* is the name of a user who is permitted to adopt the account *your_ad_user*
	 - *your_admin_password* is the password of *your_admin*
     - *your_ad_user* is the user who joins the instance to Active Directory.
	 
	For example:
	 ```
     adkeytab -A -K login.keytab -u admin1  -p admin1_pass join_user1
	```
	
  2. You need to sign in https://console.aws.amazon.com/s3 to create a S3 bucket and then upload 
     login.keytab file (created in step 1) to the bucket. You can refer to
     http://docs.aws.amazon.com/AmazonS3/latest/gsg/CreatingABucket.html about how to create a bucket.

  3. Create your Key Pair if you don't have one so that you can log into your EC2 instances. You can refer to</br>
      http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair about 
      how to create Key Pair.

  4. Create VPC, subnet and security group for your instances in the new Auto Scaling group.
  
  5. Create IAM role for lambda function.
      - Sign in AWS Management Console and select IAM Service.
	  - Select Roles, and click on `Create New Role`.
	    - Enter your role name, click `Next Step`.
		- Select `AWS Service Roles`, and select `AWS Lambda` in the drop-down list 
		- Attach the predefined policy AWSLambdaVPCAccessExecutionRole to the role.
		- Click `Next Step` to review the role. 
		- Click `Create Role`.

  6. In IAM Service, create the following IAM policy and associate it with IAM role above:
     ```
	{
		"Version": "2012-10-17",
		"Statement": [
		{
			"Effect": "Allow", "Action": [
				"ssm:SendCommand",
				"ssm:ListCommands",
				"ssm:ListCommandInvocations"
			],
			"Resource": "*"
		},
		{
			"Effect": "Allow",
			"Resource": "*",
			"Action": [
				"ec2:DescribeInstances"
			]
		},
		{
			"Effect": "Allow",
			"Resource": "*",
			"Action": [
				"autoscaling:CompleteLifecycleAction"
			]
		},
		{
			"Action": [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": "arn:aws:logs:*:*:*",
			"Effect": "Allow"
		}
		]
	}
     ```

  7. Create Lambda Function.
      - Download centrify-cleanup-lambda-1-0.zip to your local system.
	  - Select Lambda Service in AWS Console.
      - Select `Functions`, and then click `Create a Lambda function` button.
      - In the `Select blueprint` page:
	    - Choose `python2.7` in `Select runtime` box
        - Type `hello-world` in `filter` box
        - Choose `hello-world-python` template.
      - In the `Configure Triggers` page, click `Next Step`.
      - In the `Configure function` page, do as follows:
        - Enter the name of your lambda function in `Name*` box.
        - Enter description for the Lambda function in `Description` box.
        - For `Code entry type` selection, select `Upload a .ZIP file`
		- click `Upload` button to upload the copy of  centrify-cleanup-lambda-1-0.zip that you just downloaded
        - Add three Environment variables:
		  - clean_centrifydc:  Specify **yes** if instance is joined to Active Directory; otherwise **no**
          - clean_centrifycc: Specify **yes** if instance is enrolled to Centrify Identity Platform; otherwise **no** 
          - s3_bucket_name:  Specify the bucket name that login.keytab is stored in.  Only relevant if instance is joined to Active Directory
        - For `Handler*` box, keep default `lambda_function.lambda_handler`.
		- For `Role*` box, keep default `Choose an existing role`
		  - select the IAM role that you created in step 5.
		- For `Timeout*` box, set timeout value to 4 min 10 sec.
		- For `VPC` box, set the VPC and subnet to the one created in Prerequisite section.
		- Click `Next`
      - In the Review page, click `Create function` button.

  8. Create a SNS topic to publish notification of AutoScaling lifecycle hook.
     - Select SNS Service in AWS Console
	 - Select `Create topic`
       - Enter topic name and description and continue to create the topic.
     - Select `Topics` to view all SNS topics.
     - Save the ARN value for the newly created topic.	 

  9. Create an IAM Role to allow Autoscaling service to publish the SNS topic.
      - Select IAM Service in AWS Console
	  - Select Roles, and click on `Create New Role`.
	    - Enter your role name, click `Next Step`.
		- Select `AWS Service Roles`, and select `AutoScaling Notification Access` in the drop-down list , click `Next Step`.
        - In the `Attach Policy` page, don’t select any policy.
		- Keep click `Next Step` until you have finished the creation process.
      - Now an Autoscaling service role without any policy associated is created.
      - Create an IAM policy as follows and associate it with the IAM Role you just created:
	```
	{
		"Version": "2012-10-17",
		"Statement": [{ 
			"Effect": "Allow", 
			"Resource": "your sns topic arn",
			"Action": [ "sns:Publish" ] 
		}]
	}
	```
*your sns topic arn* is the ARN for the topic created in step 8.

  1. Subscribe the SNS topic to the Lambda.
       - Select SNS Service in AWS Console
       - Select `Topics`, and select the SNS topic created in step 8. 
       - In the `Topic details` page, click `Create subscription`.
       - In the `Create subscription` popup,
          - Select `AWS lambda` for `Protocol`
          - Select your lambda function in the `Endpoint` pull down menu.
          - Leave `default` in the `Version or alias` box.
          - Click `Create subscription`

  1. Grant SNS topic to invoke Lambda function.
      - Log in to an EC2 instance where awscli is installed and configured.
      - Run the following aws command: </br>
      ```
      aws lambda add-permission --function-name your_lambda_function_name --statement-id 1 --action "lambda:InvokeFunction" --principal sns.amazonaws.com --source-arn "your_sns_topic_arn" 
      ```
      
	  You need to:
       - replace *your_lambda_function_name* with the name of your lambda function created in step 7.
       - replace *your_sns_topic_arn* with the ARN of the topic created in step 8.

  1. Create IAM Role for the instances in Auto Scaling group.
      - Select IAM Service in AWS Console
	  - Select Roles, and click on `Create New Role`.
	    - Enter your role name, click `Next Step`.
		- Select `AWS Service Roles`, and select `Amazon EC2` in the drop-down list , click `Next Step`.
        - In the `Attach Policy` page, select AmazonEC2RoleforSSM and AmazonEC2ReadOnlyAccess.
		- Keep click `Next Step` until you have finished the creation process.

  1. If your AWS instance needs to join to Active Directory, create the following IAM Policy and attached it 
      to the IAM role created in step 12 above.  This policy allows the instance to access the S3 bucket to download
	  the login.keytab file. </br>
	```
	{
		"Version": "2012-10-17",
		"Statement": [{ 
			"Effect": "Allow",
			"Action": [
				"s3:GetObject",
				"s3:ListObject"
				],
			"Resource": [
				"arn:aws:s3:::your_s3_bucketname/*"
			]
		}]
	}
	```
Replace *your_s3_bucketname* by the name of the S3 bucket that you created in step 2.

  1. Download startup-userdata.sh and create a userdata template.  See the section **Configuration Parameters** for more information.
  
  1. Create a Launch Configuration for Auto Scaling group. You can refer to 
      http://docs.aws.amazon.com/autoscaling/latest/userguide/GettingStartedTutorial.html#gs-create-lc for more information about creating
	  a launch configuration.
       - In `Configure Details` page:
         - choose the IAM role you created in step 12.
		 - Click `Advanced Details`
           - If you set the configuration parameter CENTRIFYCC_NETWORK_ADDR_TYPE to `PublicIP`, you need to 
             select `Assign a public IP address to every instance` for `IP address Type`.
           - Copy the user data template that you created in step 14 to the `User Data` box.
       - Continue other steps to create the launch configuration.  Make sure that you select the key pair that you created in step 3.

  1. Create an Auto Scaling group using the Launch Configuration created above. You can refer to
      http://docs.aws.amazon.com/autoscaling/latest/userguide/GettingStartedTutorial.html#gs-create-asg for more
	  information about creating an Auto Scaling group.
      In the `Configure Auto Scaling group details` step, make sure you select the VPC and subnet that you created in step 4.
      
  1. Add a lifecycle hook for the autoscaling group so that the lambda function can be invoked when an instance is shutdown in a scale-in operation.
      - Log in your EC2 instance which you have installed and configured awscli.
      - Run following command:</br> 
      ```
      aws autoscaling put-lifecycle-hook --lifecycle-hook-name hook_name \
	    --auto-scaling-group-name autoscaling_group_name --notification-target-arn sns_topic_arn \
		--role-arn sns_publishing_role \
		--lifecycle-transition autoscaling:EC2_INSTANCE_TERMINATING --heartbeat-timeout 330
      ```
      
	  Notes:
	  </br>
	  - You can change '330' to your own time. It should be longer than timeout value of Lambda function.
      - *hook_name* can be any name you want to use as long as it is not same as any other lifecycle hook names.
      - *autoscaling_group_name* is the name of the Auto Scaling group created in step 16.
      - *sns_topic_arn* is the ARN of the SNS topic created in step 8.
      - *sns_publishing_arn* is the ARN of IAM role created in step 9.
       

# FAQ

Q. Can I only install CentrifyDC but not join to AD?

Yes. You can set CENTRIFYDC_JOIN_TO_AD to no in the user data.  You also do not need to specify CENTRIFYDC_KEYTAB_S3_BUCKET and CENTRIFYDC_ZONE_NAME.

Q. Can I specify additional packages to be installed for CentrifyDC?

Yes. You can specify additional packages in parameters CENTRIFYDC_ADDITIONAL_PACKAGES.

Q. Can I specify additional options for adjoin or cenroll?

Yes. You can specify additional options in parameter CENTRIFYDC_ADJOIN_ADDITIONAL_OPTIONS
or CENTRIFYCC_CENROLL_ADDITIONAL_OPTIONS.

Q. Can I output debug information?

Yes. You can set DEBUG_SCRIPT to yes and the centrifydc.sh/centrifycc.sh will enable 'set -x'.

Q. Can I specify what to use as the network address in created CPS resource?

Yes. You can set parameter CENTRIFYCC_NETWORK_ADDR_TYPE to specify public
IP(set to PublicIP), private IP(set to PrivateIP), or host name(set to HostName)
as your network address in CPS resource.

Q. Can I specify my computer name in Active Directory while adjoin?

Yes. You can set CENTRIFYDC_HOSTNAME_FORMAT. Currently we only support using 
aws instance id(set to INSTANCE_ID) or private IP(set to PRIVATE_IP) as your computer name.

Q. Can I use the startup-userdata.sh in my standalone EC2 instances not mananged by AutoScaling Group?

Yes. You do not need AWSLambdaFullAccess permission.  Also, the differences in deployment process are:
- You can skip steps 5 through 12, and also skip steps 15 through 17.
- If the instance needs to join to Active Directory, you still need to create an IAM role that can access the S3 bucket using the IAM policy created in step 13.
- There is no lambda function support.  You need to manually run cunenroll and/or adleave to clean up before you terminate the instance.

Q. Why don't I get Public IP while enroll EC2 for Linux to Centrify identity?

You shall make sure that your AutoScaling has enabled public IP assignment and
set CENTRIFYCC_NETWORK_ADDR_TYPE to yes if you want to use public IP as your
address while running cenroll. If you want to use hostname or private IP as your
address parameter of cenroll, you need not a public IP for your EC2 and only need to 
set CENTRIFYCC_NETWORK_ADDR_TYPE parameter to PrivateIP or HostName.

Q. Can I view any log output after running startup-userdata.sh?

Yes. You can find the log in /tmp/auto_centrify_deployment/centrifycc/deploy.log
for CentrifyCC and in /tmp/auto_centrify_deployment/centrifydc/deploy.log for CentrifyDC.

Q. Why don't we support SuSE currently?

We use AWS Run Command in AWS Lambda function to automatically run 'adleave'
or 'cunenroll' to release server's resource while autoscaling in. But AWS
doesn't support Run Command on SuSE currently.

Q. What does error "x509: certificate signed by unknown authority" mean?

Your computer needs to be enrolled to Centrify Identity Platform, but none of
the server certificates can be verified. Certificate problems may indicate
potential security risks. Please contact your administrator to configure the
root CA certificate.
References:
  - https://centrify.force.com/support/Article/KB-7973-How-to-configure-Linux-machine-trusted-certificate-chain-to-perform-enrollment-for-Centrify-Agent

Q. How to use "user data" to run orchestration script on AWS instances?

From AWS documentation:

"Scripts entered as user data are executed as the root user, so do not use the
sudo command in the script. Remember that any files you create will be owned by
root; if you need non-root users to have file access, you should modify the
permissions accordingly in the script. Also, because the script is not run
interactively, you cannot include commands that require user feedback (such as
yum update without the -y flag)." [1]

"User data is limited to 16 KB." [2]

References:
[1] Running Commands on Your Linux Instance at Launch
  - http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html

[2] Instance Metadata and User Data
  - http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html

