import sys
import os
import argparse
import subprocess
import random
import time

parser = argparse.ArgumentParser(description='.')
parser.add_argument('-i_trimmed_illumina', action="store", nargs="+", type=str, dest='i_trimmed_illumina', default="", help='Input for trimmed iilumina reads. If PE, give 2 input files seperated by a space. Please use the complete path to the given file')
parser.add_argument('-i_raw_illumina', action="store", nargs="+", type=str, dest='i_raw_illumina', default="", help='Input for untrimmed iilumina reads. If PE, give 2 input files seperated by a space. Please use the complete path to the given file')
parser.add_argument('-i_trimmed_nanopore', action="store", type=str, dest='i_trimmed_nanopore', default="", help='Input for trimmed Nanopore reads. Please use the complete path to the given file')
parser.add_argument('-i_raw_nanopore', action="store", type=str, dest='i_raw_nanopore', default="", help='Input for untrimmed Nanopore reads. Please use the complete path to the given file')
parser.add_argument('-trimmomatic_db', action="store", type=str, dest='trimmomatic_db', default="TruSeq3", help='Use either \"TruSeq3\" or \"Nextera\" as db.')
parser.add_argument('-qscore', action="store", type=str, dest='qscore', default="7", help='qscore for nanopore filtering')
parser.add_argument("-o", action="store", dest="output_name", help="Name that you would like the output directory to be called.")
args = parser.parse_args()


jobid = random.randint(1,100000)

#Name init
nanopore_name = ""
illumina_name = ""
illumina_name1 = ""
illumina_name2 = ""

if args.i_trimmed_nanopore == "" and args.i_raw_nanopore == "":
    sys.exit("No nanopore input given.")

#Function to handle fastq and gz inputs differently

#Get current directory
current_path = os.getcwd()
target_dir = current_path + "/" + args.output_name + "/"
cmd = "mkdir {}".format(target_dir)
os.system(cmd)
cmd = "mkdir {}tmp/".format(target_dir)
os.system(cmd)
cmd = "mkdir {}output/".format(target_dir)
os.system(cmd)

paired_end = False

#File handling of different illumina input options
if len(args.i_raw_illumina) == 2:
    paired_end = True
    illumina_name1 = args.i_raw_illumina[0].split('/')[-1]
    illumina_name2 = args.i_raw_illumina[1].split('/')[-1]
elif len(args.i_trimmed_illumina) == 2:
    paired_end = True
    illumina_name1 = args.i_trimmed_illumina[0].split('/')[-1]
    illumina_name2 = args.i_trimmed_illumina[1].split('/')[-1]
else:
    paired_end = False
    if args.i_raw_illumina != "":
        illumina_name = args.i_raw_illumina
    else:
        illumina_name = args.i_trimmed_illumina

trimmomatic_db = ""
#Initialize trimmomatic db
#Trimmomatic DB:
if args.trimmomatic_db == "TruSeq3":
    if paired_end:
        trimmomatic_db = "/tools/trimmomatic/adapters/TruSeq3-PE.fa"
    else:
        trimmomatic_db = "/tools/trimmomatic/adapters/TruSeq3-SE.fa"
elif args.trimmomatic_db == "Nextera":
    trimmomatic_db = "/tools/trimmomatic/adapters/NexteraPE-PE.fa"
else:
    sys.exit("An incorrect trimmomatic db was given. Please see the help function for the correct options")

#If paired end, load input into single folder to mount volume to docker container
if paired_end == True:
    if args.i_raw_illumina != "":
        cmd = "mkdir {}tmp/illuminaPE/".format(target_dir)
        os.system(cmd)
        cmd = "cp {} {}tmp/illuminaPE/.".format(args.i_raw_illumina[0], target_dir)
        os.system(cmd)
        cmd = "cp {} {}tmp/illuminaPE/.".format( args.i_raw_illumina[1], target_dir)
        os.system(cmd)
    elif args.i_trimmed_illumina != "":
        cmd = "mkdir {}tmp/illuminaPE/".format(target_dir)
        os.system(cmd)
        cmd = "cp {} {}tmp/illuminaPE/.".format(args.i_trimmed_illumina[0], target_dir)
        os.system(cmd)
        cmd = "cp {} {}tmp/illuminaPE/.".format(args.i_trimmed_illumina[1], target_dir)
        os.system(cmd)

#Handle nanopore input
if args.i_trimmed_nanopore != "":
    nanopore_name = args.i_trimmed_nanopore.split('/')[-1]
elif args.i_raw_nanopore != "":
    nanopore_name = args.i_raw_nanopore.split('/')[-1]

#Unzip nanoporereads, since qcat etc. cant handle .gz
cmd = "gunzip -c {} > {}/tmp/{}.fastq".format(args.i_raw_nanopore, target_dir, nanopore_name)
os.system(cmd)


if args.i_raw_illumina != "":
    if paired_end == True:
        #docker run -it -v /home/mbhallgren96/data/illumina/:/tmp/illuminaPE/ dceoy/trimmomatic trimmomatic PE -phred33 /tmp/illuminaPE/CPO20180119_S35_L555_R1_001.fastq.gz /tmp/illuminaPE/CPO20180119_S35_L555_R2_001.fastq.gz /tmp/f_paired /tmp/f_unpaired /tmp/r_unpaired /tmp/r_paired ILLUMINACLIP:/tools/trimmomatic/adapters/NexteraPE-PE.fa:2:30:10 LEADING:20 TRAILING:20 MINLEN:140
        cmd = "docker run -it -v {}tmp/illuminaPE/:/tmp/illuminaPE/ --name trimmomatic_container{} fjukstad/trimmomatic PE /tmp/illuminaPE/{} /tmp/illuminaPE/{} /tmp/output_forward_paired.fq.gz /tmp/output_forward_unpaired.fq.gz /tmp/output_reverse_paired.fq.gz /tmp/output_reverse_unpaired.fq.gz ILLUMINACLIP:{}:2:30:10 LEADING:20 TRAILING:20 MINLEN:140".format(target_dir, jobid, illumina_name1, illumina_name2, trimmomatic_db)
        os.system(cmd)


        proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("trimmomatic_container", jobid), shell=True, stdout=subprocess.PIPE, )
        output = proc.communicate()[0]
        id = output.decode().rstrip()

        cmd = "mkdir {}tmp/illuminaPE_trimmed/".format(target_dir)
        os.system(cmd)

        cmd = "docker cp {}:/tmp/output_forward_paired.fq.gz {}tmp/illuminaPE_trimmed/{}".format(id, target_dir, illumina_name1)
        os.system(cmd)
        cmd = "docker cp {}:/tmp/output_reverse_paired.fq.gz {}tmp/illuminaPE_trimmed/{}".format(id, target_dir, illumina_name2)
        os.system(cmd)

        cmd = "docker container rm {}".format(id)
        os.system(cmd)

        cmd = "rm -r {}/tmp/illuminaPE".format(target_dir)
        os.system(cmd)

        cmd = "gunzip -c {}/tmp/illuminaPE_trimmed/{} > {}/tmp/illuminaPE_trimmed/{}".format(target_dir, illumina_name1, target_dir, illumina_name1[:-3])
        os.system(cmd)
        cmd = "gunzip -c {}/tmp/illuminaPE_trimmed/{} > {}/tmp/illuminaPE_trimmed/{}".format(target_dir, illumina_name2, target_dir, illumina_name2[:-3])
        os.system(cmd)

    else:
        cmd = "docker run -it -v {}:/tmp/illuminaSE/ --name trimmomatic_container{} dceoy/trimmomatic SE /tmp/illuminaSE/{} /tmp/output ILLUMINACLIP:{}:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36".format(target_dir, jobid, illumina_name, trimmomatic_db)
        os.system(cmd)

        cmd = "docker cp {}:/tmp/output {}/tmp/{}".format(id, target_dir, illumina_name)
        os.system(cmd)

        cmd = "docker container rm {}".format(id)
        os.system(cmd)

if args.i_raw_nanopore != "":
    print ("Qcat is running, be patient :) ")
    cmd = "docker run -it -v {}/tmp/{}.fastq:/tmp/{}.fastq --name qcat_container{} mcfonsecalab/qcat qcat -f /tmp/{}.fastq -o /tmp/{}_trimmed.fastq".format(target_dir,nanopore_name, nanopore_name, jobid, nanopore_name, nanopore_name)
    os.system(cmd)
    print("qcat complete") ########### MISSING
    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("qcat_container", jobid), shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    cmd = "docker cp {}:/tmp/{}_trimmed.fastq {}/tmp/.".format(id, nanopore_name, target_dir)
    os.system(cmd)

    #Remove container after download
    cmd = "docker container rm {}".format(id)
    os.system(cmd)

    trimmed_nanopore = "{}_trimmed.fastq".format(nanopore_name)
else:
    trimmed_nanopore = nanopore_name

#Nanopore pipeline
cmd = "docker run --name nanofilt_q{}  -it -v {}/tmp/{}:/tmp/input/{} mcfonsecalab/nanofilt NanoFilt -q {} /tmp/input/{} | gzip > {}/tmp/{}.q{}_nanofilt".format(jobid, target_dir, trimmed_nanopore, trimmed_nanopore, args.qscore, trimmed_nanopore, target_dir, nanopore_name, args.qscore)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("nanofilt_q", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker container rm {}".format(id)
os.system(cmd)

print ("nanofilt q complete")


cmd = "docker run --name nanofilt_10k{} -it -v {}/tmp/{}:/tmp/input/{} mcfonsecalab/nanofilt NanoFilt -l 10000 /tmp/input/{} | gzip > {}/tmp/{}.10000.nanofilt".format(jobid, target_dir, trimmed_nanopore, trimmed_nanopore, trimmed_nanopore, target_dir, nanopore_name)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("nanofilt_10k", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker container rm {}".format(id)
os.system(cmd)

print ("nanofilt l 10000 complete")
q_reads = "{}.q{}_nanofilt".format(nanopore_name, args.qscore)
"""
#Filtlong
cmd = "docker run --name filtlong_500mbp -it -v {}/tmp/{}:/tmp/input/{} nanozoo/filtlong filtlong --target_bases 500000000 /tmp/input/{} > {}/tmp/{}.mbp500.fastq".format(target_dir, q_reads, q_reads, q_reads, target_dir, nanopore_name)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}\"".format("filtlong_500mbp"), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker container rm {}".format(id)
os.system(cmd)

sys.exit("filtlong done")


mbp500_reads = "{}.mbp500.fastq".format(nanopore_name)
"""
#Kraken Nanopore
cmd = "docker run --name kraken_container{}  -it -v {}/tmp/{}:/tmp/input/{} flowcraft/kraken:1.0-0.1 kraken --db /kraken_db/minikraken_20171013_4GB --output /tmp/krakenoutput_nanopore /tmp/input/{}".format(jobid, target_dir, q_reads, q_reads, q_reads)
os.system(cmd)


proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("kraken_container", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker cp {}:/tmp/krakenoutput_nanopore {}/tmp/.".format(id, target_dir)
os.system(cmd)

cmd = "docker container rm {}".format(id)
os.system(cmd)


print ("kraken finished nanopore q")

#Kraken report Nanopore
cmd = "docker run --name kraken_report{} -it -v {}tmp/krakenoutput_nanopore:/tmp/krakenoutput_nanopore flowcraft/kraken:1.0-0.1 kraken-report --db /kraken_db/minikraken_20171013_4GB /tmp/krakenoutput_nanopore > {}tmp/kraken_report_nanopore".format(jobid, target_dir, target_dir)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("kraken_report", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker container rm {}".format(id)
os.system(cmd)

cmd = "awk \'{if ($1>1) {print}}\' " + target_dir + "tmp/kraken_report_nanopore > " + target_dir + "tmp/kraken_report_nanopore_1percenthits"
os.system(cmd)

#Kraken on Illumina
if paired_end == True:
    #NOT WORKING, no outputfile
    print (illumina_name1)
    print (illumina_name2)
    cmd = "docker run --name kraken_container{} -it -v {}tmp/illuminaPE_trimmed/:/tmp/input/ flowcraft/kraken:1.0-0.1 kraken --db /kraken_db/minikraken_20171013_4GB --output /tmp/krakenoutput_illumina /tmp/input/{} /tmp/input/{}".format(jobid, target_dir, illumina_name1, illumina_name2)
    print (cmd)
    os.system(cmd)

    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("kraken_container", jobid), shell=True,
                            stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    cmd = "docker cp {}:/tmp/krakenoutput_illumina {}/tmp/.".format(id, target_dir)
    os.system(cmd)

    cmd = "docker container rm {}".format(id)
    os.system(cmd)

    print("kraken finished illumina PE")

    # Kraken report Illumina PE
    cmd = "docker run --name kraken_report{} -it -v {}tmp/krakenoutput_illumina:/tmp/krakenoutput_illumina flowcraft/kraken:1.0-0.1 kraken-report --db /kraken_db/minikraken_20171013_4GB /tmp/krakenoutput_illumina > {}tmp/kraken_report_illumina".format(jobid, target_dir, target_dir)
    os.system(cmd)

    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("kraken_report", jobid), shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    cmd = "docker container rm {}".format(id)
    os.system(cmd)

    cmd = "awk \'{if ($1>1) {print}}\' " + target_dir + "tmp/kraken_report_illumina > " + target_dir + "tmp/kraken_report_illumina_1percenthits"
    os.system(cmd)
else:
    cmd = "docker run --name kraken_container{} -it -v {}tmp/{}:/tmp/input/{} flowcraft/kraken:1.0-0.1 kraken --db /kraken_db/minikraken_20171013_4GB --output /tmp/krakenoutput_illumina /tmp/input/{}".format(jobid, target_dir, illumina_name, illumina_name, illumina_name)
    os.system(cmd)

    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("kraken_container", jobid), shell=True,
                            stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    cmd = "docker cp {}:/tmp/krakenoutput_illumina {}/tmp/.".format(id, target_dir)
    os.system(cmd)

    cmd = "docker container rm {}".format(id)
    os.system(cmd)

    print("kraken finished illumina SE")

    # Kraken report illumina se
    cmd = "docker run --name kraken_report{} -it -v {}/tmp/krakenoutput_illumina:/tmp/krakenoutput_illumina flowcraft/kraken:1.0-0.1 kraken-report --db /kraken_db/minikraken_20171013_4GB /tmp/krakenoutput_illumina > {}tmp/kraken_report_illumina".format(jobid, target_dir, target_dir)
    os.system(cmd)

    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("kraken_report", jobid), shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    cmd = "docker container rm {}".format(id)
    os.system(cmd)

    cmd = "awk \'{if ($1>1) {print}}\' " + target_dir + "tmp/kraken_report_illumina > " + target_dir + "tmp/kraken_report_illumina_1percenthits"
    os.system(cmd)


#HERE
#Unicycler nanopore

cmd = "docker run --name assembly_qreads{} -it -v {}/tmp/{}:/tmp/input/{} nanozoo/unicycler unicycler -l /tmp/input/{} -o /tmp/nanopore_assembly".format(jobid, target_dir, q_reads, q_reads, q_reads)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("assembly_qreads", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker cp {}:/tmp/nanopore_assembly {}/tmp/.".format(id, target_dir)
os.system(cmd)

cmd = "docker container rm {}".format(id)
os.system(cmd)


#Unicycler hybrid

if args.i_trimmed_illumina != "" or args.i_raw_illumina != "":
    if paired_end == True:

        cmd = "mkdir {}tmp/hybridinput/".format(target_dir)
        os.system(cmd)

        cmd = "cp {}/tmp/illuminaPE_trimmed/* {}/tmp/hybridinput/.".format(target_dir, target_dir)
        os.system(cmd)

        illumina_name1_o = args.i_raw_illumina[0].split('/')[-1]
        illumina_name2_o = args.i_raw_illumina[1].split('/')[-1]

        cmd = "mv {}/tmp/hybridinput/{} {}/tmp/hybridinput/{} ".format(target_dir, illumina_name1, target_dir, illumina_name1_o)
        os.system(cmd)

        cmd = "mv {}/tmp/hybridinput/{} {}/tmp/hybridinput/{} ".format(target_dir, illumina_name2, target_dir, illumina_name2_o)
        os.system(cmd)

        cmd = "cp {}/tmp/{} {}/tmp/hybridinput/.".format(target_dir, trimmed_nanopore, target_dir)
        os.system(cmd)

        cmd = "docker run --name hybrid_container{} -it -v {}/tmp/hybridinput/:/tmp/input/ nanozoo/unicycler unicycler -1 /tmp/input/{} -2 /tmp/input/{} -l /tmp/input/{} -o /tmp/hybrid_assembly".format(jobid, target_dir, illumina_name1_o, illumina_name2_o, trimmed_nanopore)
        os.system(cmd)

        proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("hybrid_container", jobid), shell=True,stdout=subprocess.PIPE, )
        output = proc.communicate()[0]
        id = output.decode().rstrip()

        cmd = "docker cp {}:/tmp/hybrid_assembly {}/tmp/.".format(id, target_dir)
        os.system(cmd)

        cmd = "docker container rm {}".format(id)
        os.system(cmd)
    else:
        cmd = "mkdir {}/tmp/hybridinput/".format(target_dir)
        os.system(cmd)

        cmd = "cp {}/tmp/{} {}/tmp/hybridinput/.".format(target_dir, illumina_name, target_dir)
        os.system(cmd)

        cmd = "cp {}/tmp/{} {}/tmp/hybridinput/.".format(target_dir, trimmed_nanopore, target_dir)
        os.system(cmd)

        illumina_name_o = args.i_raw_illumina.split('/')[-1]

        cmd = "mv {}/tmp/hybridinput/{} {}/tmp/hybridinput/{} ".format(target_dir, illumina_name, target_dir, illumina_name_o)
        os.system(cmd)

        cmd = "docker run --name hybrid_container{} -it -v {}/tmp/hybridinput/:/tmp/input/ nanozoo/unicycler unicycler -s /tmp/input/{} -l /tmp/input/{} -o /tmp/hybrid_assembly".format(jobid, target_dir, illumina_name_o, trimmed_nanopore)
        os.system(cmd)

        proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("hybrid_container", jobid), shell=True,stdout=subprocess.PIPE, )
        output = proc.communicate()[0]
        id = output.decode().rstrip()

        cmd = "docker cp {}:/tmp/hybrid_assembly {}/tmp/.".format(id, target_dir)
        os.system(cmd)

        cmd = "docker container rm {}".format(id)
        os.system(cmd)



#ABRRICATE HERE NOW





"""
#Unicycler nanopore mbp500

cmd = "docker run --name mbp500_container -it -v {}/tmp/{}:/tmp/input/{} nanozoo/unicycler unicycler -l /tmp/input/{} -o /tmp/mbp500_assembly".format(target_dir, mbp500_reads, mbp500_reads, mbp500_reads)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}\"".format("mbp500_container"), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker cp {}:/tmp/mbp500_assembly {}/tmp/.".format(id, target_dir)
os.system(cmd)
"""

cmd = "docker run --name nanopore_abricate_plasmid{} -it -v {}/tmp/nanopore_assembly/assembly.fasta:/tmp/assembly.fasta replikation/abricate --db plasmidfinder_db -i /tmp/assembly.fasta -o /tmp/output".format(jobid, target_dir)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("nanopore_abricate_plasmid", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker cp {}:/tmp/output {}/tmp/abricate_nanopore_plasmidfinder.".format(id, target_dir)
os.system(cmd)

cmd = "docker container rm {}".format(id)
os.system(cmd)

cmd = "docker run --name nanopore_abricate_res{} -it -v {}/tmp/nanopore_assembly/assembly.fasta:/tmp/assembly.fasta replikation/abricate --db resfinder_db -i /tmp/input/assembly.fasta -o /tmp/output".format(jobid, target_dir)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("nanopore_abricate_res", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker cp {}:/tmp/output {}/tmp/abricate_nanopore_resfinder.".format(id, target_dir)
os.system(cmd)

cmd = "docker container rm {}".format(id)
os.system(cmd)

if args.i_trimmed_illumina != "" or args.i_raw_illumina != "":

    cmd = "docker run --name hybrid_abricate_plasmid{} -it -v {}/tmp/hybrid_assembly/assembly.fasta:/tmp/assembly.fasta replikation/abricate --db plasmidfinder_db -i /tmp/assembly.fasta -o /tmp/output".format(jobid, target_dir)
    os.system(cmd)

    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("hybrid_abricate_plasmid", jobid), shell=True,
                            stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    cmd = "docker cp {}:/tmp/output {}/tmp/hybrid_abricate_plasmid.".format(id, target_dir)
    os.system(cmd)

    cmd = "docker container rm {}".format(id)
    os.system(cmd)

    cmd = "docker run --name hybrid_abricate_res{} -it -v {}/tmp/hybrid_assembly/assembly.fasta:/tmp/assembly.fasta replikation/abricate --db resfinder_db -i /tmp/assembly.fasta -o /tmp/output".format(jobid, target_dir)
    os.system(cmd)

    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("hybrid_abricate_res", jobid), shell=True,
                            stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    cmd = "docker cp {}:/tmp/output {}/tmp/hybrid_abricate_resfinder.".format(id, target_dir)
    os.system(cmd)

    cmd = "docker container rm {}".format(id)
    os.system(cmd)

sys.exit("Completed nanopore abricate")

"""

#ABRRICATE HERE NOW
#MAKE ABBRICATE

#Fail in filtlong, so unicyclertesting now possible
print ("Abricate")
#Abricate hybrid

#docker run --name hybrid_abricate -it -v {}/tmp/hybridinput/:/tmp/input/

"""

#UNICYCLER


# DATABSER
# DOWNLOAD ftp://ftp.neb.com/pub/rebase/dna_mini_reg_seqs.txt
# wget ftp://ftp.neb.com/pub/rebase/dna_mini_reg_seqs.txt
#VENT MED RM FINDER

#python3 au.py -i_raw_illumina /home/mbhallgren96/data/illumina/CPO20180119_S35_L555_R1_001.fastq.gz /home/mbhallgren96/data/illumina/CPO20180119_S35_L555_R2_001.fastq.gz -i_raw_nanopore /home/mbhallgren96/data/minion/CPO20180119.q7.fastq.gz -trimmomatic_db Nextera -o test1

#List to be done:

#min lenght flag
#Brug 10.000 long til nanopore only og q-reads til hybrid
#python3 /home/FFPA.py -i_raw_illumina /home/data/illumina/CPO20180119_S35_L555_R1_001.fastq.gz /home/data/illumina/CPO20180119_S35_L555_R2_001.fastq.gz -i_raw_nanopore /home/data/minion/CPO20180119.q7.fastq.gz -trimmomatic_db Nextera -o hybrid1
#python3 /home/FFPA.py -i_raw_illumina /home/data/illumina/CPO20180119_S35_L555_R1_001.fastq.gz /home/data/illumina/CPO20180119_S35_L555_R2_001.fastq.gz -i_raw_nanopore /home/data/minion/CPO20180119.q7.fastq.gz -trimmomatic_db Nextera -o test_outout
#Handle inputs correctly
#docker run -it -v /home/mbhallgren96/data/minion/CPO20180119.q7.fastq:/tmp/input/CPO20180119.q7.fastq mcfonsecalab/qcat qcat -f /tmp/input/CPO20180119.q7.fastq  -o /tmp/CPO20180119.q7.fastq
#Trimmomatic
#docker run -it -v /home/mbhallgren96/test_outout/tmp/hybridinput/:/tmp/input/ nanozoo/unicycler unicycler -s /tmp/input/CPO20180119_S35_L555_R1_001.fastq.gz_trimmed -l /tmp/input/CPO20180119.q7.fastq.gz_trimmed.fastq -o /tmp/hybrid_assembly
#Databases
#docker run -it -v /home/mbhallgren96/hybrid3/tmp/hybridinput/:/tmp/input/ flowcraft/kraken:1.0-0.1 kraken --db /kraken_db/minikraken_20171013_4GB --output /tmp/krakenoutput_illumina /tmp/input/CPO20180119_S35_L555_R1_001.fastq.gz /tmp/input/CPO20180119_S35_L555_R2_001.fastq.gz

#cmd = "docker run --name kraken_report -it -v {}/tmp/krakenoutput_illumina:/tmp/krakenoutput_illumina flowcraft/kraken:1.0-0.1 kraken-report --db /kraken_db/minikraken_20171013_4GB /tmp/krakenoutput_illumina > {}tmp/kraken_report_illumina".format(target_dir, target_dir)

#python3 /home/FFPA.py -i_raw_illumina  /home/data/illumina/CPO20180119_S35_L555_R1_001.fastq.gz /home/data/illumina/CPO20180119_S35_L555_R2_001.fastq.gz -i_raw_nanopore /home/data/minion/CPO20180119.q7.fastq.gz -trimmomatic_db Nextera -o final1
#FILTLONG OUTPUT ER IKKE FASTQ???????
#docker run -it -v /home/mbhallgren96/test1/tmp/illuminaPE_trimmed/:/tmp/illu/ flowcraft/kraken:1.0-0.1 kraken --db /kraken_db/minikraken_20171013_4GB --output /tmp/krakenoutput_illumina /tmp/illu/CPO20180119_S35_L555_R1_001.fastq.gz_trimmed /tmp/illu/CPO20180119_S35_L555_R2_001.fastq.gz_trimmed
#docker run --name mbp500_container -it -v /home/mbhallgren96/test1/tmp/CPO20180119.q7.fastq.gz.mbp500.fastq:/tmp/input/CPO20180119.q7.fastq.gz.mbp500.fastq nanozoo/unicycler unicycler -l /tmp/input/CPO20180119.q7.fastq.gz.mbp500.fastq -o /tmp/mbp500_assembly
#docker run  -it -v /home/mbhallgren96/dna_mini_reg_seqs.txt:/tmp/input/dna_mini_reg_seqs.txt /bin/bash -c "cp /tmp/input/dna_mini_reg_seqs.txt sequences; abricate --setupdb; --list"
#docker run --name filtlong_500mbp -it -v /home/mbhallgren96/test1/tmp/CPO20180119.q7.fastq.gz.q7_nanofilt :/tmp/input/CPO20180119.q7.fastq.gz.q7_nanofilt  nanozoo/filtlong filtlong --target_bases 500000000 /tmp/input/CPO20180119.q7.fastq.gz.q7_nanofilt  > /home/mbhallgren96/test1/tmp/CPO20180119.q7.fastq.gz.q7_nanofilt_out