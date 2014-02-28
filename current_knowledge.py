#!/usr/bin/python

from geography_common import *
from models_current_knowledge import *
import sys

## needs cleaning...
## parameter search needs improving

def sensi_analysis(data, Model, values, par_name = None, do_plot = 1, verbose=1, place = None):
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
        m.process_data(data, place)
        r = log_rmse(m.log) 
        if verbose: print "\tRMSE", round(r,4)
        rmses.append(r)
        if rmses[i] < rmses[best]: best = i
    print "Best par value:", values[best]
    if do_plot:
        plt.plot(values, rmses)
        plt.show()

def sensi_analysis_grid(data, Model, parameters):
    best = float("inf")        
    bestparam = None
    for param in parameters:
        m = Model(**param)
        m.process_data(data)
        r = log_rmse(m.log)
        print str(param).ljust(30), round(r,3)        
        if r < best:
            best = r
            bestparam = param
    print "Best:", best
    print bestparam    

def sensi_analysis_grid2d(data, Model, parameters):
    logger = MultipleRunLogger(1)
    pars = parameters[0].keys()
    assert len(pars) == 2  # plus some hidden assumptions...
    for param in parameters:
        m = Model(**param)
        m.process_data(data)
        logger.log(`param[pars[0]]`, `param[pars[1]]`, log_rmse(m.log))
    logger.print_table(print_best = 2)
    plt.imshow(logger.get_table())
    plt.show()
    
def sensi_analysis_gridPFA(data):    
    parameters = [ { "Kgood": Kg, "Kbad": Kb }
                   for Kg in [ 0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4 ]
                   for Kb in [-0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6]
                  ]
    sensi_analysis_grid(data, PFAbasic, parameters)

def sensi_analysis_gridPFA2(data):    
    # parameters = [ { "Kgood": Kg, "Kbad": Kb }
    #                for Kg in [ 0.7, 0.8, 0.9, 1.0, 1.1 ]
    #                for Kb in [ 0.3, 0.4, 0.5, 0.6, 0.7]
    #               ]
    # sensi_analysis_grid2d(data, PFAbasic, parameters)
    parameters = [ { "Kgood": Kg, "Kbad": Kb }
                   for Kg in [ 3.0, 3.2, 3.3, 3.4, 3.5 ]
                   for Kb in [ -0.4, -0.3, -0.2, -0.1, 0]
                  ]
    sensi_analysis_grid2d(data, PFAplus, parameters)

    
def sensi_analysis_per_place(data, Model, parameters, limit=140):
    states, _ = process_states()
    D = read_dict("data/raschD.csv")
    for place in data:
        if len(data[place].keys()) < limit: continue
        best = float("inf")        
        bestparam = None
        for param in parameters:
            m = Model(**param)
            m.process_data(data, place)
            r = log_rmse(m.log)
            if r < best:
                best = r
                bestparam = param
        print states[place][:15].ljust(18).encode("UTF8"),\
            round(sigmoid(-D.get(place,0)), 2),"\t",\
            bestparam

def PFA_sensi_analysis_per_place(data):
    parameters = [ { "Kgood": Kg, "Kbad": Kb }
                   for Kg in [ 0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4 ]
                   for Kb in [-0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6]
                  ]    
    sensi_analysis_per_place(data, PFAbasic, parameters)        
    
def Elo_sensi_analysis_per_place(data):
    parameters = [ { "alpha": a }
                   for a in [ 0.5, 1.0, 1.5, 2.0, 2.5, 3.0 ]
                  ]    
    sensi_analysis_per_place(data, Elo, parameters)        

def PFAplus_sensi_analysis_per_place(data):
    parameters = [ { "Kgood": Kg, "Kbad": Kb }
                   for Kg in [ 2, 2.5, 3, 3.5, 4 ]
                   for Kb in [ -0.2, 0, 0.2, 0.4, 0.6 ]
                  ]    
    sensi_analysis_per_place(data, PFAplus, parameters)            

def PFAplus_sensi_analysis_per_place_split(data):
    parameters = [ { "Kgood": Kg, "Kbad": Kb }
                   for Kg in [ 2, 2.5, 3, 3.5, 4 ]
                   for Kb in [ -0.4, -0.2, 0, 0.2, 0.4 ]
                  ]
    data1, data2 = split_combined_data_user_level(data)
    print "data1"
    sensi_analysis_per_place(data1, PFAplus, parameters, 80)        
    print "data2"
    sensi_analysis_per_place(data2, PFAplus, parameters, 80)        
    
def compare_models(data, models, textable = 1, roccurves = 0):
    leg = []
    for m in models:
        leg.append(str(m))
        m.process_data(data)
        if textable:
            print str(m), "&", round(log_rmse(m.log), 3), "&", round(log_LL(m.log), 3), "&", round(log_auc(m.log), 3), r"\\"
        else:
            print str(m).ljust(30),
            print "\tRMSE    \t", round(log_rmse(m.log), 3), 
            print "\tLL\t", round(log_LL(m.log), 3),
            print "\tAUC    \t", round(log_auc(m.log), 3)
            if roccurves: do_roc(*zip(*m.log))
    if roccurves:
        plt.legend(leg, loc = 4)
        plt.show()

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

def run_sensi_analysis(data, choices):
    options = {
        'BKT': [ BKT, [0.2, 0.3, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7, 0.8 ] ],
        'BKTs': [ BKT, [0.03, 0.04, 0.05,  0.06, 0.07,  0.08, 0.09 ], "pslip" ],
        'BKTg': [ BKT, [ 0.05,  0.1, 0.12, 0.15, 0.2, 0.25 ], "pguess10" ],
        'decay': [ TimeDecay, [0, 0.05, 0.1, 0.2, 0.3, 0.4 ] ],
        'Elo': [ EloBasic, [0.75, 1.0,  1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75] ],
        'Elot': [ Elo, [ 0, 40, 80, 120, 160, 200, 240 ], "time_effect" ],
        'EloRt': [ Elo, [ 0, 0.2, 0.4, 0.6, 0.8, 1.0 ], "rtime_effect" ],
        'Eloa': [ Elo, [ 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0 ], "alpha" ],
        'PFAg': [ PFA, [ 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6], "Kgood"],
        'PFA+g': [ PFAplus, [ 2, 2.5, 3, 3.5, 4, 5], "Kgood"],
        'PFA+b': [ PFAplus, [ -0.6, -0.4, -0.3, -0.2, -0.1, 0, 0.2 ], "Kbad"],
        'PFA+t': [ PFAplus, [ 0, 40, 80, 120, 160, 200, 240 ], "time_effect" ],
        'PFA+r': [ PFAplus, [ 0, 0.1, 0.2, 0.3, 0.4 ],  "rtime_effect" ],
        'PFAb': [ PFA, [ -0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8, 1.0], "Kbad"],
        'PFAt': [ PFA, [ 0, 40, 60, 80, 120, 160 ], "time_effect"],
        'PFArt': [ PFA, [ -0.4, -0.2, 0, 0.2, 0.4, 0.6  ], "rtime_effect"]
        }
    if len(choices) == 0:
        for c in options.keys():
            print "\n",c
            sensi_analysis(data, *options[c], do_plot=0, verbose=0)
    else:
        choice = choices[0]
        if len(choices) > 1: place = int(choices[1])
        else: place = None
        sensi_analysis(data, *options[choice], place=place)

def run_sensi_analysis2(data, model, param):
    modelmap = { 'PFAbasic': PFAbasic, 'PFAtime': PFAtime,
                 'PFAprob': PFAprob, 'PFAplus': PFAplus }
    paramlist = {
#        'Kgood': [  0.6, 0.7, 0.75, 0.8, 0.9, 1.0, 1.1, 1.2],
        'Kgood': [  2.8, 2.9, 3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6], # hack
        'Kbad': [ -0.6, -0.4, -0.3, -0.2, -0.1, 0, 0.2, 0.4, 0.5, 0.6, 0.8],
        'time_effect': [ 20, 40, 60, 80, 100, 120, 160, 200, 240 ],
        'rtime_effect': [ 0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4 ] }
    sensi_analysis(data, modelmap[model], paramlist[param], param)
    

def run_model_comparison(data, choices):
    options = {
        '0': [ BKT(), PFAbasic(), PFAtime(), PFAprob(), PFAplus()  ]
        }
    if len(choices) == 0 or not choices[0] in options:
        choices = [ '0' ]
    compare_models(data, options[choices[0]])
            
def main():
    if len(sys.argv) < 2:
        print "Gimme command"
        return
    datafile = "data/repeated_attempts.csv"
    data = read_combined_data(datafile)
    if sys.argv[1] == "sensi":
        run_sensi_analysis(data, sys.argv[2:]) 
    elif sys.argv[1] == "sensi2":
        run_sensi_analysis2(data, *sys.argv[2:]) 
    elif sys.argv[1] == "gridPFA":
        sensi_analysis_gridPFA(data) 
    elif sys.argv[1] == "grid2":
        sensi_analysis_gridPFA2(data) 
    elif sys.argv[1] == "placesPFA":
        PFA_sensi_analysis_per_place(data) 
    elif sys.argv[1] == "placesPFA+":
#        PFAplus_sensi_analysis_per_place(data)
        PFAplus_sensi_analysis_per_place_split(data)                
    elif sys.argv[1] == "placesElo":
        Elo_sensi_analysis_per_place(data) 
    elif sys.argv[1] == "compare":
        run_model_comparison(data, sys.argv[2:])
    elif sys.argv[1] == "show":
#        show_predictions(data, PFA(), Elo()  )        
        show_predictions(data, Elo(), Elo(rtime_effect = 0.5)  )        
    elif sys.argv[1] == "classes":
        show_prediction_classes(data, [ PFA(), Elo(), PFAplus(), BKT()])
    else:
        print "Dont know what", sys.argv[1], "means."
    
if __name__ == "__main__":
    main()
        
############################ outdated
########## for the moment ...
    
# outdated... now I prefer to use RMSE... maybe
def sensi_analysis_roc(data, Model, values):
    for pval in values:
        print "par value", pval
        m = Model(pval)
        m.process_data(data)
        do_roc(*zip(*m.log))
    plt.show()
    
