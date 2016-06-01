This is a library includes the SIMEXP lab release tools.

For now, it only contains the NIAK release tool.

I also includes a simple git wrapper `simplegit.py`. That is both simple and
intuitive.

It is a python3 project.

To use the tool, edit the `config.py` file, the two value that
 have to be updated for every a full release are
```python
TARGET.TAG_NAME  = "X.X.X"
NIAK.TAG_NAME  = "vX.X.X"
```
 You might also want to have a look at  
```python
PSOM.RELEASE_TAG  = X.X.X # The version of psom used to compute the target
```

 Then, release a target only :
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

One other useful option is `-f`. Let say you have release a NIAK version
with tag v0.0.0, and there is an error in it. If you want to 
overwite the release with the same tag name, just do:

```bash
./release_new_target.py -n -f
```

Also note that new target can only be released from the tip of a branch
(typically master), while NIAK can be release from any commit in your
repo using the `NIAK.RELEASE_FROM_COMMIT` option and giving it the value of the 
long frm git hash:
```python
NIAK.RELEASE_FROM_COMMIT = "a97d465841d910bdb1043066976de9207970e74d"  # IS OK
NIAK.RELEASE_FROM_COMMIT = "a97d465"  # IS NOT OK

```
