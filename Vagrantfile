# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  config.vm.box = "ubuntu/trusty64"
  # config.vm.box_check_update = false
  config.vm.network "forwarded_port", guest: 5000, host: 5000
  # config.vm.network "private_network", ip: "192.168.33.10"
  # config.vm.network "public_network"

  # config.vm.synced_folder "../data", "/vagrant_data"
  config.vm.synced_folder ".", "/vagrant/orlo",
     type: "virtualbox", create: "true", owner: "vagrant"

  config.vm.provider "virtualbox" do |vb|
  #   vb.gui = true
  #   vb.memory = "1024"
    vb.cpus = "2"
  end

  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  config.vm.provision "shell", inline: <<-SHELL
    # sudo sed -i 's/archive.ubuntu.com/nl.archive.ubuntu.com/g' /etc/apt/sources.list
    apt-get update
    apt-get -y install python-pip python-dev postgresql postgresql-server-dev-all
    echo "CREATE USER orlo WITH PASSWORD 'password'; CREATE DATABASE orlo OWNER orlo; " \
        | sudo -u postgres -i psql

    # python-ldap dependencies
    apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev

    # Build tools
    apt-get -y install build-essential git-buildpackage debhelper python-dev \
        python3-dev dh-systemd python-virtualenv
    wget -P /tmp/ \
        'https://launchpad.net/ubuntu/+archive/primary/+files/dh-virtualenv_0.11-1_all.deb'
    dpkg -i /tmp/dh-virtualenv_0.11-1_all.deb
    apt-get -f install -y

    pip install --upgrade pip setuptools
    pip install --upgrade virtualenv

    # Virtualenv is to avoid conflict with Debian's python-six
    virtualenv /home/vagrant/virtualenv/orlo
    source /home/vagrant/virtualenv/orlo/bin/activate
    echo "source ~/virtualenv/orlo/bin/activate" >> /home/vagrant/.profile

    pip install -r /vagrant/orlo/requirements.txt
    pip install -r /vagrant/orlo/requirements_testing.txt
    pip install -r /vagrant/orlo/docs/requirements.txt

    sudo chown -R vagrant:vagrant /home/vagrant/virtualenv

    # Create the database
    cd /vagrant/orlo
    python create_db.py
    python setup.py develop
    mkdir /etc/orlo
    chown vagrant:root /etc/orlo
    chown vagrant:root /vagrant
  SHELL
end
