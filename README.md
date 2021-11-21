# DTN_Project
Workspace for the DTN(Digital Network Twin) Project

Modified the code for adding the Match field nodes and the Instruction nodes. The entire code for writing the flow data to Neo4j is wriiten in DTNManager.py file.
The respective function codes for intercating with the SDN controller is in dtninter which is an interface, which can be imported into the DTNManager for using 
different functions. Currently the interface contains code for extracting flowrules (Flowrules.py) which uses REST API to get the flow rule information from the
Controller.


**Neo4j** : https://neo4j.com/

**Documentations**
Neo4j Python Driver Manual v4.3 :
PDF -> https://neo4j.com/docs/pdf/neo4j-driver-manual-4.3-python.pdf
HTML -> https://neo4j.com/docs/python-manual/current/

Neo4j Cypher (Query Language) : 
PDF-> https://neo4j.com/docs/pdf/neo4j-cypher-manual-4.3.pdf
HTML -> https://neo4j.com/docs/cypher-manual/current/

Neo4j Python API :
https://neo4j.com/docs/api/python-driver/current/api.html#api-documentation

**All Documentations**
https://neo4j.com/docs/

<br>
<br>

**Installing Neo4j**:
<br>
1.Goto https://neo4j.com/  , and download the Neo4j desktop.

2.On the next page, fill out the form by giving the details (Name, Email etc)

3.Neo4j will be downloaded, copy the activation key from the page given.

4.Now for linux, goto the downloaded location and run chmod +x FILE_NAME (File name of downloaded file)

5.Now double click the file to launch installation, then paste the key copied earlier and click activate.

6.Wait till Neo4j installs.

7.Neo4j is installed.

**Setting Up Neo4j**:
1.We can create a new database graph called **“dtn_kg”** to which we will add the nodes according to the KG schema decided as we extract the information from the SDN.

2. Create a new database **"dtn_kg"**, create a new schema inside it called **"dtnkg"**.

3.Create a user with admin and public roles with username:"dtn_user" and password:"password"

2.DTN manager will be responsible for getting the information and building the KG, Updating and deleting the KG.


