# Instructions to roll out this demo.

## Rollout the cluster, HA Proxy & App Server
 - run keys.sh
 - apply terraform.tfvars
 - get the access keys and apply those to the session
 - terraform apply --auto-approve

## On one of the database nodes
```
sudo yum install git -y
git clone https://github.com/nollenr/ucc-metadata-demo.git
cd ucc-metadata-demo/ddl
chmod +x database_setup.sh
chmod +x dbnode_setup.sh
./dbnode_setup.sh
./database_setup.sh
```

## On the app server
```
git clone https://github.com/nollenr/ucc-metadata-demo.git
cd ucc-metadata-demo/
python3.11 demo.py
```

# Demo
## Patch the database to 25.2
```
cd crdb-ucc-metadata-demo/
python3.11 demo.py
```
Bring up the database UI
- TTL Job 
- the database UI shows one of the nodes is not patched! -- note the message at the top of the overview screen
- be sure we can see all 3 app nodes and the database terminal
- MANUALLY STOPCRDB!   
- Then run apply_upgrade.sh
- MANUALLY STARTCRDB
- Check out the database UI -- note the message changed at the top of the overview screen
```
SHOW CLUSTER SETTING version;
SET CLUSTER SETTING version='25.2';
```

## Apply a schema Change
```
use pua_demo;
ALTER TABLE buckets ADD COLUMN owner_secondary STRING NOT NULL DEFAULT 'Unknown';
```
- Be sure the 4 terminals are available to view!
- Once the "alter table" is submitted, look at the Database UI
