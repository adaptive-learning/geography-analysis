#!/usr/bin/python -u

from models_prior_knowledge import *
from geography_common import *
import pylab as plt
import sys

################ analysis of estimates ############

def compare_model_estimates(data, m1, m2):
    print "Comparing model estimates"
    m1.process_data(data)
    print str(m1), "done"
    m2.process_data(data)
    print str(m2), "done"
    scatter_dicts_with_same_keys(m1.D, m2.D)
    plt.xlabel(str(m1) + " estimate")
    plt.ylabel(str(m2) + " estimate")
    plt.savefig("results/elo-rasch-estimates.svg")
    plt.show()

def compare_estimates_two_halves(data, Model):
    m1 = Model()
    m2 = Model()
    print "starting"
    data1, data2 = split_data_user_level(data)
    print "data split"
    m1.process_data(data1)
    print "m1 ok"
    m2.process_data(data2)
    print "m2 ok"
    scatter_dicts_with_same_keys(m1.D, m2.D)
    plt.figure()
    attempts, diffs = [], []
    for p in m1.D:
        if p in m2.D:
            attempts.append( m1.place_attempts[p] + m2.place_attempts[p] )
            diffs.append( abs(m1.D[p] - m2.D[p]) )
    plt.scatter(attempts, diffs)
    plt.xscale('log')
    plt.show()
    
#[ 178, 63, 196, 211, 67, 97,118 ]    
def history_plots(data, states, selection = [ 222, 150, 119, 212, 107, 165 ]):
    m = EloModel()
    m.process_data(data)
    leg = []
    for place in selection:
        if place in m.history:
            plt.plot(m.history[place])
            leg.append(states[place])
    plt.xlim([0,350])
    plt.legend(leg, loc=2)
    plt.savefig("results/elo-history.svg")
    plt.show()

    
############# analysis of predictions ###################
    
def compare_model_predictions(data):
    metrics = [ ("AUC", log_auc), ("RMSE", log_rmse) ]  # ("MAE", log_mae)
 
    models = [ ConstantModel(0.9), GlobalRatioModel(), SuccessRatePlaceModel(),
               EloModel(0.5,0), EloModel(), EloModel(4.0, 0.5) ]

    logger = MultipleRunLogger(1)    
    for m in models:
        m.process_data(data)
        for (metric_name, metric) in metrics:                
            logger.log(str(m), metric_name, metric(m.log))
    logger.print_table()
          
def elo_ufun_sensi_analysis(data):
    loggerR = MultipleRunLogger(1)
    loggerA = MultipleRunLogger(1)
    
    for a in [ 0.5, 0.75, 1.0, 1.25, 1.5, 1.75 ]:
        for b in [ 0.02, 0.05, 0.1, 0.15, 0.2 ]:
            m = EloModel(a, b)
#            m = EloModel(1.25, 0.1, a, b)
            m.process_data(data)
            loggerR.log(`a`, `b`,  log_rmse(m.log))
            loggerA.log(`a`, `b`,  log_auc(m.log))
    print "RMSE"
    loggerR.print_table(print_best = 2)
    plt.imshow(loggerR.get_table())
    print "\nAUC"
    loggerA.print_table(print_best = 1)
    plt.figure()
    plt.imshow(loggerA.get_table())
    plt.show()    

    
################## likelihood test ##################33

def get_avgloglikelihoods(data, model):
    avg_ll = {}
    solved = {}
    for student in data.user.unique():
        g = model.G.get(student, 0)
        sum_ll = 0.0
        solved[student] = 0
        for i in data[data.user==student].index:            
            d = model.D.get(data.place[i], 0)
            pred = sigmoid(g-d)
            sum_ll += math.log(1-abs(data.correct[i] - pred))
            solved[student] += 1
            # if g > 2.5:
            #     print student, g, d, pred, data.correct[i], math.log(1-abs(data.correct[i] - pred))
        avg_ll[student] = sum_ll / solved[student]
    return (avg_ll, solved)

def sorted_values(d):
    k = d.keys()
    k.sort()
    return [ d[i] for i in k ]

def likelihood_test(data):    
#    m = Rasch()
    m = EloModel()
    m.process_data(data)
    (avg_ll, solved) = get_avgloglikelihoods(data, m)
    plt.scatter(sorted_values(solved), sorted_values(avg_ll))
    plt.figure()
    plt.scatter(sorted_values(m.G), sorted_values(avg_ll))
    plt.show()

def on_cont(places, onmap, continents):
    out = []
    for p in places:
        ok = False
        for c in continents:
            if p in onmap[c]: ok = True
        out.append(ok)
    return out

def subskills(data):
    onmap = process_placerelation()
    states, _ = process_states()
    cont1 = [ 230, 227]
    cont2 = [  231, 228, 229 ]
    data1 = data[ on_cont(data.place, onmap, cont1) ]
    data2 = data[ on_cont(data.place, onmap, cont2) ]
    m1, m2 = EloModel(), EloModel()
    print "data read"
    m1.process_data(data1)
    print "m1 ok"
    m2.process_data(data2)
    print "m2 ok"
    skills = [] 
    for s in m1.G.keys():
        if not s in m2.G: continue
        if m1.student_attempts[s] < 15: continue
        if m2.student_attempts[s] < 15: continue
        skills.append((m1.G[s], m2.G[s]))
    print "spearman", round(spearman(*zip(*skills)),2)
    print "pearson", round(pearson(*zip(*skills)),2)
    plt.scatter(*zip(*skills))
    plt.xlim([-3.5, 3.5])
    plt.ylim([-3.5, 3.5])
    plt.xlabel(",".join([states[c] for c in cont1]))
    plt.ylabel(",".join([states[c] for c in cont2]))
    plt.savefig("results/subskills.svg")
    plt.show()
    
    
######################### MAIN ######################

def main():
    if len(sys.argv) < 2:
        print "Gimme command"
        return 
    states, codes = process_states()
    datafile = "data/data_first.csv"
    if len(sys.argv) > 2:
        datafile = sys.argv[2]
    data = read_data(datafile)
    ## TODO nejak hezceji ?
    if sys.argv[1] == "compare1":
        compare_model_estimates(data, Rasch(), EloModel())
    elif sys.argv[1] == "compare2":
        compare_model_estimates(data, SuccessRateModel(), EloModel())
    elif sys.argv[1] == "compare_halves":
        compare_estimates_two_halves(data, EloModel)
    elif sys.argv[1] == "predictions":
        compare_model_predictions(data)        
    elif sys.argv[1] == "history":
        history_plots(data, states)    
    elif sys.argv[1] == "sensi":
        elo_ufun_sensi_analysis(data)
    elif sys.argv[1] == "likelihood":
        likelihood_test(data)
    elif sys.argv[1] == "subskills":
        subskills(data)
    else:
        print "Dont know what", sys.argv[1], "means."
        
if __name__ == "__main__":
    main()
