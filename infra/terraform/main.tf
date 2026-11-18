data "aws_availability_zones" "available" {state="available"}
locals {
  name="${var.project}-${var.environment}"
  azs=slice(data.aws_availability_zones.available.names,0,2)
  tags={Project=var.project,Environment=var.environment,ManagedBy="Terraform"}
}
resource "aws_vpc" "this" {
  cidr_block=var.vpc_cidr
  enable_dns_hostnames=true
  enable_dns_support=true
  tags=merge(local.tags,{Name=local.name})
}
resource "aws_internet_gateway" "this" {vpc_id=aws_vpc.this.id
tags=local.tags}
resource "aws_subnet" "public" {
  count=2
  vpc_id=aws_vpc.this.id
  cidr_block=cidrsubnet(var.vpc_cidr,8,count.index)
  availability_zone=local.azs[count.index]
  map_public_ip_on_launch=true
  tags=merge(local.tags,{Name="${local.name}-public-${count.index}","kubernetes.io/role/elb"="1"})
}
resource "aws_subnet" "private" {
  count=2
  vpc_id=aws_vpc.this.id
  cidr_block=cidrsubnet(var.vpc_cidr,8,count.index+10)
  availability_zone=local.azs[count.index]
  tags=merge(local.tags,{Name="${local.name}-private-${count.index}","kubernetes.io/role/internal-elb"="1"})
}
resource "aws_eip" "nat" {domain="vpc"
tags=local.tags}
resource "aws_nat_gateway" "this" {
  allocation_id=aws_eip.nat.id
  subnet_id=aws_subnet.public[0].id
  depends_on=[aws_internet_gateway.this]
  tags=local.tags
}
resource "aws_route_table" "public" {vpc_id=aws_vpc.this.id
 tags=local.tags}
resource "aws_route" "public" {route_table_id=aws_route_table.public.id
destination_cidr_block="0.0.0.0/0"
gateway_id=aws_internet_gateway.this.id}
resource "aws_route_table_association" "public" {count=2
subnet_id=aws_subnet.public[count.index].id
route_table_id=aws_route_table.public.id}
resource "aws_route_table" "private" {vpc_id=aws_vpc.this.id
tags=local.tags}
resource "aws_route" "private" {route_table_id=aws_route_table.private.id
destination_cidr_block="0.0.0.0/0"
nat_gateway_id=aws_nat_gateway.this.id}
resource "aws_route_table_association" "private" {count=2
subnet_id=aws_subnet.private[count.index].id
route_table_id=aws_route_table.private.id}

data "aws_iam_policy_document" "eks_assume" {
  statement {actions=["sts:AssumeRole"]
principals {type="Service"
identifiers=["eks.amazonaws.com"]}}
}
resource "aws_iam_role" "eks" {name="${local.name}-eks-role"
assume_role_policy=data.aws_iam_policy_document.eks_assume.json
tags=local.tags}
resource "aws_iam_role_policy_attachment" "eks" {role=aws_iam_role.eks.name
policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"}
resource "aws_eks_cluster" "this" {
  name=local.name
  role_arn=aws_iam_role.eks.arn
  vpc_config {subnet_ids=aws_subnet.private[*].id
endpoint_public_access=true
endpoint_private_access=true}
  access_config {authentication_mode="API_AND_CONFIG_MAP"}
  depends_on=[aws_iam_role_policy_attachment.eks]
  tags=local.tags
}
data "aws_iam_policy_document" "nodes_assume" {
  statement {actions=["sts:AssumeRole"]
principals {type="Service"
identifiers=["ec2.amazonaws.com"]}}
}
resource "aws_iam_role" "nodes" {name="${local.name}-nodes-role"
assume_role_policy=data.aws_iam_policy_document.nodes_assume.json
tags=local.tags}
resource "aws_iam_role_policy_attachment" "nodes_worker" {role=aws_iam_role.nodes.name
policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"}
resource "aws_iam_role_policy_attachment" "nodes_ecr" {role=aws_iam_role.nodes.name
policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly"}
resource "aws_iam_role_policy_attachment" "nodes_cni" {role=aws_iam_role.nodes.name
policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"}
resource "aws_eks_node_group" "this" {
  cluster_name=aws_eks_cluster.this.name
  node_group_name="${local.name}-nodes"
  node_role_arn=aws_iam_role.nodes.arn
  subnet_ids=aws_subnet.private[*].id
  instance_types=var.eks_node_instance_types
  scaling_config {desired_size=var.eks_node_desired
min_size=var.eks_node_min
max_size=var.eks_node_max}
  update_config {max_unavailable=1}
  depends_on=[aws_iam_role_policy_attachment.nodes_worker,aws_iam_role_policy_attachment.nodes_ecr,aws_iam_role_policy_attachment.nodes_cni]
  tags=local.tags
}
resource "aws_ecr_repository" "api" {name=local.name
image_scanning_configuration {scan_on_push=true}
encryption_configuration {encryption_type="AES256"}
tags=local.tags}
resource "aws_security_group" "data" {name="${local.name}-data"
vpc_id=aws_vpc.this.id
tags=local.tags}
resource "aws_vpc_security_group_ingress_rule" "pg" {security_group_id=aws_security_group.data.id
ip_protocol="tcp"
from_port=5432
to_port=5432
referenced_security_group_id=aws_eks_cluster.this.vpc_config[0].cluster_security_group_id}
resource "aws_vpc_security_group_ingress_rule" "redis" {security_group_id=aws_security_group.data.id
ip_protocol="tcp"
from_port=6379
to_port=6379
referenced_security_group_id=aws_eks_cluster.this.vpc_config[0].cluster_security_group_id}
resource "aws_db_subnet_group" "this" {name=local.name
subnet_ids=aws_subnet.private[*].id
tags=local.tags}
resource "aws_db_instance" "postgres" {
  identifier="${local.name}-db"
  engine="postgres"
engine_version="16"
  instance_class=var.db_instance_class
  allocated_storage=20
max_allocated_storage=100
  storage_encrypted=true
db_name="ecomm"
username=var.database_username
  manage_master_user_password=true
  db_subnet_group_name=aws_db_subnet_group.this.name
  vpc_security_group_ids=[aws_security_group.data.id]
  publicly_accessible=false
backup_retention_period=7
  skip_final_snapshot=false
final_snapshot_identifier="${local.name}-final-snapshot"
  deletion_protection=true
tags=local.tags
}
resource "aws_elasticache_subnet_group" "this" {name=local.name
subnet_ids=aws_subnet.private[*].id}
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id="${local.name}-redis"
description="Redis for ${local.name}"
  node_type="cache.t4g.micro"
num_cache_clusters=2
  engine="redis"
engine_version="7.1"
  automatic_failover_enabled=true
multi_az_enabled=true
  at_rest_encryption_enabled=true
transit_encryption_enabled=true
  subnet_group_name=aws_elasticache_subnet_group.this.name
  security_group_ids=[aws_security_group.data.id]
  tags=local.tags
}
resource "aws_s3_bucket" "catalog" {bucket_prefix="${local.name}-catalog-"
force_destroy=false
tags=local.tags}
resource "aws_s3_bucket_public_access_block" "catalog" {bucket=aws_s3_bucket.catalog.id
block_public_acls=true
block_public_policy=true
ignore_public_acls=true
restrict_public_buckets=true}
resource "aws_s3_bucket_server_side_encryption_configuration" "catalog" {bucket=aws_s3_bucket.catalog.id
rule {apply_server_side_encryption_by_default {sse_algorithm="AES256"}}}
resource "aws_s3_bucket_versioning" "catalog" {bucket=aws_s3_bucket.catalog.id
versioning_configuration {status="Enabled"}}
