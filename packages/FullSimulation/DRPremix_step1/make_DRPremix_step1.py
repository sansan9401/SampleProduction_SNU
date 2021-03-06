import os,sys,socket,pwd
from datetime import datetime

def print_sampleinfo(sample_name, inputpath):
        print "[INFO] "+sample_name
        print "[INFO] || "+inputpath

def exit_argumenterr():
        print "[EXIT] Input arguments are not correctly given"
        print "[EXIT] single : python make_"+nametag+".py RUNMODE SAMPLENAME INPUTPATH"
        print "[EXIT] multiple : python make_"+nametag+".py RUNMODE LIST.dat"
        sys.exit()

def exit_runhosterr(runmode, hostname):
        print "[EXIT] "+runmode+" could not be submitted to "+hostname
        print "[EXIT] MULTICORE : SNU"
        print "[EXIT] CLUSTER : SNU tamsa & KISTI"
        print "[EXIT] CRABJOB : KNU & KISTI"
        sys.exit()

username = pwd.getpwuid(os.getuid()).pw_name

cwd = os.getcwd()
datasettag = cwd.split("/")[-2]
nametag =datasettag.split("__")[0]
year = cwd.split("/")[-3]

try:
  runmode = sys.argv[1]
except:
  exit_argumenterr()
if (len(sys.argv) == 3):
  if (".dat" in sys.argv[2]):
    multi_flag = True
    inputpath = sys.argv[2]
  else:
    exit_argumenterr()
elif (len(sys.argv) == 4):
  multi_flag = False
else:
  exit_argumenterr()

hostname = os.getenv("HOSTNAME")
if (runmode == "MULTICORE"):
  if not hostname in ["cms1", "cms2"]:
    exit_runhosterr(runmode,hostname)
elif (runmode == "CLUSTER"):
  if not hostname in ["tamsa1", "tamsa2", "ui10.sdfarm.kr", "ui20.sdfarm.kr"]:
    exit_runhosterr(runmode,hostname)
elif (runmode == "CRABJOB"):
  if not hostname in ["cms.knu.ac.kr", "cms01.knu.ac.kr", "cms02.knu.ac.kr", "cms03.knu.ac.kr", "lxplus", "ui10.sdfarm.kr", "ui20.sdfarm.kr"]:
    exit_runhosterr(runmode,hostname)
else:
  exit_runhosterr(runmode,hostname)

minbias_files = "\"###PILEUP_INPUT\""
if year == "2016": nevt_minbias = 2052. #these are nevents each minbias files have
if year == "2017": nevt_minbias = 1433.
if year == "2018": nevt_minbias = 800.
n_minbias = int(70000./nevt_minbias)
if hostname in ["tamsa1", "tamsa2", "cms1", "cms2"]:
  use_SNU = True
  os.system("ls -1 /data9/Users/shjeon_public/PRESERVE/MinBias/FullSimulation/"+year+"/*root &>skeleton/ThisMinBias.dat")
else:
  use_SNU = False
  os.system("cp skeleton/FullMinBias_"+year+".dat skeleton/ThisMinBias.dat")
#  if (year == "2016"): minbias_files = "\"dbs:/Neutrino_E-10_gun/RunIISpring15PrePremix-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v2-v2/GEN-SIM-DIGI-RAW\""
#  elif (year == "2017"): minbias_files = "\"dbs:/Neutrino_E-10_gun/RunIISummer17PrePremix-MCv2_correctPU_94X_mc2017_realistic_v9-v1/GEN-SIM-DIGI-RAW\""
#  elif (year == "2018"): minbias_files = "\"dbs:/Neutrino_E-10_gun/RunIISummer17PrePremix-PUAutumn18_102X_upgrade2018_realistic_v15-v1/GEN-SIM-DIGI-RAW\""

try:
  hostname=hostname+" "+socket.gethostbyname(socket.gethostname())
except:
  print "[WARNING] socket.gethostbyname(socket.gethostname()) is not working"

ncores = 0
ncores_many = 0
if (multi_flag == True):
  if (os.path.exists("submit_many.sh") or os.path.exists("submit_many_dir")):
    print "[EXIT] Make sure you cleared up all the shell script files before generating new submit scripts"
    print "[EXIT] Please execute : rm -rf submit_many_dir; rm submit_many.sh"
    sys.exit()

  os.system("mkdir submit_many_dir")
  tmp_multi_flag = open ("tmp/multi_flag", "w")
  tmp_multi_flag.close()
  submitmanyshellfile = open("submit_many.sh", "w")
  submitmanyshellfile.write("rm tmp/multi_flag\n")
  submitmanyshellfile.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n")
  submitmanyshellfile.write("eval `scramv1 runtime -sh`\n")

  listf = open(inputpath)
  lists = listf.readlines()
  listf.close()
  for listl in lists:
    listl = listl.strip()
    sample_name = listl.split("\t")[0]
    inputpath = listl.split("\t")[1]
    submitmanyshellfile.write("source "+cwd+"/submit_many_dir/submit_"+sample_name+".sh\n")
    os.system("python make_"+nametag+".py "+runmode+" "+sample_name+" "+inputpath)
    inputlinef = open("tmp/"+sample_name+".dat")
    inputlines = inputlinef.readlines()
    inputlinef.close()
    ncores_many = ncores_many+len(inputlines)
  submitmanyshellfile.close()
else:
  sample_name = sys.argv[2]
  inputpath = sys.argv[3]

  if (runmode == "MULTICORE" or runmode == "CLUSTER"):
    os.system("rm "+inputpath+"/*_inLHE.root")
    os.system("ls -1 "+inputpath+"/*.root &> tmp/"+sample_name+".dat")

    inputlinef = open("tmp/"+sample_name+".dat")
    inputlines = inputlinef.readlines()
    inputlinef.close()
    inputlinef_tmp = open("tmp/"+sample_name+"_tmp.dat","w")
    for inputlinel in inputlines:
      inputlinel=inputlinel.strip()
      if os.path.exists(inputlinel):
        if (use_SNU == True):
          inputlinef_tmp.write("file://"+inputlinel+"\n")
        else:
          inputlinef_tmp.write("root://cms-xrdr.private.lo:2094//xrd/store/user/"+username+"/"+inputlinel.split("/xrootd/")[1]+"\n")
      else:
        print "[EXIT] Inputfiles does not exist"
        print "[EXIT] Please execute : cat tmp/"+sample_name+".dat"
        sys.exit()
    inputlinef_tmp.close()
    os.system("mv tmp/"+sample_name+"_tmp.dat tmp/"+sample_name+".dat")
    inputlinef = open("tmp/"+sample_name+".dat")
    inputlines = inputlinef.readlines()
    inputlinef.close()

    ncores = len(inputlines)

if (runmode == "MULTICORE"):
  if (int(ncores_many) > 70) or (int(ncores) > 70):
    print "[EXIT] Number of cores too many : should not be more than 70 [cms*.snu.ac.kr]"
    sys.exit()

if (multi_flag == True):
  sys.exit()
else:
  if os.path.exists("tmp/multi_flag"):
    submitshellfile = open("submit_many_dir/submit_"+sample_name+".sh", "w")
  else:
    submitshellfile = open("submit.sh", "w")
    submitshellfile.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n")
    submitshellfile.write("eval `scramv1 runtime -sh`\n")

if (os.path.exists(runmode+"/"+sample_name+"/") or os.path.exists("output/"+sample_name+"/")):
  print "[EXIT] Either "+runmode+"/"+sample_name+"/ or output/"+sample_name+"/ already exists"
  sys.exit()
else:
  os.system("mkdir -p "+runmode+"/"+sample_name+"/")
  if (runmode == "MULTICORE") or (runmode == "CLUSTER"):
    os.system("mkdir -p output/"+sample_name+"/")

print_sampleinfo(sample_name, inputpath)

cmsdriverf = open("skeleton/"+nametag+".dat")
cmsdrivers = cmsdriverf.readlines()
cmsdriverf.close()
for cmsdriverl in cmsdrivers:
  if (year == cmsdriverl.strip().split("\t")[0]):
    cmsdriverdat = cmsdriverl.strip().split("\t")[1]

cmsdrivercmd = "cmsDriver.py "+cmsdriverdat+" -n 91117"
submitshellfile.write("###Submitting "+sample_name+"\n")

if (runmode == "MULTICORE") or (runmode == "CLUSTER"):
  for ijob in range(1,ncores+1):
    os.system("mkdir -p "+runmode+"/"+sample_name+"/run"+str(ijob))
    os.system("cp skeleton/sedcommand.py "+runmode+"/"+sample_name+"/run"+str(ijob)+"/")
    os.system("cp skeleton/ThisMinBias.dat "+runmode+"/"+sample_name+"/run"+str(ijob)+"/")

    runshellfile = open(runmode+"/"+sample_name+"/run"+str(ijob)+"/run"+str(ijob)+".sh","w")
    runshellfile.write("cd "+cwd+"/"+runmode+"/"+sample_name+"/run"+str(ijob)+"/\n")
    runshellfile.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n")
    runshellfile.write("eval `scramv1 runtime -sh`\n")
    this_cmsdrivercmd = cmsdrivercmd+" --python_filename run"+str(ijob)+".py --fileout \"file:"+cwd+"/output/"+sample_name+"/"+nametag+"_"+str(ijob)+".root\" --pileup_input "+minbias_files+" --filein \"file:"+inputlines[ijob-1].strip()+"\""
    runshellfile.write(this_cmsdrivercmd+"\n")
    runshellfile.write("python sedcommand.py run"+str(ijob)+".py "+str(n_minbias)+"\n")
    runshellfile.write("cmsRun run"+str(ijob)+".py &> run"+str(ijob)+".log\n")
    runshellfile.close()

    submitshellfile.write("cd "+cwd+"/"+runmode+"/"+sample_name+"/run"+str(ijob)+"\n")
    if (runmode == "MULTICORE"):
      submitshellfile.write("chmod 755 "+cwd+"/"+runmode+"/"+sample_name+"/run"+str(ijob)+"/run"+str(ijob)+".sh\n")
      submitshellfile.write("nohup "+cwd+"/"+runmode+"/"+sample_name+"/run"+str(ijob)+"/run"+str(ijob)+".sh &\n")
    elif (runmode == "CLUSTER"):
      os.system("cp skeleton/condor.jds "+runmode+"/"+sample_name+"/run"+str(ijob))
      os.system("sed -i 's|###CONDORRUN|executable = run"+str(ijob)+".sh|g' "+runmode+"/"+sample_name+"/run"+str(ijob)+"/condor.jds")
      os.system("sed -i 's|###JOBBATCHNAME|+JobBatchName=\""+sample_name+"\"|g' "+runmode+"/"+sample_name+"/run"+str(ijob)+"/condor.jds")
      submitshellfile.write("condor_submit condor.jds\n")

elif (runmode == "CRABJOB"):
  os.system("cp skeleton/crab.py "+runmode+"/"+sample_name+"/")
  os.system("sed -i 's|###REQUESTNAME|config.General.requestName = \""+sample_name+"__"+datasettag+"\"|g' "+runmode+"/"+sample_name+"/crab.py")
  os.system("sed -i 's|###PSETNAME|config.JobType.psetName = \""+sample_name+".py\"|g' "+runmode+"/"+sample_name+"/crab.py")
  os.system("sed -i 's|###INPUTDATASET|config.Data.inputDataset = \""+inputpath+"\"|g' "+runmode+"/"+sample_name+"/crab.py")
  os.system("sed -i 's|###OUTPUTTAG|config.Data.outputDatasetTag = \""+datasettag+"\"|g' "+runmode+"/"+sample_name+"/crab.py")
  os.system("cp skeleton/sedcommand.py "+runmode+"/"+sample_name+"/")
  os.system("cp skeleton/ThisMinBias.dat "+runmode+"/"+sample_name+"/")

  runshellfile = open(runmode+"/"+sample_name+"/run.sh","w")
  this_cmsdrivercmd = cmsdrivercmd+" --python_filename "+sample_name+".py --fileout \""+nametag+".root\" --nThreads 2 --pileup_input "+minbias_files
  runshellfile.write(this_cmsdrivercmd+"\n")
  runshellfile.write("python sedcommand.py "+sample_name+".py "+str(n_minbias)+"\n")
  runshellfile.write("crab submit -c crab.py\n")
  runshellfile.close()

  submitshellfile.write("cd "+runmode+"/"+sample_name+"\n")
  submitshellfile.write("source run.sh\n")
submitshellfile.write("cd "+cwd+"\n")
submitshellfile.close()
