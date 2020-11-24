# FullForcePlasmidAssembler
Make sure any version of python3 is running on your system.
##### SETTING UP A NEW UNBUNTO BASED CLOUD SERVER #############
-Create ubuntu instance with plenty of space and mem.
-install docker (This is an installation for linux system, but other installations can be found at https://docs.docker.com/get-docker/)
```bash
$ curl -fsSL https://get.docker.com -o get-docker.sh
$ sh get-docker.sh
$ sudo usermod -a -G docker $USER
```
Now, close terminal and reopen to activate doc ker installation.

## Git clone

```bash
$ git clone https://github.com/MBHallgren/FullForcePlasmidAssembler.git
```

## Automatic installation of docker images:
```bash
$ python3 images.py
```

## Pipeline

FullForcePlasmidAssembler uses Trimmomatic and QCAT for tirmming illumina and nanopore data, respectively.
FastQC and Nanoplots are used to quality check the trimmed reads.
Kraken reports are generated from the reads, and then Unicycler is used to perform a hybrid assembly.
Finally, Abcricate with plasmidfinder_db and resfinder_db is run.

## Docker images used are:

fjukstad/trimmomatic  
mcfonsecalab/qcat  
nanozoo/nanoplot:1.32.0--1ae6f5d  
nanozoo/fastqc  
mcfonsecalab/nanofilt  
flowcraft/kraken:1.0-0.1  
nanozoo/unicycler:0.4.7-0--c0404e6  
replikation/abricate  

