#!/bin/bash



usage (){

echo 
echo "usage:  $0 <image_to_push> <ssh uid>"
echo 
 
}

if [[ "$#" -ne 2 ]]; then 
  usage
  exit 1
fi

rsync -avz --chmod=644 --progress $1 $2@cedar.computecanada.ca:/project/6003287/NIAK/.
