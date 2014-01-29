from __future__ import division
import pandas as pd
from pandas import DataFrame, Series
import numpy as np
import json
import math
import random
import re
from sklearn.metrics import roc_curve, auc
from scipy.stats import spearmanr
import pylab as plt

# lot of small stuff doing rutine work... bit messy

################# reading data ######################

def read_json(filename):
    f = open(filename)
    data = json.load(f)
    f.close()
    return data    

def process_states(filename = "data/place.json", data = None):
    info = read_json(filename)
    states = {}
    codes = {}
    for r in info:
        states[r["pk"]] = r["fields"]["name"]
        codes[r["pk"]] = r["fields"]["code"]
    if data:
        for place in data.place.unique():
            if not place in states:
                states[place] = 'unknown'
                codes[place] = 'XX'        
    return states, codes

def process_placerelation(filename = "data/placerelation.json"):
    info = read_json(filename)
    onmap = {}
    for r in info:
        if r["fields"]["type"] == 1:
            onmap[r["fields"]["place"]] = r["fields"]["related_places"]
    return onmap

def add_norm_user_times(d):
    meant = {}
    for u in d.user.unique():
        meant[u] = np.mean(np.log(d[d.user==u].time))
    normt = [ np.log(d.time[i]) - meant[d.user[i]] for i in d.index ]
    d["ntime"] = Series(normt, index = d.index)
#    hist([d.ntime[d.correct==1],d.ntime[d.correct==0]],normed=1)

def read_data(filename = "data/data.csv"):
    d = pd.read_csv(filename)
    d.time[d.time > 30000] = 30000 # time cut-off 30s 
    add_norm_user_times(d)
    return d

# reading two column csv as dict; ... bit of a hack
def read_dict(filename):
    f = open(filename)
    f.readline() #ignoring first line of csv
    d = {}
    for line in f.readlines():
        p = line.rstrip().split(',')
        d[int(p[0])] = float(p[1])
    return d

###### combined data - predikce z rasch modelu + data o opakovanych odpovedich

def read_combined_data(data_repeated, fileD = "data/raschD.csv", fileG = "data/raschG.csv"):
    D = read_dict(fileD)
    G = read_dict(fileG)        
    f = open(data_repeated)
    data = {}
    for line in f.readlines():
        p = line.rstrip().split(';')            
        ans, qtype, time = [],[],[]
        ok = 1
        student = int(p[0])
        place = int(p[1])
        if not place in D: continue  # nove pridano, beru jen mista, pro ktera mam dost dat a tudiz odhad D        
        for resp in p[2].split(':'):
            m = re.match(r'(\d)\((\d+),(\d+)\)',resp)
            if m: 
                ans.append(int(m.group(1)))
                qtype.append(int(m.group(2)))
                time.append(int(m.group(3)))
            else:
                ok = 0
        if ok:
            if not (place in data): data[place] = {}
            data[place][student] = {
                'init': sigmoid(G.get(student,0) - D.get(place,0)),
                'initskill': G.get(student,0) - D.get(place,0),
                'ans': ans, 'qtype':qtype, 'time':time, 'n': len(ans) }
    f.close()
    return data

def test_printout(data):
    for s, p in data.keys():
        print s, p
        print "\tinit prob:", round(data[s,p]['init'],2)
        for i in range(data[s,p]['n']):
            print "\t",data[s,p]['ans'][i], data[s,p]['time'][i]


# not used currently
def split_data_user_level(data, ratio = 0.8):
    users = data.user.unique()
    count = int(len(users) * ratio)
    sample = random.sample(users, count)
    in_sample = data.user.map(lambda x: x in sample)
    data1 = data[in_sample]
    data2 = data[in_sample == False]
    return data1, data2

################## small helper functions ################

# ad hoc values
def slip(qtype):
    return 0.02

def guess(qtype):
    if qtype == 10: return 0.04 # should be map dependent
    return 1.0 / (qtype - 10*(qtype//10))

def random_factor(qtype):
    if qtype == 10: return 0
    return 1.0 / (qtype - 10*(qtype//10))

# weighted mean with respect to time decay function
def weighted_mean(seq, n, fun):
    s, w = 0.0, 0
    for i in range(n):
        w += fun(i)
        s += fun(i) * seq[n-i-1]
    return s/w

def exp_fun(k):
    return lambda x: math.exp(-k*x)

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def sigmoid_shift(x, c):
    return c + (1-c) * sigmoid(x)

def rmse(estimated, correct):
    return math.sqrt(np.mean((np.array(correct) - np.array(estimated))**2))

def log_rmse(log):
    return rmse(*zip(*log)) # asi ne moc efektivni...

# def logloss(estimated, correct):
#     # prepsat vektorove?
#     s = 0.0
#     n = len(correct)
#     for i in range(n):
#         if correct[i]:
#             s += math.log(estimated[i])
#         else:
#             s += math.log(1-estimated[i])
#     return - s / n

def log_logloss(log):
    s = 0.0
    n = len(log)
    for i in range(n):
        if log[i][1]:
            s += math.log(log[i][0])
        else:
            s += math.log(max(1-log[i][0], 0.02)) # trochu hack
    return - s / n

def mae(estimated, correct):
    return np.mean(np.absolute(np.array(correct) - np.array(estimated)))

def log_mae(log):
    return mae(*zip(*log))

def do_roc(estimated, correct, desc = ""):
    fpr, tpr, thresholds = roc_curve(correct, estimated)
    roc_auc = auc(fpr, tpr)
    print desc, "AUC", roc_auc
    plt.plot(fpr, tpr)

def auc_metric(estimated, correct):    
    fpr, tpr, thresholds = roc_curve(correct, estimated)
    return auc(fpr, tpr)

def log_auc(log):    
    return auc_metric(*zip(*log))

def pairwise_sum(a, b):
    return tuple(map(sum, zip(a,b)))

def spearman(x,y):
    return spearmanr(x,y)[0]

############# visualization and analysis helpers ##########

def values_in_order(d, k):
    return [ d.get(x,0) for x in k ]
        
def scatter_dicts_with_same_keys(dict1, dict2):
    k = dict1.keys()
    v1 = values_in_order(dict1, k)
    v2 = values_in_order(dict2, k)
    plt.scatter(v1, v2)
    print "spearman", round(spearman(v1,v2),2)

def plot_scatter(p1, p2, labelx, labely, symbol = 'o'):
    plt.figure()
    plt.plot(p1, p2, symbol)
    plt.xlabel(labelx)
    plt.ylabel(labely)
    print labelx, labely, "spearman", round(spearman(p1,p2),2)
    
############# prevzato z problem solving times a rozsireno

class MultipleRunLogger:
    
    def __init__(self, verbose = 0):
        self.row_names = []
        self.col_names = [] 
        self.data = {}
        self.verbose = verbose

    def log(self, r, c, value):
        if not r in self.row_names:
            self.row_names.append(r)
        if not c in self.col_names:
            self.col_names.append(c)
        if not (r,c) in self.data:
            self.data[r,c] = []        
        self.data[r,c].append(value)
        if self.verbose:
            print r, c, len(self.data[r,c]), value
        
    def print_table(self, sep = "\t", line_end = "", print_best = 0):
        # print_best = 1 (vyssi lepsi), = 2 (nizsi lepsi)
        if print_best == 1: best = (-float('inf'), "","")
        if print_best == 2: best = (float('inf'), "","")
        w = max(map(lambda x: len(x), self.row_names)) + 1
        print
        print " "*w,sep, sep.join(self.col_names), line_end
        for r in self.row_names:
            print r.ljust(w), 
            for c in self.col_names:
                if len(self.data[r,c]) == 0:
                    print sep, "-", 
                else:
                    val = float(sum(self.data[r,c])) / len(self.data[r,c])
                    print sep, round(val, 3),
                    if print_best == 1 and val > best[0]: best = (val, r, c)
                    if print_best == 2 and val < best[0]: best = (val, r, c)
            print line_end
        print
        if print_best:
            print "Best:", best[1], best[2], round(best[0], 3)
        
    def get_table(self):
        t = np.zeros((len(self.row_names), len(self.col_names)))
        for i in range(len(self.row_names)):
            for j in range(len(self.col_names)):
                t[i][j] = float(sum(self.data[self.row_names[i],self.col_names[j]])) / len(self.data[self.row_names[i],self.col_names[j]])
        return t
        # use plt.imshow(t)
