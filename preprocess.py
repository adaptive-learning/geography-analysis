#!/usr/bin/python

import sys
import datetime
import math
from geography_common import read_data
from models_prior_knowledge import Rasch

# zhackovane:
#  * lepsi by bylo pres pandas, read_csv... takto zahazuju prvni radek s popisem, protoze to hackuju pres cisilka ... fuj
#  * predpoklada usporadani zaznamu (inverzne)
#  * nefektivni pro velky soubory ... ale je to jen preprocessing a zatim rychle bez problemu, takze to me moc netrapi

def process(foutput, finput, umin = 10, pmin = 30, only_first = 0, only10 = 0):
    print "Creating", foutput
    f = open(finput)
    out = open(foutput,"w")
    f.readline() 
    usolved, psolved  = {}, {}
    lines = f.readlines() 
    for l in lines:
        p = l.rstrip().split(',')
        user = p[1]
        place = p[2]
        usolved[user] = usolved.get(user,0) + 1
        psolved[place] = psolved.get(place,0) + 1
    done = {}
    out.write("user,type,time,place,answer,correct\n")
    for l in lines[::-1]:
        p = l.rstrip().split(',')        
        if usolved[p[1]] > umin and psolved[p[2]] > pmin:
#            t = datetime.datetime.strptime(p[5], '%Y-%m-%d %H:%M:%S')
            # to v tom zakladnim nevyuzivam
            if ((only_first == 0) or (not ((p[1],p[2]) in done))) and \
                (only10 == 0 or (p[4]+p[7] == "10")):
                if p[2] == p[3]: c = "1"
                else: c = "0"            
                out.write(",".join([p[1], p[4]+p[7], p[6], p[2], p[3], c ])+"\n")
            done[p[1],p[2]] = 1
    f.close()
    out.close()

def repeated_attempts(foutput, finput, minlen = 3, mintimestep = 0):
    print "Creating", foutput
    f = open(finput)
    out = open(foutput,"w")
    f.readline() 
    lines = f.readlines()
    f.close()
    userplace = {}
    for l in lines:
        p = l.rstrip().split(',')
        up = p[1]+";"+p[2]
        if p[2] == p[3]: c = "1"
        else: c = "0"            
        rtime = int(p[6])
        if rtime > 30000: rtime = 30000
        if rtime < 200: rtime = 200
        rtime = round(math.log(rtime, 2),2)
        if not up in userplace: userplace[up] = []
        userplace[up].append((int(p[0]), c, p[4]+p[7], datetime.datetime.strptime(p[5], '%Y-%m-%d %H:%M:%S'), rtime))
    stats_all, stats_ones = 0.0, 0
    all_ones = {}
                
    for up in userplace.keys():
        if len(userplace[up]) >= minlen:  
            line = up+";" 
            first_date = None
            prev_date = None
            local_stats_all, local_stats_ones = 0,0
            for pk, c, t, d, rt in sorted(userplace[up]):
                if first_date == None:
                    first_date = d
                    dif, difprev = 0, 0
                else:
                    dif = int((d - first_date).total_seconds())
                    difprev = int((d - prev_date).total_seconds())
                if dif==0 or difprev > mintimestep:
                    line += c+"("+t+','+`dif`+","+`rt`+"):"
                    local_stats_all +=1
                    if c=="1": local_stats_ones += 1
                prev_date = d
            if local_stats_all >= minlen:
                out.write(line[:-1]+"\n")
                stats_all += local_stats_all
                stats_ones += local_stats_ones
    out.close()
    print "  Ratio correct:", round(stats_ones / stats_all, 3)

########## save results for use in 2. phase ##############
    
def save_resultsDG(data):
    print "Creating data/raschD.csv, data/raschG.csv"
    print "Running Rasch JMLE ..."    
    r = Rasch()
    r.process_data(data, it = 3)
    fd = open("data/raschD.csv", "w")
    fd.write("place,D\n")
    for p in r.D:
        fd.write(`p`+","+`r.D[p]`+"\n")
    fd.close()    
    fu = open("data/raschG.csv", "w")
    fu.write("user,G\n")
    for u in r.G:
        fu.write(`u`+","+`r.G[u]`+"\n")
    fu.close()
    
#save_results_csv()

###################

if __name__ == "__main__":
    exportfile = "data/export.csv"
    if len(sys.argv) > 1:
        exportfile = sys.argv[1]    
    process("data/data.csv", exportfile)
    process("data/data_first.csv", exportfile, only_first = 1)
    process("data/data_first60.csv", exportfile, only_first = 1, pmin = 60)
    repeated_attempts("data/repeated_attempts.csv", exportfile, mintimestep = 0)
    if len(sys.argv) > 2 and sys.argv[2] == 'DG':    
        data = read_data("data/data_first.csv")
        save_resultsDG(data)
