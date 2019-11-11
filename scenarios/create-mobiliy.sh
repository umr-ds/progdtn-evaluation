#!/usr/bin/env bash

set -e

# use env parameters to generate traces using bonnmotion
function autobonn(){
    mkdir -p `dirname $name`

    # generate trace
    bm -f $name $model \
        -i $ignore -R $randomSeed -x $x -y $y -d $duration -n $nn -c $circular -J $J\
        -w $noOfWaypoints -p $minpause -P $maxpause -b $beta -h $hurst -l $dist_weight -r $cluster_range -Q$cluster_ratio -W$waypoint_ratio

    # generate ns-2 movement files
    bm NSFile -f $name
    
    # replace node 0 by node number (CORE nodes are 1-indexed)
    sed -i "s/node_(0)/node_($nn)/g" $name.ns_movements
}

# base configuration
ignore=3600.0       # skip 1 hour of model
randomSeed=0        # initialize with 1
x=1500.0            # 1500 meters long
y=300.0             # 300 meters high
duration=7200.0     # 2 hours total runtime
nn=100              # 100 nodes
circular=false      
J=2D


# SLAW
## many features derived from the SLAW model: [1] "Steady-State of The SLAW Mobility Model"
name=`dirname $0`/slaw/$randomSeed
model=SLAW
noOfWaypoints=400   # waypoints, derived from 20m Wi-Fi Range in 1000x1000 meter area
minpause=30.0       # 30 seconds minimum pause [1]
maxpause=36000.0    # seconds maximum pause [1]
beta=1.5            # Pause Distribution seconds minimum pause [1]
hurst=0.75          # hurst, "custer-density", how "clustery" are the waypoints
dist_weight=3.0     # alpha, [1], move to non-optimal waypoints from time to time
cluster_range=50.0  # meters clustering range (size of a building)
cluster_ratio=20    # a node visiits 20% of the clusters
waypoint_ratio=20   # 20% of the waypoints in a cluster are visited

autobonn
