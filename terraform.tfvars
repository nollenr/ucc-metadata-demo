my_ip_address = "98.148.51.154"
aws_region_01 = "us-east-2"
owner = "nollen"
project_name = "ucc-demo"
crdb_instance_key_name = "nollen-cockroach-revenue-us-east-2-kp01"
vpc_cidr = "192.168.7.0/24"

# -----------------------------------------
# CRDB Specifications
# -----------------------------------------
crdb_nodes = 3
crdb_instance_type = "m6g.xlarge"
crdb_store_volume_type = "gp3"
crdb_store_volume_size = 8
# iops and throughput are only used for gp3 volumes
# ratio of IOPS to volume size cannot be greater than 500
# ration of throughput to volume size cannot be greater than 25
# crdb_store_volume_iops = 3000
# crdb_store_volume_throughput = 125
crdb_version = "24.3.18"
crdb_arm_release = "yes"
crdb_enable_spot_instances = "no"
crdb_wal_failover = "yes"
create_db_ui_user = "yes"  # <------------ setting this to yes, requires you to set an environment variable.  See the NOTE below.
db_ui_user_name = "bob"
# **********************************************************
# NOTE:  If you want to have a DB UI user created, define
#        the shell varaible "TF_VAR_db_ui_user_password"
#        prior to running this script!    The value will
#        automatically be picked up by this HCL and applied
# **********************************************************
# db_ui_user_password = ""
cache = 0.35             # Must be a decimal value.
max_sql_memory = 0.35    # Must be a decimal value.
install_enterprise_keys = "yes"

# HA Proxy
include_ha_proxy = "yes"
haproxy_instance_type = "m6i.large"

# APP Node
include_app = "yes"
app_instance_type = "m6i.large"

create_admin_user = "yes"
admin_user_name = "ron"
