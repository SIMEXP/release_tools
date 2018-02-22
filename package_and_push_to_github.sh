#!/bin/bash
# put a niak image into a tarball with its config file a psom_console.sh


usage (){

echo 
echo "usage: ${0} <singulatity_image>"
echo 
echo "   -p        Push the singularity tar ball to niak github"

}



while getopts "p" opt; do
  case $opt in
    p)
      PUSH_TO_GIT_HUB=1
      ;;
   \?)
      usage
      exit 1
      ;;
  esac
done


shift $(expr ${OPTIND} - 1 )
if [[ $# < 1 || $# > 2 ]] ; then

  usage
  exit 1
fi


SING_IMAGE=$1

if [ ! -f ${SING_IMAGE}  ] ; then
  echo ${SING_IMAGE} not found
fi

rm -r niak_singularity
cp -r  ./niak_singularity_template niak_singularity
mv ${SING_IMAGE} niak_singularity/.

filename=niak_singularity.tgz


tar -zcvf $filename niak_singularity 

tag=$(echo ${SING_IMAGE} | sed "s/.*-\([0-9].[0-9].[0-9]\)\.img/\1/")
owner=simexp
repo=niak

id=$(curl https://api.github.com/repos/simexp/niak/releases  | python3 -c "import sys, json; a = (json.load(sys.stdin));print( [i['id'] for i in a if i['tag_name'] == 'v${tag}'][0])")

# Construct url
GH_ASSET="https://uploads.github.com/repos/$owner/$repo/releases/$id/assets?name=${filename}"

curl -v  --data-binary @"$filename" -H "Authorization: token $GIT_TOKEN" -H "Content-Type: application/octet-stream" $GH_ASSET


