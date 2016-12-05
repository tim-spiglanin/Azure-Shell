#!/bin/bash

REQUIRED_MONO_VERSION="4.0.1"



# assume that these variable will be passed somehow, maybe as ENV variables
execution_server_path="/home/adminuser/ExecutionServer"
cs_server_host="192.168.120.20"
cs_server_user="admin"
cs_server_pass="admin"
es_name="TEST_ES_NAME"



command_exists () {
    type "$1" &> /dev/null ;
}

contains() {
    string="$1"
    substring="$2"

    if test "${string#*$substring}" != "$string"
    then
        return 0    # $substring is in $string
    else
        return 1    # $substring is not in $string
    fi
}

unistall_mono_old_version () {
	echo "Uninstalling old Mono..."
	yes | yum remove mono
	yes | yum autoremove
}

install_mono () {
	echo "installing mono v$REQUIRED_MONO_VERSION"
	# Obtain necessary gpg keys by running the following:
	wget http://download.mono-project.com/repo/xamarin.gpg
	# Import gpg key by running the following:
	rpm --import xamarin.gpg
	# Add Mono repository
	yum-config-manager --add-repo http://download.mono-project.com/repo/centos/
	yes | yum install epel-release
	yum -y update
	# Install Mono
	yes | yum install mono-devel-4.0.1 --skip-broken
	yes | yum install mono-complete-4.0.1 --skip-broken
	# Install Python pip
	yes | yum -y install python-pip
	yes | pip install -U pip
	# Install required stuff to build cryptography package
	yes | yum -y install gcc 
	yes | yum -y install python-devel
	yes | yum -y install openssl-devel
	# Install requiered packages for the QsDriverHost
	pip install -r $execution_server_path/packages/VirtualEnvironment/requirements.txt
	
}

setup_supervisor() {
	# Install Needed Package
	yes | yum install python-setuptools
	yes | yum install supervisor
	# create config file
	echo_supervisord_conf > /etc/supervisord.conf
	echo -e '\n[program:cloudshell_execution_server]\ncommand=/usr/bin/mono '$execution_server_path'/QsExecutionServer.exe console\nenvironment=MONO_IOMAP=all\n' >> /etc/supervisord.conf
}

if [command_exists mono]
	then
		echo "Mono installed, checking version..."
		res=$(mono -V);
	
		if ! [contains "res" REQUIRED_MONO_VERSION]
			then
				echo "Mono Version is not $REQUIRED_MONO_VERSION"
				unistall_mono_old_version
				install_mono
	fi
else
	install_mono
fi

setup_supervisor

python_path=$(which python)

# add python path to customer.config
sed -i "s~</appSettings>~<add key='ScriptRunnerExecutablePath' value='${python_path}' />\n</appSettings>~g" customer.config

/usr/bin/mono $execution_server_path/QsExecutionServerConsoleConfig.exe /s:$cs_server_host /u:$cs_server_user /p:$cs_server_pass /esn:$es_name

service supervisord start

