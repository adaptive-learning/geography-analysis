#!/usr/bin/python

from geography_common import *
from models_current_knowledge import *
import sys

# outdated... now I prefer to use RMSE
def sensi_analysis_roc(data, Model, values):
    for pval in values:
        print "par value", pval
        m = Model(pval)
        m.process_data(data)
        do_roc(*zip(*m.log))
    plt.show()

def sensi_analysis(data, Model, values, par_name = None):
    rmses = []
    for pval in values:
        print "par value", pval
        if par_name == None:
            m = Model(pval)
        else:
            args = { par_name: pval }
            m = Model(**args)
        m.process_data(data)
        r = log_rmse(m.log)
        print "\tRMSE", round(r,3)
        rmses.append(r)
    plt.plot(values, rmses)
    plt.show()
    
def compare_models(data, models):
    leg = []
    for m in models:
        print m
        leg.append(str(m))
        m.process_data(data)
        do_roc(*zip(*m.log))
        print " RMSE", log_rmse(m.log)
    plt.legend(leg, loc = 4)
    plt.show()

######################### MAIN ######################

def main():
    if len(sys.argv) < 2:
        print "Gimme command"
        return
    datafile = "data/repeated_attempts.csv"
    if len(sys.argv) > 2:
        datafile = sys.argv[2]
    data = read_combined_data(datafile)
    ## TODO nejak hezceji ?    
    if sys.argv[1] == "sensiBKT":
        sensi_analysis(data, BKT, [0.3, 0.5, 0.6, 0.7 ])
    elif sys.argv[1] == "sensiELO":
        sensi_analysis(data, EloBasic, [0.5, 0.75, 1.0,  1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0])
    elif sys.argv[1] == "sensiELOtime":
        sensi_analysis(data, EloTime, [ 0, 40, 80, 120, 160, 200, 240 ])
    elif sys.argv[1] == "sensiELOtime2":
        sensi_analysis(data, EloTime, [ 0.5, 1.0, 1.5, 2.0, 2.5, 3.0 ], "alpha")
    elif sys.argv[1] == "compare1":
        compare_models(data, [ BKT(0.3), EloBasic(1.0), BKT_Elo() ] )
    elif sys.argv[1] == "compare2":
        compare_models(data, [ BKT(0.3), EloBasic(1.0), EloTime(0.3, 0.5), TimeDecay(0.1) ] )
    elif sys.argv[1] == "compare3":
        compare_models(data, [ EloBasic(1.2), EloTime(100, 1.5) ] )
    else:
        print "Dont know what", sys.argv[1], "means."
    
if __name__ == "__main__":
    main()
        
