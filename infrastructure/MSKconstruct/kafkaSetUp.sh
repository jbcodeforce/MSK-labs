msk_cluster_arn=????
region=???
topic_name=???


echo "TLS=$(aws kafka describe-cluster --cluster-arn $msk_cluster_arn --query "ClusterInfo.ZookeeperConnectString" --region $region)" >> /etc/environment
./kafka-topics.sh --bootstrap-server $ZK --command-config client.properties --create --replication-factor 3 --partitions 3 --topic $topic_name