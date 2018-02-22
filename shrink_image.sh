#!/bin/bash


usage (){

echo 
echo "usage: $0 <image_to_shrink>"
echo 
echo "shrink singularity image to minimal size" 
 
}

if [[ "$#" -ne 1 || "$1" = "-h" ]]; then 
  usage
  exit 1
fi


image=$1
stripped_img=`tempfile --directory=.`
tail -n +2 $image > $stripped_img
e2fsck -f $stripped_img
resize2fs -M $stripped_img
shrunk_img=`tempfile --directory=.`
head -n 1 $image > $shrunk_img
cat $stripped_img >> $shrunk_img
rm $stripped_img
mv $shrunk_img $image
chmod a+x $image

