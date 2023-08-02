sudo yum update
sudo yum install  -y java-11-amazon-corretto-headless git
cd /home/ec2-user
sudo wget http://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo -O /etc/yum.repos.d/epel-apache-maven.repo
sudo sed -i s/\$releasever/7/g /etc/yum.repos.d/epel-apache-maven.repo
sudo yum install -y apache-maven
sudo yum install docker
sudo usermod -a -G docker ec2-user
newgrp docker
sudo systemctl start docker.service
wget https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip 
unzip awscli-exe-linux-x86_64.zip
./aws/install
wget https://archive.apache.org/dist/kafka/3.4.1/kafka_2.12-3.4.1.tgz
tar -xzf kafka_2.12-3.4.1.tgz 
export PATH=/usr/local/bin:$PATH

cd kafka_2.12-3.4.1/libs
wget https://github.com/aws/aws-msk-iam-auth/releases/download/v1.1.7/aws-msk-iam-auth-1.1.7-all.jar
cd ../bin
echo "security.protocol=SASL_SSL
sasl.mechanism=AWS_MSK_IAM
sasl.jaas.config=software.amazon.msk.auth.iam.IAMLoginModule required;
sasl.client.callback.handler.class=software.amazon.msk.auth.iam.IAMClientCallbackHandler" > client.properties
source ~/.bash_profile
echo "CLASSPATH=/home/ec2-user/aws-msk-iam-auth-1.1.7-all.jar" >> /etc/environment
