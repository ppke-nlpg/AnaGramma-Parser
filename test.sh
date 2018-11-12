#!/bin/bash

for i in `seq 0 12`  # 43 -ig van
do
    echo "Testing ${i}"
    python3 main.py --test ${i} > temp.out 2> temp.err
    if [ $? -ne 0 ]; then
        cat temp.err 1>&2
        exit 1
    fi
    if [ $? -ne 0 ]; then
        exit 1
    fi
    grep "ÉL KÉSZÜLT" temp.out > temp_filt.out
    echo "cat temp_filt.out"
    diff -ys --suppress-common-lines temp_filt.out test_output/${i}_ref.txt
    if [ $? -ne 0 ]; then
        exit 1
    fi
    egrep -v "^(searcher|feature) " temp.err > temp_filt.err
    echo "cat temp.err"
    diff -ys --suppress-common-lines temp_filt.err test_output/${i}_vis.txt
    if [ $? -ne 0 ]; then
        exit 1
    fi
done
echo "OK!"
