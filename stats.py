#!/usr/bin/python

import sys
import pylab as plt
from geography_common import *

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
        v = []
        for p in onmap[cont]:
            if p in solved.keys() and p in D.keys():
                v.append((solved[p], D[p]))
        plt.scatter(*zip(*v), color = colors[i])
        leg.append(states[cont])
    plt.xlabel("solved")
    plt.ylabel("difficulty")
    plt.legend(leg, loc = 1)
    plt.show()

def dif_hist():
    D = read_dict("data/raschD.csv")
    onmap = process_placerelation()
    states, _ = process_states()
    continents = [ 227, 228, 229, 230, 231 ]
    d = [ [ D[p] for p in onmap[c] ]
          for c in continents ]
    plt.hist(d, histtype='bar',normed=True) # stacked=True .. mi nefunguje, stara verze matplotlib?...
    plt.legend([states[c] for c in continents], loc=2)
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
        dif_hist()

        
if __name__ == "__main__":
    main()


