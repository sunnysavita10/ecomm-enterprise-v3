output "cluster_name" {value=aws_eks_cluster.this.name}
output "ecr_repository_url" {value=aws_ecr_repository.api.repository_url}
output "rds_endpoint" {value=aws_db_instance.postgres.address}
output "redis_endpoint" {value=aws_elasticache_replication_group.redis.primary_endpoint_address}
output "catalog_bucket" {value=aws_s3_bucket.catalog.bucket}
output "rds_master_secret_arn" {value=aws_db_instance.postgres.master_user_secret[0].secret_arn
sensitive=true}
