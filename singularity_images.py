import os
cmd = "singularity pull docker://fjukstad/trimmomatic"
os.system(cmd)
cmd = "singularity pull docker://mcfonsecalab/qcat"
os.system(cmd)
cmd = "singularity pull docker://nanozoo/nanoplot:1.32.0--1ae6f5d"
os.system(cmd)
cmd = "singularity pull docker://nanozoo/fastqc"
os.system(cmd)
cmd = "singularity pull docker://mcfonsecalab/nanofilt"
os.system(cmd)
cmd = "singularity pull docker://flowcraft/kraken:1.0-0.1"
os.system(cmd)
cmd = "singularity pull docker://nanozoo/unicycler:0.4.7-0--c0404e6"
os.system(cmd)
cmd = "singularity pull docker://replikation/abricate"
os.system(cmd)
