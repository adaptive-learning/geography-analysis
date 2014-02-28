#!/usr/bin/python

import sys
import pylab as plt
from geography_common import *
from models_prior_knowledge import *

def visit_stats(filename = "data/export.csv"):
    f = open(filename)
    f.readline() # zahodim prvni radek s popisem, protoze to hackuju pres cisilka
    lines = f.readlines()
    lines.reverse()
    users = set([])
    lastdate = ''
    steps = 0
    udata = []
    sdata = []
    for l in lines:
        p = l.rstrip().split(',')        
        date = p[5][:10]
        if date != lastdate:
            print lastdate, len(users), steps
            udata.append(len(users))
            sdata.append(steps)
            users = set([])
            steps = 0        
        lastdate = date
        steps += 1
        users.add(p[1])
    print lastdate, len(users), steps
    plt.plot(range(len(udata)), udata)
    plt.ylabel("users")
    plt.figure()
    plt.plot(range(len(sdata)), sdata)
    plt.ylabel("answers")
    plt.show()

def stats_repeated():
    f = open("data/repeated_attempts.csv")
    solved, attempts, incorrect = {}, {}, {}
    states, codes = process_states()    
    for l in f.readlines():
        p = l.rstrip().split(';')
        place = int(p[1])
        solved[place] = solved.get(place,0) + 1
        attempts[place] = attempts.get(place,0) + p[2].count(':') + 1
        incorrect[place] = incorrect.get(place,0) + p[2].count('0(') 
    f.close()
    for place in sorted(solved.keys(), key=lambda x: solved[x]):
        print place, states.get(place,"XX").ljust(20).encode("UTF8"), solved[place], attempts[place], incorrect[place]


def solved_difficulty():
    data = read_data("data/data_first.csv")
    solved = data.place.value_counts()
    D = read_dict("data/raschD.csv")
    onmap = process_placerelation()
    states, _ = process_states()
    leg = []
    colors = ['b','g','r','y','c','m','k']
    continents = [ 227, 228, 229, 230, 231 ]
    for i in range(len(continents)):
        cont = continents[i]
#        print i, continents[i], states[cont]
        v = []
        for p in onmap[cont]:
            if p in solved.keys() and p in D.keys():
                v.append((solved[p], D[p]))
        plt.scatter(*zip(*v), color = colors[i])
        leg.append(states[cont])
    plt.xlabel("solved")
    plt.ylabel("difficulty")
    plt.legend(leg, loc = 1)
    for p in sorted(D.keys(), key = lambda x: D[x]):
        print p, states[p][:18].ljust(20).encode("UTF8"), D[p], "\t", solved.get(p, 0)
    plt.show()

def histDG():
#    G = read_dict("data/raschG.csv")
#    D = read_dict("data/raschD.csv")
    m = EloModel()
    data = read_data("data/data_first.csv")
    m.process_data(data)
    G, D = m.G, m.D
    plt.hist(G.values())    
    plt.figure()
    onmap = process_placerelation()
    onmap[228229] = onmap[228][:]
    onmap[228229].extend(onmap[229][:]) # spojeni amerik
    states, _ = process_states()
    states[228229] = "Amerika"
    continents = [ 227, 228229, 231, 232, 230 ]
    d = [ [ D[p] for p in onmap[c] ]
          for c in continents ]
#    plt.hist(d, 7, histtype='barstacked')
#    plt.hist(d, range(-4, 4), histtype='barstacked')
    plt.hist(d, [ i - 0.5 for i in range(-4, 4)], histtype='barstacked')
    plt.ylim([0,50])
    plt.legend([states[c] for c in continents], loc=2)
    plt.savefig("results/hist-states.svg")
    plt.show()

def skill_hist():
    plt.show()
    
def main():
    if len(sys.argv) < 2:
        print "Gimme command"
        return
    if sys.argv[1] == "visits":    
        visit_stats()
    elif sys.argv[1] == "rep":    
        stats_repeated()
    elif sys.argv[1] == "soldif":    
        solved_difficulty()
    elif sys.argv[1] == "hist":    
        histDG()
        
if __name__ == "__main__":
    main()


