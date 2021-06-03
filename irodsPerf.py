"""
Performance test for different iRODS commandline clients 
Author: Christine Staiger
License: Apache2.0 (Wageningen University and Research, 2021)
"""

import os
import json
import time
import getpass
import irods
from irods.session import iRODSSession
import irods.keywords as kw
import pickle

def testdata(path):
    """
    Ensures directory testdata
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def testcoll(collpath, client, session=None):
    if client == 'python' and session != None:
        coll = session.collections.create(collpath)
        return coll.path
    elif client == 'cadaver':
        os.system("echo 'mkdir "+collpath+"' | cadaver")
    elif client == "icommands":
        os.system("imkdir -p "+collpath)
        return collpath
    else:
        raise Exception("No valid client to setup iRODS test collection.")

def createFileGB(path, size = 1):
    fname = path+'/data'+str(size)+'GB.img'
    cmd = 'fallocate -l '+str(size)+'G '+fname
    os.system(cmd)
    return path+'/data'+str(size)+'GB.img'

def createFileKB(path, size = 1, name = ''):
    fname = path+'/data'+str(size)+'KB.img_'+name
    cmd = 'fallocate -l '+str(size)+'K '+fname
    os.system(cmd)
    return path+'/data'+str(size)+'KB.img'

def pythonIrodsSession(password, envfile = None, host='', user='', zone=''):
    if envfile == None:
        session = iRODSSession(host=host, port=1247, user=user, password=password, zone=zone)
    else:
        with open(envfile) as f:
            ienv = json.load(f)
        session = iRODSSession(**ienv, password=password)

    return session

def icommandsSession():
    os.system('iinit')

def timeUploadPythonAPI(filepath, collpath, session, resource = None, checksum=False):
    opts = {}
    if checksum:
        opts[kw.REG_CHKSUM_KW] = ''
    if resource != None:
        opts[kw.RESC_NAME_KW] = resource
    session.collections.create(collpath)
    tic = time.perf_counter()
    session.data_objects.put(filepath, collpath+'/'+os.path.basename(filepath), **opts)
    toc = time.perf_counter()

    return [toc-tic, checksum, "python-"+irods.__version__]

def timeUploadIcommands(filepath, collpath, resource = None, checksum=False):
    cmd = "iput -bf" #bulk & recursive
    if checksum:
        cmd = cmd + " -K"
    if resource != None:
        cmd = cmd + " -R "+resource
    cmd = cmd + " " + filepath +" "+collpath
    print(cmd)
    tic = time.perf_counter()
    os.system(cmd)
    toc = time.perf_counter()

    return [toc-tic, checksum, "icommands"]

def timeUploadCollIcommands(datapath, collpath, resource = None, checksum=False):
    cmd = "iput -brf" #bulk & recursive
    if checksum:
        cmd = cmd + " -K"
    if resource != None:
        cmd = cmd + " -R "+resource
    cmd = cmd + " " + datapath +" "+collpath
    print(cmd)
    tic = time.perf_counter()
    os.system(cmd)
    toc = time.perf_counter()

    return [toc-tic, checksum, "icommands"]

def timeUploadCollPythonAPI(datapath, collpath, session, resource = None, checksum=False):
    opts = {}
    if checksum:
        opts[kw.REG_CHKSUM_KW] = ''
    if resource != None:
        opts[kw.RESC_NAME_KW] = resource
    walk = [datapath]
    tic = time.perf_counter()
    while len(walk) > 0:
        for srcDir, dirs, files in os.walk(walk.pop()):
            walk.extend(dirs)
            session.collections.create(collpath+"/"+os.path.basename(srcDir))
            for fname in files:
                session.data_objects.put(srcDir+'/'+fname,
                                         collpath+'/'+os.path.basename(srcDir)+'/'+fname,
                                         **opts)
    toc = time.perf_counter()

    return [toc-tic, checksum, "python-"+irods.__version__]

def timeUploadWebdav(filepath, collpath):
    tic = time.perf_counter()
    os.system("echo 'cd "+collpath+"\n put "+filepath+"' | cadaver")
    toc = time.perf_counter()
    return [toc-tic, False, "webdav"]

def timeUploadCollWebdav(datapath, collpath):
    base = os.path.basename(datapath)
    os.system("echo 'cd "+collpath+"\n mkdir "+base+"' | cadaver")
    os.chdir(datapath)
    os.chdir(os.pardir)
    tic = time.perf_counter()
    print("echo 'cd "+collpath+"\n mput "+base+"/*' | cadaver")
    os.system("echo 'cd "+collpath+"\n mput "+base+"/data500KB.img_279*' | cadaver")
    toc = time.perf_counter()
    os.chdir(os.environ['HOME'])
    return [toc-tic, False, "webdav"]

def cleaniRODS(collpath, client="icommands", session = None):
    if client == "icommands":
        os.system("irm -r "+collpath)
        os.system("irmtrash")
        return True
    elif client == "python" and session != None:
        coll =  session.collections.get(collpath)
        coll.remove(recurse=True, force=True)
        return True
    elif client == "cadaver":
        os.system("echo 'rmcol "+collpath+" ' | cadaver")
    else:
        print("CLEANUP: No valid client and session found.")
        return False

def cleanSystem(datapath):
    os.system("rm -rf "+datapath)
    return True

results = []

testdatasize = [2, 3, 5] #GB
testfolder = (4000, 500) #4000 files of 500KB

clients = ['icommands', 'python', 'cadaver']
collname = 'perfTest'
datafolder = '/home/staig001/testdata'

#setup testdata
print("Create testdata ...")
testdata(datafolder)
fnames = []
for size in testdatasize:
    fnames.append(createFileGB(datafolder, size))
testdata(datafolder+'/smallfiles')
for i in range(testfolder[0]):
    createFileKB(datafolder+'/smallfiles', size = 500, name = str(i))

# setup test environment on iRODS
for client in clients:
    if client == 'icommands':
        print("Icommands performance")
        icommandsSession()
        collpath = testcoll(collname, "icommands")
        print("Single large files ...")
        for fname in fnames:
            results.append([fname]+timeUploadIcommands(fname, collpath, checksum=False))
            results.append([fname]+timeUploadIcommands(fname, collpath, checksum=True))
        print("Bulk upload ...")
        results.append(['4000 files']+timeUploadCollIcommands(datafolder+'/smallfiles',
                                               collpath, resource = None, checksum=False))
        results.append(['4000 files']+timeUploadCollIcommands(datafolder+'/smallfiles',
                                               collpath, resource = None, checksum=True))
        cleaniRODS(collpath)
    if client == 'python':
        print("python client performance")
        #password = getpass.getpass('iRODS password: ')
        password = "...."
        session = pythonIrodsSession(password, envfile = None,
                                     host='MYHOST',
                                     user='MYUSER',
                                     zone='MYZONE')
        collpath = testcoll('/'+session.zone+'/home/'+session.username+'/'+collname,
                            client = "python", session = session)
        print("Single large files ...")
        for fname in fnames:
            results.append([fname]+timeUploadPythonAPI(fname, collpath, session, checksum=False))
            results.append([fname]+timeUploadPythonAPI(fname, collpath, session, checksum=True))
        print("Bulk upload ...")
        results.append(['4000 files']+timeUploadCollPythonAPI(datafolder+'/smallfiles',
                                               collpath, session, checksum=False))
        results.append(['4000 files']+timeUploadCollPythonAPI(datafolder+'/smallfiles',
                                               collpath, session, checksum=True))
        cleaniRODS(collpath, client="python", session = session)
    if client == 'cadaver':
        print("Cadaver checking setup: (.cadverrc & .netrc)")
        os.system("echo 'exit' | cadaver")
        os.system("echo 'mkdir "+collname+"' | cadaver") 
        for fname in fnames:
            results.append([fname]+timeUploadWebdav(fname, collname))
        results.append(['4000 files']+timeUploadCollWebdav(datafolder+"/smallfiles", 
                                                           collname))
        cleaniRODS(collpath, "cadaver")

filename = 'irodsPerformances.out.pickle'
print("Pickling results: "+filename)
outfile = open(filename, 'wb')
pickle.dump(results, outfile)
outfile.close()

cleanupSystem(datafolder)
