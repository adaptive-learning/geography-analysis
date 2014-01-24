#!/usr/bin/python -u

from models_prior_knowledge import *
from geography_common import *
import pylab as plt
import sys

################ analysis of estimates ############

def compare_model_estimates(data, m1, m2):
    print "Comparing model estimates"
    m1.process_data(data)
    print m1.name, "done"
    m2.process_data(data)
    print m2.name, "done"
    scatter_dicts_with_same_keys(m1.D, m2.D)
    plt.xlabel(m1.name + " estimate")
    plt.ylabel(m2.name + " estimate")
    plt.show()

def history_plots(data, states, selection = [ 178, 63, 196, 211, 67, 97,118 ]):
    m = EloModel(1.0, 0.1)
    m.process_data(data)
    leg = []
    for place in selection:
        if place in m.history:
            plt.plot(m.history[place])
            leg.append(states[place])
    plt.xlim([0,300])
    plt.legend(leg)
    plt.show()

############# analysis of predictions ###################
    
def compare_model_predictions(data):
    metrics = [ ("AUC", log_auc), ("RMSE", log_rmse) ]  # ("MAE", log_mae)
 
    models = [ ConstantModel(0.9), GlobalRatioModel(), SuccessRatePlaceModel(),
               EloModel(0.5,0), EloModel(1, 0.2), EloModel(4.0, 0.5) ]

    logger = MultipleRunLogger(1)    
    for m in models:
        m.process_data(data)
        for (metric_name, metric) in metrics:                
            logger.log(str(m), metric_name, metric(m.log))
    logger.print_table()
          
def elo_ufun_sensi_analysis(data):
    loggerR = MultipleRunLogger(1)
    loggerA = MultipleRunLogger(1)
    
    for a in [ 0.5, 1.0, 1.5, 2.0, 3.0, 4.0 ]:
        for b in [ 0, 0.2, 0.4, 0.6, 0.5, 0.8, 1.0]:
            m = EloModel(a, b)
            m.process_data(data)
            loggerR.log(`a`, `b`,  log_rmse(m.log))
            loggerA.log(`a`, `b`,  log_auc(m.log))
    print "RMSE"
    loggerR.print_table(print_best = 2)
    print "\nAUC"
    loggerA.print_table(print_best = 1)    
    

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
        compare_model_estimates(data, Rasch(), EloModel(1, 0.1))
    elif sys.argv[1] == "compare2":
        compare_model_estimates(data, SuccessRateModel(), EloModel(1, 0.1))
    elif sys.argv[1] == "predictions":
        compare_model_predictions(data)        
    elif sys.argv[1] == "history":
        history_plots(data, states)    
    elif sys.argv[1] == "sensi":
        elo_ufun_sensi_analysis(data)
    elif sys.argv[1] == "likelihood":
        likelihood_test(data)
    else:
        print "Dont know what", sys.argv[1], "means."
        
if __name__ == "__main__":
    main()