#! /bin/bash

stats="Nodes-uarch-Commits:NonSpin:User Nodes-uarch-InsnCount:User:Load Nodes-uarch-InsnCount:User:Store  Nodes-L1d-EvictsWithData Nodes-L1d-Fills Nodes-uarch-CoalescedStores Nodes-batch-unroller0-dest-addressed-access Nodes-batch-unroller0-normal Nodes-fag-branches:cond"

for stat in $stats; do
    grep $stat stats.raw
done
