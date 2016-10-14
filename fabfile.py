#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import with_statement
from fabric.api import show, local, settings, prefix, abort, run, cd, env, require, hide, execute, put, lcd
from fabric.contrib.console import confirm
from fabric.network import disconnect_all
from fabric.colors import green as _green, yellow as _yellow, red as _red
from fabric.contrib.files import exists
from fabric.operations import local as lrun, run
from fabric.api import task
from fabric.utils import error
import os
import time

# ssh.util.log_to_file("paramiko.log", 10)

"""
env.use_ssh_config = True
env.hosts = ["52.24.208.205"] ##For t2 medium
#env.hosts = ["ec2-54-186-203-98.us-west-2.compute.amazonaws.com"] ##For m3.large
env.user = "ubuntu"
env.key_filename = "/home/kaali/Programs/Python/MadMachinesNLP01/MadMachines.pem"
env.warn_only = True

This is the file which remotely makes an ec2 instance for the use of this repository
"""

"""
#!/usr/bin/env python
"""

VIRTUAL_ENVIRONMENT = "/home/{0}/VirtualEnvironment".format(env["user"])
print VIRTUAL_ENVIRONMENT

PATH = "/home/{0}/VirtualEnvironment/Canworks/".format(env["user"])
print PATH

TAGGERS_PATH = "{0}/Text_Processing/PosTaggers/hunpos-1.0-linux".format(PATH)

@task
def localhost():
    env.run = lrun
    env.hosts = ['localhost']

@task
def basic_setup():
    """"
    This method should be run before installing virtual environment as it will install python pip
    required to install virtual environment
    """
    env.run("sudo apt-get update")
    env.run("sudo apt-get upgrade")
    env.run("sudo apt-get install -y python-pip")
    env.run("sudo apt-get install -y libevent-dev")
    env.run("sudo apt-get install -y python-all-dev")
    env.run("sudo apt-get install -y ipython")
    env.run("sudo apt-get install -y libxml2-dev")
    env.run("sudo apt-get install -y libxslt1-dev") 
    env.run("sudo apt-get install -y python-setuptools python-dev build-essential")
    env.run("sudo apt-get install -y libxml2-dev libxslt1-dev lib32z1-dev")
    env.run("sudo apt-get install -y python-lxml")

@task
def get_host():
        if env["host"] == "localhost":
                print "We are on localhost"
        else:
                print env["host"], env["user"]


def install_phantomjs():
        """
        http://phantomjs.org/build.html
        """
        env.run ("sudo apt-get install build-essential g++ flex bison gperf ruby perl \
                  libsqlite3-dev libfontconfig1-dev libicu-dev libfreetype6 libssl-dev \
                    libpng-dev libjpeg-dev python libX11-dev libxext-dev")
        env.run("sudo git clone git://github.com/ariya/phantomjs.git")
        with lcd(VIRTUAL_ENVIRONMENT+"/MadMachinesNLP01Scraping/"+"/phantomjs"):
            env.run("sudo git checkout 2.0")
            env.run("sudo ./build.sh")
@task
def deploy(no_of_workers):
    # execute(basic_setup)
    #execute(MadMachinesNLP01Scraping)
    execute(StartWorkers,no_of_workers)


def MadMachinesNLP01Scraping():
    # env.run("sudo apt-get install -y openssh-server")
    # env.run("sudo restart ssh")
    # env.run("sudo apt-get install -y python-virtualenv")
    # env.run("sudo apt-get install -y redis-server")
    # env.run("sudo apt-get install -y mongodb-server")
    # env.run("sudo apt-get install -y tor")
    # env.run("sudo apt-get install -y git")

    # env.run("sudo virtualenv VirtualEnvironment")
    with lcd(VIRTUAL_ENVIRONMENT):
        with prefix(". "+VIRTUAL_ENVIRONMENT+ "/bin/activate"):
            env.run("pwd")
            if not exists(VIRTUAL_ENVIRONMENT+"/MadMachinesNLP01Scraping"):
            	env.run("sudo git clone https://github.com/kaali-python/MadMachinesNLP01Scraping.git")
            	with lcd(VIRTUAL_ENVIRONMENT+"/MadMachinesNLP01Scraping"):
			env.run("sudo pip install -U pip")
            		env.run("sudo "+VIRTUAL_ENVIRONMENT+"/bin/pip install -r requirement.txt")
            		execute(install_phantomjs)
            else:
            	with lcd(VIRTUAL_ENVIRONMENT+"/MadMachinesNLP01Scraping"):
            		#env.run("git init")
            		#env.run("sudo git fetch --all")
			#env.run("sudo git reset --hard origin/master")
			#env.run("sudo pip install -U pip")
			env.run(VIRTUAL_ENVIRONMENT+"/bin/pip install -U -r requirement.txt")
    env.run("sudo chown -R "+env["user"]+":"+env["user"]+" "+VIRTUAL_ENVIRONMENT)
    env.run("sudo chmod -R a+rX "+VIRTUAL_ENVIRONMENT)

@task
def StartWorkers(no_of_workers):
    with lcd(VIRTUAL_ENVIRONMENT):
        with prefix(". "+VIRTUAL_ENVIRONMENT+ "/bin/activate"):
            with lcd(VIRTUAL_ENVIRONMENT+"/MadMachinesNLP01Scraping"):
                env.run("ls *.log > workers.txt")
                m=0
                with open(VIRTUAL_ENVIRONMENT+"/MadMachinesNLP01Scraping"+'/workers.txt','r+') as f:
                    workers_list=f.read().split("\n")
                print workers_list
                for logfile in workers_list:
                    if logfile.startswith('worker'):
                        W_no=int(logfile.split("worker")[1].split(".log")[0])
                        if W_no>=m:
                            m=W_no
                print m
                worker_names = ""
                for i in xrange(int(no_of_workers)):
                     worker_names+="worker"+str(m+i+1)+" "
                print worker_names
                env.run(VIRTUAL_ENVIRONMENT+"/bin/celeryd-multi start "+worker_names+"-c 1 -A tasks")
                env.run("ps aux | grep 'celery worker'")
                # env.run("python -c "+"'from tasks import runn ; runn.apply_async(["+'"'+str(url)+'"'+","+str(number_of_restaurants)+", "+str(skip)+", "+'"'+Type_of_url+'"'+"])'")
        # env.run("ps auxww | grep phantomjs | awk '{print $2}' | xargs kill -9")
        # env.run("ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9")
        print "Running"
