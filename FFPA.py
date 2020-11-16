import sys
import os
import argparse
import subprocess
import random
import time

parser = argparse.ArgumentParser(description='.')
parser.add_argument('-i_trimmed_illumina', action="store", nargs="+", type=str, dest='i_trimmed_illumina',  default="", help='Input for trimmed iilumina reads. If PE, give 2 input files seperated by a space. Please use the complete path to the given file')
parser.add_argument('-i_raw_illumina', action="store", nargs="+", type=str, dest='i_raw_illumina', default="", help='Input for untrimmed iilumina reads. If PE, give 2 input files seperated by a space. Please use the complete path to the given file')
parser.add_argument('-i_trimmed_nanopore', action="store", type=str, dest='i_trimmed_nanopore', default="", help='Input for trimmed Nanopore reads. Please use the complete path to the given file')
parser.add_argument('-i_raw_nanopore', action="store", type=str, dest='i_raw_nanopore', default="", help='Input for untrimmed Nanopore reads. Please use the complete path to the given file')
parser.add_argument('-trimmomatic_db', action="store", type=str, dest='trimmomatic_db', default="TruSeq3", help='Use either \"TruSeq3\" or \"Nextera\" as db.')
parser.add_argument('-nanoporeqscore', action="store", type=str, dest='nanoporeqscore', default="7", help='nanoporeqscore for nanopore filtering')
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
if args.i_raw_illumina[-3:] == ".gz":
    cmd = "gunzip -c {} > {}/tmp/{}.fastq".format(args.i_raw_nanopore, target_dir, nanopore_name)
    os.system(cmd)
else:
    cmd = "cp {} {}/tmp/{}".format(args.i_raw_nanopore, target_dir, nanopore_name)
    os.system(cmd)

print ("Trimmomatic started")
if args.i_raw_illumina != "":
    if paired_end == True:
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


    else:
        cmd = "docker run -it -v {}:/tmp/illuminaSE/ --name trimmomatic_container{} fjukstad/trimmomatic SE /tmp/illuminaSE/{} /tmp/output ILLUMINACLIP:{}:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36".format(target_dir, jobid, illumina_name, trimmomatic_db)
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

#NANOPLOT
cmd = "docker run --name nanoplot{} -it -v {}/tmp/{}:/tmp/{} nanozoo/nanoplot:1.32.0--1ae6f5d NanoPlot --fastq_rich /tmp/{} -o /tmp/nanoplots/ --N50 -p {} -t 8".format(jobid, target_dir, trimmed_nanopore, trimmed_nanopore, trimmed_nanopore, trimmed_nanopore)
os.system(cmd)


proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("nanoplot", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker cp {}:/tmp/nanoplots {}/tmp/.".format(id, target_dir)
os.system(cmd)


cmd = "docker container rm {}".format(id)
os.system(cmd)

#FASTQC:
if args.i_raw_illumina != "" or args.i_trimmed_illumina != "":
    cmd = "docker run --name fastqc{} -it -v {}/tmp/{}:/tmp/input nanozoo/fastqc fastqc --extract -t 8 /tmp/input/{} /tmp/input/{} ".format(jobid, target_dir, "illuminaPE_trimmed", illumina_name1, illumina_name2)
    os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("fastqc", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

cmd = "docker cp {}:/tmp {}/tmp/fastqc".format(id, target_dir)
os.system(cmd)


cmd = "docker container rm {}".format(id)
os.system(cmd)


#Nanopore pipeline
cmd = "docker run --name nanofilt_q{}  -it -v {}/tmp/{}:/tmp/input/{} mcfonsecalab/nanofilt NanoFilt -q {} /tmp/input/{} | gzip > {}/tmp/{}.q{}_nanofilt".format(jobid, target_dir, trimmed_nanopore, trimmed_nanopore, args.nanoporeqscore, trimmed_nanopore, target_dir, nanopore_name, args.nanoporeqscore)
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

cmd = "mv {}/tmp/{}.q{}_nanofilt {}/tmp/{}.q{}_nanofilt.fastq".format(target_dir, nanopore_name, args.nanoporeqscore, target_dir, nanopore_name, args.nanoporeqscore)
os.system(cmd)

print ("nanofilt l 10000 complete")
q_reads = "{}.q{}_nanofilt.fastq".format(nanopore_name, args.nanoporeqscore)

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

    cmd = "rm {}/tmp/kraken_report_illumina".format(target_dir)
    os.system(cmd)

    cmd = "rm {}/tmp/krakenoutput_illumina".format(target_dir)
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

    cmd = "rm {}/tmp/kraken_report_illumina".format(target_dir)
    os.system(cmd)

    cmd = "rm {}/tmp/krakenoutput_illumina".format(target_dir)
    os.system(cmd)

cmd = "rm {}/tmp/kraken_report_nanopore".format(target_dir)
os.system(cmd)

cmd = "rm {}/tmp/krakenoutput_nanopore".format(target_dir)
os.system(cmd)



#HERE
#Unicycler nanopore

cmd = "docker run --name assembly_qreads{} -it -v {}/tmp/{}:/tmp/input/{} nanozoo/unicycler:0.4.7-0--c0404e6 unicycler -l /tmp/input/{} -o /tmp/nanopore_assembly".format(jobid, target_dir, q_reads, q_reads, q_reads)
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

        cmd = "docker run --name hybrid_container{} -it -v {}/tmp/hybridinput/:/tmp/input/ nanozoo/unicycler:0.4.7-0--c0404e6  unicycler -1 /tmp/input/{} -2 /tmp/input/{} -l /tmp/input/{} -o /tmp/hybrid_assembly".format(jobid, target_dir, illumina_name1_o, illumina_name2_o, trimmed_nanopore)
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

        cmd = "docker run --name hybrid_container{} -it -v {}/tmp/hybridinput/:/tmp/input/ nanozoo/unicycler:0.4.7-0--c0404e6  unicycler -s /tmp/input/{} -l /tmp/input/{} -o /tmp/hybrid_assembly".format(jobid, target_dir, illumina_name_o, trimmed_nanopore)
        os.system(cmd)

        proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("hybrid_container", jobid), shell=True,stdout=subprocess.PIPE, )
        output = proc.communicate()[0]
        id = output.decode().rstrip()

        cmd = "docker cp {}:/tmp/hybrid_assembly {}/tmp/.".format(id, target_dir)
        os.system(cmd)

        cmd = "docker container rm {}".format(id)
        os.system(cmd)



#ABRRICATE HERE NOW


cmd = "docker run --name nanopore_abricate_plasmid{} -it -v {}/tmp/nanopore_assembly/assembly.fasta:/tmp/assembly.fasta replikation/abricate --db plasmidfinder /tmp/assembly.fasta > {}/tmp/nanopore_plasmidfinder_abricate".format(jobid, target_dir, target_dir)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("nanopore_abricate_plasmid", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

#cmd = "docker cp {}:/tmp/output {}/tmp/abricate_nanopore_plasmidfinder.".format(id, target_dir)
#os.system(cmd)

cmd = "docker container rm {}".format(id)
os.system(cmd)

cmd = "docker run --name nanopore_abricate_res{} -it -v {}/tmp/nanopore_assembly/assembly.fasta:/tmp/assembly.fasta replikation/abricate --db resfinder --minid 80 /tmp/assembly.fasta > {}/tmp/nanopore_resfinder_abricate".format(jobid, target_dir, target_dir)
os.system(cmd)

proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("nanopore_abricate_res", jobid), shell=True, stdout=subprocess.PIPE, )
output = proc.communicate()[0]
id = output.decode().rstrip()

#cmd = "docker cp {}:/tmp/output {}/tmp/abricate_nanopore_resfinder.".format(id, target_dir)
#os.system(cmd)

cmd = "docker container rm {}".format(id)
os.system(cmd)

cmd = "mv {}/tmp/nanopore_resfinder_abricate {}/tmp/nanopore_assembly/nanopore_resfinder_abricate".format(target_dir, target_dir)
os.system(cmd)
cmd = "mv {}/tmp/nanopore_plasmidfinder_abricate {}/tmp/nanopore_assembly/nanopore_plasmidfinder_abricate".format(target_dir, target_dir)
os.system(cmd)

if args.i_trimmed_illumina != "" or args.i_raw_illumina != "":

    cmd = "docker run --name hybrid_abricate_plasmid{} -it -v {}/tmp/hybrid_assembly/assembly.fasta:/tmp/assembly.fasta replikation/abricate --db plasmidfinder --minid 80 /tmp/assembly.fasta > {}/tmp/hybrid_plasmidfinder_abricate".format(jobid, target_dir, target_dir)
    os.system(cmd)

    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("hybrid_abricate_plasmid", jobid), shell=True,
                            stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    #cmd = "docker cp {}:/tmp/output {}/tmp/hybrid_abricate_plasmid.".format(id, target_dir)
    #os.system(cmd)

    cmd = "docker container rm {}".format(id)
    os.system(cmd)

    cmd = "docker run --name hybrid_abricate_res{} -it -v {}/tmp/hybrid_assembly/assembly.fasta:/tmp/assembly.fasta replikation/abricate --db resfinder /tmp/assembly.fasta > {}/tmp/hybrid_resfinder_abricate".format(jobid, target_dir, target_dir)
    os.system(cmd)

    proc = subprocess.Popen("docker ps -aqf \"name={}{}\"".format("hybrid_abricate_res", jobid), shell=True,
                            stdout=subprocess.PIPE, )
    output = proc.communicate()[0]
    id = output.decode().rstrip()

    #cmd = "docker cp {}:/tmp/output {}/tmp/hybrid_abricate_resfinder.".format(id, target_dir)
    #os.system(cmd)

    cmd = "docker container rm {}".format(id)
    os.system(cmd)

    cmd = "mv {}/tmp/hybrid_resfinder_abricate {}/tmp/hybrid_assembly/hybrid_resfinder_abricate".format(target_dir, target_dir)
    os.system(cmd)
    cmd = "mv {}/tmp/hybrid_plasmidfinder_abricate {}/tmp/hybrid_assembly/hybrid_plasmidfinder_abricate".format(target_dir, target_dir)
    os.system(cmd)


#Cleaning:
if args.i_raw_illumina != "" and args.i_trimmed_illumina != "":
    cmd = "rm -r {}/tmp/hybridinput".format(target_dir)
    os.system(cmd)
    cmd = "mv {}/tmp/illuminaPE_trimmed {}/tmp/illuminaReads".format(target_dir, target_dir)
    os.system(cmd)



cmd = "mkdir {}tmp/nanoporeReads".format(target_dir)
os.system(cmd)

cmd = "cp {}tmp/{}* {}tmp/nanoporeReads/.".format(target_dir, nanopore_name, target_dir)
os.system(cmd)

cmd = "mv {}/tmp/kraken_report_illumina_1percenthits {}/tmp/illuminaPE_trimmed".format(target_dir, target_dir)
os.system(cmd)

cmd = "mv {}/tmp/kraken_report_nanopore_1percenthits {}/tmp/nanoporeReads".format(target_dir, target_dir)
os.system(cmd)

cmd = "mv {}/tmp/fastqc/input/* {}/tmp/fastqc/.".format(target_dir, target_dir)
os.system(cmd)

cmd = "rm -r {}/tmp/fastqc/input".format(target_dir)
os.system(cmd)

cmd = "rm -r {}/tmp/fastqc/hsperfdata_root".format(target_dir)
os.system(cmd)

cmd = "rm -r {}/tmp/hybridinput".format(target_dir)
os.system(cmd)

#Renaming
if nanopore_name[-6:] == ".fastq":
    prefix_nanopore = nanopore_namenanopore_name[0:-6]
else:
    prefix_nanopore = nanopore_name[0:-9]
print (prefix_nanopore)
cmd = "rm {}/tmp/nanoporeReads/{}.fastq.gz.fastq".format(target_dir, prefix_nanopore)
os.system(cmd)
cmd = "mv {}/tmp/nanoporeReads/{}_trimmed.fastq {}/tmp/nanoporeReads/{}_trimmed.fastq.gz".format(target_dir, nanopore_name, target_dir, prefix_nanopore)
os.system(cmd)
cmd = "mv {}/tmp/nanoporeReads/{}.fastq.gz.{}_nanofilt.fastq {}/tmp/nanoporeReads/{}.{}_nanofilt.fastq".format(target_dir, nanopore_name, args.nanoporeqscore, target_dir, prefix_nanopore, args.nanoporeqscore)
os.system(cmd)



cmd = "mv {}/tmp/* {}/output/.".format(target_dir, target_dir)
os.system(cmd)
cmd = "rm -r {}/tmp".format(target_dir)
os.system(cmd)

