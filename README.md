This is a library includes the SIMEXP lab release tools.

I also includes a simple git wrapper called `simplegit.py`.
That is both simple and intuitive.

It is a python3 project.

+++++++++++++++++++++++++++++++++++++

There is a couple value to set in the `niakrelease/config.py` file before doing
a release.

The *Repo* class:

Set __SANDBOX__ and __DEBUG_SANDBOX__ to empty path on your computer.

Set  __GIT_REPO__ to "simexp", it is the github account where you will do the
 releases.

Set  __DEBUG_GIT_REPO__  to a debug repo ( e.g. you home git page) where you will be
 able to check if all is ok. Just fork the most recent NIAK in that repo.

In the *PSOM* class
Set the PSOM version used to compute the target.


Before being able to do a release on github, you need to get a git token
https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/
you can put that tocken in your .profile to make sure that it is in the release
tool environment before you run it.



### Relese a new target

Note that you can always run these comand with the --debug option, so it push
the release on a secondary testing git repo, no SIMEXP/NIAK.


Take the tip of the master branch (let say the commit hash is fffffff) to release the
target. The arget are all named `target_test_niak_mnc1-XX` the suffix `--target_suffix`
option replace the XX. For the current taget is target_test_niak_mnc1-aj. This
mean that the next one would be `ak`

```
./release_new_target.py -r  --from_branch master  --target_suffix ak fffffff
```

Note that the short and long form commit hash are accepted

```
commit_hash = "a97d465841d910bdb1043066976de9207970e74d"  # IS OK
commit_hash = "a97d465"  # IS OK TOO

```

### Release a new NIAK  

Take the tip of the master branch (let say the commit hash is fffffff) release a
new NIAK version to the `niak-cog` branch with version 1.9.9.

```
./release_new_target.py -r  --from_branch master --to_branch niak-cog  --niak_version v1.9.9  fffffff
```

### Release a new NIAK and a new target

Do both the target and NIAK release.

```
./release_new_target.py -r  --from_branch master --to_branch niak-cog  --target_suffix ak --niak_version v1.9.9  fffffff
```


Also note that new target can only be released from the tip of a branch
(typically master), while NIAK can be release from any commit in your
repo, without the --from_branch option.

## Deploy
Niak is deployed with Singularity containers. But it is typically easier to
build an docker image and then translate it to singularity.

You can alway go in the niak repo and run the following after having checked out
the tag created in the release phase.

```
cd path_to/niak
git checkout v1.9.9
docker build --tag simexp/niak-cog:1.9.9 .
```

This will create a docker image of the checkout NIAK version.

From there, you can use the `create_singularity_from_docker.sh` script
in the release tool repo to create a singularity image.

```
./create_singularity_from_docker.sh simexp/niak-cog:1.9.9

```
Note that you need sudo to be able to create singularity images.

This will have created a `simexp_niak-cog-:1.9.9.img` file on your system.

you can then  shrink_image.sh the image so it is as small as possible and then
push it to cedar:

```
shrink_image.sh my-release.img
push_image_to_cedar.sh simexp_niak-cog-:1.9.9.img <cedar_login>
```

There is also a tool to push the release on github:

```
package_and_push_to_github.sh simexp_niak-cog-:1.9.9.img
```
