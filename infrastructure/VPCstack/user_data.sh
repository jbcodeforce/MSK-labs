sudo yum update
sudo yum install git
wget --no-check-certificate -c --header "Cookie: oraclelicense=accept-securebackup-cookie" https://download.oracle.com/java/17/latest/jdk-17_linux-x64_bin.rpm
sudo rpm -Uvh jdk-17_linux-x64_bin.rpm
sudo wget http://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo -O /etc/yum.repos.d/epel-apache-maven.repo
sudo sed -i s/\$releasever/7/g /etc/yum.repos.d/epel-apache-maven.repo
sudo yum install -y apache-maven
sudo yum install docker
sudo usermod -a -G docker ec2-user
newgrp docker
sudo systemctl start docker.service

wget https://archive.apache.org/dist/kafka/3.4.1/kafka_2.12-3.4.1.tgz
tar -xzf kafka_2.12-3.4.1.tgz 
cd kafka_2.12-3.4.1/libs
wget https://github.com/aws/aws-msk-iam-auth/releases/download/v1.1.7/aws-msk-iam-auth-1.1.7-all.jar
cd ../bin
echo "security.protocol=SASL_SSL
sasl.mechanism=AWS_MSK_IAM
sasl.jaas.config=software.amazon.msk.auth.iam.IAMLoginModule required;
sasl.client.callback.handler.class=software.amazon.msk.auth.iam.IAMClientCallbackHandler" > client.properties