This is a library includes the SIMEXP lab release tools.

For now, it only contains the NIAK release tool.

I also includes a simple git wrapper `simplegit.py`. That is both simple and
intuitive.

It is a python3 project.

To use the tool, fist edit the `config.py` file, the two value that
 have to be updated for every a full release are
```python
TARGET.TAG_NAME  # typcally in the X.X.X format
NIAK.TAG_NAME  # typcally in the vX.X.X format
```
 You might also want to have a look at  
```python
PSOM.RELEASE_TAG  # The version of psom use to compute the target
```

 Then to do to release a target only :
 ```bash
cd bin
./release_new_target.py -r
 ```

 To release a new version of NIAK:
```bash
./release_new_target.py -r
```
To do both all at once

```bash
./release_new_target.py -r -n
```

One other useful option is `-f`. Let say that you have release an NIAK version
with the v0.0.0 tag, but that there is an error in it. If you want to be able
to overwite that release with the same tag name, just do:

```bash
./release_new_target.py -n -f
```

Also note that new target can only be released from the tip of a branch
(typically master), while NIAK version can be release from any commit in your
repo using the `NIAK.RELEASE_FROM_COMMIT` option and giving it the long
version of a git hash:
```python
NIAK.RELEASE_FROM_COMMIT = "a97d465841d910bdb1043066976de9207970e74d"  # IS OK
NIAK.RELEASE_FROM_COMMIT = "a97d465"  # IS NOT OK

```
