#!/usr/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <pipreqs_output_file>"
    exit 1
fi
while IFS='==' read -r pkg version; do
    ## Find packages in requirements
    if grep -qi "^${pkg}==" requirements.txt; then
        ## Update the given package number based on pipreqs.txt
        sed -i "s/^${pkg}==.*/${pkg}==${version}/" requirements.txt
    else
        ## Append newly found packages
        echo -e "${pkg}==${version}" >> requirements.txt
    fi
done < $1 ## $1: argument for temporary pipreqs file generated
