#!/usr/bin/python

from geography_common import *
from models_current_knowledge import *
import sys

# outdated... now I prefer to use RMSE... maybe
def sensi_analysis_roc(data, Model, values):
    for pval in values:
        print "par value", pval
        m = Model(pval)
        m.process_data(data)
        do_roc(*zip(*m.log))
    plt.show()

def sensi_analysis(data, Model, values, par_name = None, do_plot = 1, verbose=1):
    rmses = []
    best = 0
    for i in range(len(values)):
        pval = values[i]
        if verbose: print "par value", pval, 
        if par_name == None:
            m = Model(pval)
        else:
            args = { par_name: pval }
            m = Model(**args)
        m.process_data(data)
        r = log_rmse(m.log)
        if verbose: print "\tRMSE", round(r,3)
        rmses.append(r)
        if rmses[i] < rmses[best]: best = i
    print "Best par value:", values[best]
    if do_plot:
        plt.plot(values, rmses)
        plt.show()
    
def compare_models(data, models):
    leg = []
    for m in models:
        print str(m), " "*(max(1,20 - len(str(m)))),
        leg.append(str(m))
        m.process_data(data)
#        do_roc(*zip(*m.log))
        print "\tRMSE    \t", round(log_rmse(m.log), 3), 
        print "\tLog loss\t", round(log_logloss(m.log), 3)
#     plt.legend(leg, loc = 4)
#    plt.show()

def show_predictions(data, m1, m2):
    m1.process_data(data)
    m2.process_data(data)
    selection = random.sample(m1.logmap.keys(), 400)
    preds = [ [], [] ]
    for k in selection:
        (p1, c1) = m1.logmap[k]
        (p2, c2) = m2.logmap[k]
        assert c1 == c2
        if c1 == 0: preds[0].append((p1, p2))
        else: preds[1].append((p1,p2))
    plt.scatter(*zip(*preds[1]), color = "blue")
    plt.scatter(*zip(*preds[0]), color = "red")
    plt.plot((0,1), (0,1))
    plt.xlabel(str(m1))
    plt.ylabel(str(m2))
    plt.show()
    
def classes_stats(log, n = 10):
    bounds = np.linspace(0,1,n+1)
    midpoints = np.zeros(n)
    a = np.zeros(n)
    for i in range(n):
        midpoints[i] = (bounds[i] + bounds[i+1])/2
        tmp = filter(lambda x: bounds[i] <= x[0] < bounds[i+1], log)
        alli = len(tmp)
        onesi = len(filter(lambda x: x[1]==1, tmp))
        if alli: print midpoints[i], round(onesi / float(alli), 2), "\t", alli
        if len(tmp) > 0:
            a[i] =  onesi / float(alli)
    print
    return (midpoints, a)

def show_prediction_classes(data, models):
    leg = []
    for m in models:
        m.process_data(data)
        plt.plot(*classes_stats(m.log,10))
        leg.append(str(m))
    plt.plot((0,1), (0,1))
    plt.legend(leg, loc = 4)
    plt.show()
    
######################### MAIN ######################

def run_sensi_analysis(data, choice):
    options = {
        'BKT' : [ BKT, [0.3, 0.4, 0.5, 0.55, 0.6, 0.7 ] ],
        'Elo' : [ EloBasic, [0.75, 1.0,  1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75] ],
        'Elot' : [ Elo, [ 0, 40, 80, 120, 160, 200, 240 ], "time_effect" ],
        'Eloa' : [ Elo, [ 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0 ], "alpha" ],
        'PFAg': [ PFA, [ 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6], "Kgood"],
        'PFAb': [ PFA, [ -0.2, 0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2], "Kbad"],
        'PFAt': [ PFA, [ 0, 40, 60, 80, 120, 160 ], "time_effect"]
        }
    if choice in options.keys():
        sensi_analysis(data, *options[choice])
    else:
        for c in options.keys():
            print "\n",c
            sensi_analysis(data, *options[c], do_plot=0, verbose=0)

def run_model_comparison(data, choice):
    options = {
        '': [ BKT(), Elo(),  PFA(), TimeDecay(0.1) ],
        '2': [ BKT(0.3), Elo(0.3,100), PFA ],
        }
    if not choice in options:
        choice = ''
    compare_models(data, options[choice])
            
def main():
    if len(sys.argv) < 2:
        print "Gimme command"
        return
    datafile = "data/repeated_attempts.csv"
    arg2 = ""
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
    data = read_combined_data(datafile)
    if sys.argv[1] == "sensi":
        run_sensi_analysis(data, arg2) 
    elif sys.argv[1] == "compare":
        run_model_comparison(data, arg2)
    elif sys.argv[1] == "show":
        show_predictions(data, PFA(), Elo()  )        
    elif sys.argv[1] == "classes":
        show_prediction_classes(data, [ PFA(), Elo(), BKT()])
    else:
        print "Dont know what", sys.argv[1], "means."
    
if __name__ == "__main__":
    main()
        
