# DTN_Project
Workspace for the DTN(Digital Network Twin) Project

Modified the code for adding the Match field nodes and the Instruction nodes. The entire code for writing the flow data to Neo4j is wriiten in DTNManager.py file.
The respective function codes for intercating with the SDN controller is in dtninter which is an interface, which can be imported into the DTNManager for using 
different functions. Currently the interface contains code for extracting flowrules (Flowrules.py) which uses REST API to get the flow rule information from the
Controller.
