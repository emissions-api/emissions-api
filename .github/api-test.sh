#!/bin/bash

set -e
set -u

api_call () {
    cmd="curl --silent --fail -X GET \"accept: application/json\" http://localhost:8000/api/v2/$1"
    >&2 echo "Calling '$cmd'"
    $cmd
}

PRODUCTS=$(api_call products.json | jq ".[].name" | tr -d \")
for product in $PRODUCTS
do
    first=$(api_call "$product/data-range.json" | jq .first)
    last=$(api_call "$product/data-range.json" | jq .last)

    for endpoint in average.json geo.json statistics.json
    do
        api_call "$product/$endpoint" | jq > /dev/null
        api_call "$product/$endpoint?limit=10" | jq > /dev/null
        api_call "$product/$endpoint?offset=10" | jq > /dev/null
        api_call "$product/$endpoint?begin=$first&end=$last" | jq > /dev/null
        for area in 'country=DE' \
            'polygon=30&polygon=10&polygon=40&polygon=40&polygon=20&polygon=40&polygon=10&polygon=20&polygon=30&polygon=10' \
            'geoframe=30&geoframe=10&geoframe=40&geoframe=40' \
            'point=30,10'
        do
            api_call "$product/$endpoint?$area" | jq > /dev/null
        done
    done
done

# Test contry codes
api_call countries.json \
    | jq -r .DE \
    | grep -i Germany
