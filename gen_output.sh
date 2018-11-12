#!/bin/bash

for i in `seq 13 43`  # 43 -ig van
do
    echo "Testing ${i}"
    python3 main.py --test ${i} > temp_${i}.out 2> temp_${i}.err
    if [ $? -ne 0 ]; then
        cat temp_${i}.err 1>&2
#        exit 1
    fi
#    if [ $? -ne 0 ]; then
#        exit 1
#    fi
    grep "ÉL KÉSZÜLT" temp_${i}.out > temp_${i}_filt.out
    echo "cat temp_${i}_filt.out"
#    diff -ys --suppress-common-lines temp_filt.out test_output/${i}_ref.txt
#    if [ $? -ne 0 ]; then
#        exit 1
#    fi
    egrep -v "^(searcher|feature) " temp_${i}.err > temp_${i}_filt.err
    echo "cat temp_${i}.err"
#    diff -ys --suppress-common-lines temp_filt.err test_output/${i}_vis.txt
#    if [ $? -ne 0 ]; then
#        exit 1
#    fi
done
echo "OK!"
