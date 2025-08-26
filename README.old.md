## Database and Application Server Prep
1.  Roll out a cluster, HA Proxy and App Server
2.  Open a connection to the DB and 2 App server Connections
3.  on the app server, create the following directory
   
```mkdir crdb-ucc-metadata-demo```

4.  Start WinSCP and copy (ron's stuff) `ucc-metadata-demo` to the app server directory created above
5.  Add license keys to the database (if not done when the cluster was rolled out.)
6.  Directly on the DB server, create an admin (bob) to use in the database console and open the console.  
 
```
create user bob with password 'bob123321bob';
grant admin to bob;
```

7.  In one of the app server nodes, start the HTTP server

```
cd /home/ec2-user/crdb-ucc-metadata-demo/ddl/demo_data
python3 -m http.server --bind $HOSTNAME 3000
```
8.  Run the setup scripts in the other app server terminal
9.  In Visual Studio Code, change the IP address in setup_script_02.sql to the IP of the app server node
10. Run the setup scripts 
```
cd /home/ec2-user/crdb-ucc-metadata-demo/ddl
CRDB
\i setup_script_00.sql
\i setup_script_01.sql
\i setup_script_02.sql
\i setup_script_03.sql
```

## Database Upgade Prep
1.  run SETCRDBVARS 
2.  Figure out which CRDBNODE you're on.
3.  Create `apply_update.sh` on node 1
4.  Create `prep_update.sh` on node 1
5.  Make the shell scripts executable

```
chmod +x *.sh
```
6.  Copy the shell scripts to the nodes you're **NOT** on

```
scp *.sh $CRDBNODE1:.
```
7.  Run `prep_update.sh` on **all** nodes  
```
ssh $CRDBNODE1 'bash -lc "~/prep_update.sh"'
```
8.  Run `apply_update.sh` on all nodes **EXCEPT** the last one!
```
ssh -t "$CRDBNODE1" 'bash -lic "source ~/.bashrc; source $HOME/apply_update.sh"'
```
9.  Start 3 Instances of the App Server

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

