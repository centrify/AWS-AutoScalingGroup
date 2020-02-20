# Introduction

This is the README file for using sample orchestration scripts to automatically
enroll Linux-based cloud instances to Centrify Identity Platform or
to automatically join the instance to Active Directory.

You need to set up your configuration by modifying the top part of the sample orchestration
script startup-userdata.sh.  When you launch the new Auto Scaling or EC2 instance, you 
need to upload the script as "user data".  

The following platforms are supported:
* Red Hat Enterprise Linux 7.5 or later
* Ubuntu Server 16.04 LTS
* Ubuntu Server 18.04 LTS
* Amazon Linux AMI 2018.03.0
* Amazon Linux 2 LTS
* CentOS 7.x


# Prerequisite
- You need the following AWS permissions:
  - permission to create, modify, read, list and delete IAM Policies and Roles.
  - Full permission to EC2
  - AWSLambdaFullAccess
- Create one or more subnets in your VPC for lambda functions to use. These subnets must be private subnets. The routing table of these private subnets must point to a NAT instance or AWS NAT instance that resides in the public subnet of the VPC.
- You need an EC2 instance that has AWS CLI commands installed.  Please refer to 
   http://docs.aws.amazon.com/cli/latest/userguide/installing.html#install-with-pip
   for more information about awscli installation.  Make sure that you have configured awscli 
   using the `aws configure` command. Please refer to 
   http://docs.aws.amazon.com/cli/latest/reference/configure/index.html#examples
   for more information about configuring AWS CLI commands.
- If you need to use Centrify Infrastructure Services to join the AWS instance to Active Directory, 
  you also need the followings:
  -  An AD user who joins the EC2 instance for Linux to your centrify zone. 
     You need to make sure that the AD user has following two permissions at least:
    - Delegate `Join a computer to the domain` in `Active Directory Users and Computers`.
    - Delegate 'Join computers to the zone' in `Centrify Access Manager`.
  - Permission to create and upload files to a S3 bucket
  - An EC2 instance that has Centrify Infrastructure Services installed and joined to your Active Directory.
  - An account in the Centrify Support website 
	 (http://www.centrify.com/support).   Follow the instruction in 
	 https://www.centrify.com/support/customer-support-portal/repos to generate the repo key. Use the string
	 before @repo.centrify.com to set up the parameter CENTRIFY_REPO_CREDENTIAL.  For example, if the repo key 
	 is 1111111122222233333333333333344444555555:777888880000099999991234567890abcdefghij@repo.centrify.com, set
	 CENTRIFY_REPO_CREDENIIAL=1111111122222233333333333333344444555555:777888880000099999991234567890abcdefghij

# Configuration parameters
You can specify the AWS deployment configuration in the `User Data` of the AWS instance.   You need to download the file 
startup-userdata.sh and set up the parameter values in the top part of the file.  The whole file must be copied to 
the `User Data` of the new EC2 instance and/or Auto Scaling group launch configuration.

## Centrify Agent for Linux parameters
The following parameters are for enrolling the AWS instances to Centrify Identity Platform.

| Parameter | Description | Optional | Example |
| --- | --- | --- | --- | 
| DEPLOY_CENTRIFYCC | Specifies enroll to Centrify Identity Platform | no | yes |
| CENTRIFYCC_TENANT_URL | Centrify Identity Platform URL | no | *my-company.deployment.centrify.com* |
| CENTRIFYCC_ENROLLMENT_CODE | Enrollment code to use | no | *12345678-1234-5678-1234-ABCDEF123456* |
| CENTRIFYCC_AGENT_AUTH_ROLES | Roles where members can log in to the instance.  Specifies as a comma separated list | yes | *my_login_role* |
| CENTRIFYCC_AGENT_SETS | Sets that  the machine will be added as a member.  Specifies as a comma separated list | yes | *my_machine_sets* |
| CENTRIFYCC_FEATURES | Features to enable for the agent.  Specifies as a comma separated list.  Valid values are: **agentauth**, **aapm**, **all** | no | agentauth,aapm |
| CENTRIFYCC_NETWORK_ADDR_TYPE | Value to use to as network address for the created resource.  Allowed values are PublicIP, PrivateIP, Hostname. | no | PublicIP |
| CENTRIFYCC_COMPUTER_NAME_PREFIX | Prefix to use for computer name | yes | *apac* |
| CENTRIFYCC_CENROLL_ADDITIONAL_OPTIONS | Additional options for cenroll command line | yes | --resource-setting ProxyUser:centrify | 

Notes:
- The AWS instance ID used as the computer name for the created resource.  If CENTRIFYCC_COMPUTER_NAME_PREFIX is specified, the computer name 
will be *\<CENTRIFYCC_COMPUTER_NAME_PREFIX\>*-*\<AWS Instance ID\>*.  Otherwise, it will be *\<AWS Instance ID\>*.
-Both CENTRIFYCC_AGENT_AUTH_ROLES and CENTRIFYCC_AGENT_SETS cannot be empty.



## Centrify Infrastructure Services agent parameters
The following parameters are for joining to Active Directory using the Centrify Infrastructure Services agent.

| Parameter | Description | Optional | Example |
| --- | --- | --- | --- | 
| DEPLOY_CENTRIFYDC | Install Centrify Infrastructure Services agent | no | yes |
| CENTRIFY_REPO_CREDENTIAL | Credential required to access Centrify Repo | no | *a long string* |
| CENTRIFYDC_JOIN_TO_AD | Whether to join to Active Directory | no | yes |
| CENTRIFYDC_ZONE_NAME | Name of zone to join to | no | *my_zone* |
| CENTRIFYDC_USE_CUSTOM_KEYTAB_FUNCTION | Whether login.keytab is retrieved using default method or a custom function provided by user. | no | yes |
| CENTRIFYDC_CUSTOM_KEYTAB_FUNCTION | The name of the custom function used to retrieve login.keytab file. | yes | my_function |
| custom_keytab_function | Customized function for retrieving the login.keytab file. Function name is specified in CENTRIFYDC_CUSTOM_KEYTAB_FUNCTION. | yes, if using customized function; no for default download. Be sure to save the login.keytab file to /tmp/auto_centrify_deployment/centrifydc; return 0 for success, others for error | wget -O /tmp/auto_centrify_deployment/centrifydc/login.keytab https://your_bucket_name.s3.amazonaws.com/path/to/file <br> r=$? <br> return $r|
| CENTRIFYDC_KEYTAB_S3_BUCKET | Name of S3 bucket where the login.keytab file for the enroller is stored | no, if using customized function; yes for defualt download | *my_s3_bucket* |
| CENTRIFYDC_ADDITIONAL_PACKAGES | Name of additional packages to install.  Allowed values are: **centrifydc-openssh**, **centrifydc--ldapproxy** | yes | |
| CENTRIFYDC_ADJOIN_ADDITIONAL_OPTIONS | Additional options for adjoin command | yes | |

Note that host name is limited to 15 characters.  If the instance ID is longer than 15 characters, the first 15 characters of instance ID will be used 
and there is a remote possibility of hostname conflicts.   We recommend to use PRIVATE-IP address for hostname.


# Deployment process
  1. If you do not need to install/deploy Centrify Infrastructure Services agent to join to Active Directory,
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
     - *your_ad_user* is the user who joins the instance to Active Directory.</br>
	 For example:</br>
	 ```
       adkeytab -A -K login.keytab -u admin1  -p admin1_pass join_user1
	 ```
	 
  1. If you are using a customized function to get the login.keytab, you can skip to step 3.
     </br>
	 You need to sign in https://console.aws.amazon.com/s3 to create a S3 bucket and then upload 
     login.keytab file (created in step 1) to the bucket. You can refer to
     http://docs.aws.amazon.com/AmazonS3/latest/gsg/CreatingABucket.html about how to create a bucket.

  1. Create your Key Pair if you don't have one so that you can log into your EC2 instances. You can refer to</br>
      http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair about 
      how to create Key Pair.

  1. Create VPC, subnet and security group for your instances in the new Auto Scaling group.
  
  1. Create IAM role for lambda function.
      - Sign in AWS Management Console and select IAM Service.
	  - Select Roles, and click on `Create Role`.
		- Select `AWS Service` as type of trusted entity.
		- Select `Lambda` as the service that will use this role. Clikc `Next: Permissions`.
		- Attach the predefined policy AWSLambdaVPCAccessExecutionRole to the role.
		- Click `Next: Review` to review the role. 
		- Specify the role name and description.
		- Click `Create Role`.

  1. In IAM Service, create the following IAM policy and associate it with IAM role above:
     ```
     {
         "Version": "2012-10-17",
         "Statement": [
            {
            "Effect": "Allow",
            "Action": [
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
            "Resource": "*",
            "Effect": "Allow"
            }
        ]
     }
     ```

  1. Create Lambda Function.
      - Download centrify-cleanup-lambda-1-0.zip to your local system.
	  - Select Lambda Service in AWS Console.
      - Select `Functions`, and then click `Create function` button.
	  - Select `Author from scratch` to create the function template.
      - In the `Author from scratch` panel:
		- Enter the name of your lambda function in `Name` box.
	    - Choose `Python 2.7` in `Runtime` box
		- For the 'Role*' box, keep the default `Choose an existing role` selection.
		- Choose the IAM role that you created in step 5 in the `Existing role` box.
		- Click on `Create function`
	  - Do not add any triggers
	  - In the `Function code` panel:
	    - For `Code entry type` selection, select `Upload a .ZIP file`
		- Make sure the `Runtime` selection is `Python 2.7`.
		- Keep `lambda_function.lambda_handler` as the value in `Handler` box.
		- click `Upload` button to upload the copy of centrify-cleanup-lambda-1-0.zip that you just downloaded.
	  - Add the following two environment variables in the `Environment variables` panel:
        - clean_centrifydc:  Specify **yes** if instance is joined to Active Directory; otherwise **no**
        - clean_centrifycc: Specify **yes** if instance is enrolled to Centrify Identity Platform; otherwise **no** 
	  - In the `Basic settings` panel:
	    - For the `Timeout` setting, set timeout value to 4 min 10 sec.
	  - In the `Network` panel, set the VPC and subnet to the ones created in Prerequisite section.  Note that you may need to create a security group for the lambda instances.  No incoming internet connection is required for this security group, but it needs to allow outbound connection to internet.
	  - Click `Save` to create the lambda function.

  1. Create a Simple Notification Service (SNS) topic to publish notification of AutoScaling lifecycle hook.
     - Select Simple Notification Service in AWS Console
	 - Select `Create topic`
       - Enter topic name and description and continue to create the topic.
     - Select `Topics` to view all SNS topics.
     - Save the ARN value for the newly created topic.	 

  1. Create an IAM Role to allow Autoscaling service to publish the SNS topic.
      - Select IAM Service in AWS Console
	  - Select Roles, and click on `Create Role`.
	    - Select `AWS service` as type of trusted entity.
		- Select `Auto Scaling` as the service that will use this role.
		- Select `Auto Scaling Notification Access` as the use case for this role.
		- Select `Next: Permissions` to continue
		- In the `Attached permissions policy`, do not change/add any policy.  Just click on `Next: Review`.
		- Enter your role name and description.
		- Click `Create role` to continue.
      - Now an Autoscaling service role is created.

  1. Subscribe the SNS topic to the Lambda.
       - Select SNS Service in AWS Console
       - Select `Topics`, and select the SNS topic created in step 8. 
       - Click on `Actions` and select `Subscribe to topic` in the pull-down menuexit
       - In the `Create subscription` popup,
          - Select `AWS lambda` for `Protocol`
          - Select your lambda function in the `Endpoint` pull down menu.
          - Leave `default` in the `Version or alias` box.
          - Click `Create subscription`

  1. Create IAM Role for the instances in Auto Scaling group.
      - Select IAM Service in AWS Console
	  - Select Roles, and click on `Create Role`.
	    - Select `AWS service` as type of trusted entity.
		- Select `EC2` as the service that will use this role.
		- Select `Next: Permissions` to continue
		- In the `Attached permissions policy`, select to add `AmazonEC2ReadOnlyAccess` and `AmazonEC2RoleforSSM`.
		- Click on `Next: Review`.
		- Enter your role name and description.
		- Click `Create role` to continue.
	 
  1. If your AWS instance does not need to join to Active Directory or if it needs to join to Active Directory but you 
	  are using a customized function to get login.keytab, skip this step.</br>
	  Create the following IAM Policy and attached it to the IAM role created in step 11 above.  
	  This policy allows the instance to access the S3 bucket to download the login.keytab file. </br>
	  ```
	  {
		"Version": "2012-10-17",
		"Statement": [{ 
			"Effect": "Allow",
			"Action": [
				"s3:GetObject",
				"s3:ListBucket"
				],
			"Resource": [
				"arn:aws:s3:::your_s3_bucketname/*"
			]
		}]
	  }
	  ```
     </br>Replace *your_s3_bucketname* by the name of the S3 bucket that you created in step 2.

  1. Download startup-userdata.sh and create a userdata template.  See the section **Configuration Parameters** for more information.
     If CENTRIFYDC_USE_CUSTOM_KEYTAB_FUNCTION=yes, be sure to define a valid function with its necessary prerequisites.
  
  1. Create a Launch Configuration for Auto Scaling group. You can refer to 
      http://docs.aws.amazon.com/autoscaling/latest/userguide/GettingStartedTutorial.html#gs-create-lc for more information about creating
	  a launch configuration.
       - In `Create Launch Configuration` page:
         - choose the IAM role you created in step 11.
		 - Click `Advanced Details`
           - If you set the configuration parameter CENTRIFYCC_NETWORK_ADDR_TYPE to `PublicIP`, you need to 
             select `Assign a public IP address to every instance` for `IP address Type`.
           - Copy the user data template that you created in step 13 to the `User Data` box.
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
      - *autoscaling_group_name* is the name of the Auto Scaling group created in step 15.
      - *sns_topic_arn* is the ARN of the SNS topic created in step 8.
      - *sns_publishing_role* is the ARN of IAM role created in step 9.
       

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
set CENTRIFYCC_NETWORK_ADDR_TYPE to PublicIP if you want to use public IP as your
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

