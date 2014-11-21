#!/bin/bash

###
### Run this script with:
###
###   run.sh
###
#$ -S /bin/bash
#$ -q all.q@master

# Set up cluster-specific variables
PARAVIEW_DIR="/opt/paraview/install"
PV_PYTHON="${PARAVIEW_DIR}/bin/pvpython"
APPS_DIR="lib/paraview-4.2/site-packages/paraview/web"
VISUALIZER="${PARAVIEW_DIR}/${APPS_DIR}/pv_web_visualizer.py"
#PROXIES="/opt/paraview/defaultProxies.json"
RC_PORT="54321"
REVERSE="--reverse-connect-port ${RC_PORT}"

# Run in MPI mode
MPIPROG="${PARAVIEW_DIR}/lib/paraview-4.2/mpiexec"
PV_SERVER="${PARAVIEW_DIR}/bin/pvserver"

# Get the private ip of this host
IPADDRESS=`curl -s http://169.254.169.254/latest/meta-data/local-ipv4`

# Create proxy entry
BODY='{"host": "'$IPADDRESS'", "clusterId": "{{ cluster._id }}", "port": 8080, "jobId": "{{ job._id }}"}'
curl -X POST -d "$BODY"  --header "Content-Type: application/json" {{ base_url }}/proxy

export LD_LIBRARY_PATH=$PARAVIEW_DIR/lib/paraview-4.2

# First run pvpython with the reverse connect port
${PV_PYTHON} ${VISUALIZER} --host $IPADDRESS --port 8080

# Remove proxy entry
curl -X DELETE {{ base_url }}/proxy/{{ cluster._id }}/{{ job._id }}
