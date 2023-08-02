msk_cluster_arn=????
region=???
topic_name=???

source ~/.bash_profile
echo "TLS=$(aws kafka describe-cluster --cluster-arn $msk_cluster_arn --query "ClusterInfo.ZookeeperConnectString" --region $region)" >> /etc/environment
echo "CLASSPATH=/home/ec2-user/aws-msk-iam-auth-1.1.7-all.jar" >> /etc/environment
./kafka-topics.sh --bootstrap-server $ZK --command-config client.properties --create --replication-factor 3 --partitions 3 --topic $topic_name