#! /bin/bash

pre='run/'
post='/timing/phase_001/flexpoint_000/'

folders='nmp_base_4core_4MB_join nmp_base_4core_4MB_join_pp nmp_base_4core_4MB_join_dramsim nmp_base_4core_4MB_join_pp_dramsim'

for folder in $folders; do
    pushd "$pre$folder$post" > /dev/null
    echo $folder
    ../../../../../grep_stats.sh
    echo
    popd > /dev/null
done

