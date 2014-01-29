from geography_common import *

# models of current knowledge based on sequence of repeated attempts

class ModelC:

    def __init__(self):
        pass

    def process_data(self, data, verbose = 0):
        self.log = []
        self.logmap = {}
        self.verbose = verbose
        for s, p in data.keys():
            # save context
            self.sp = (s,p)
            self.i = 1
            if verbose:
                print "\n", s, p
            self.process_sequence(
                data[s,p]['initskill'],
                data[s,p]['ans'],
                data[s,p]['qtype'],
                data[s,p]['time']
                )

    def save_to_log(self, pred, ans):
        self.log.append((pred, ans))
        self.logmap[self.sp[0], self.sp[1], self.i] = (pred, ans)
        self.i += 1
        if self.verbose:
            print "\t", ans, pred
            
    # implementuji dilci modely, vraci seznam dvojic (pred, ans)
    def process_sequence(self, initskill, ans, qtype, time):
        pass 


class BKT(ModelC):

    def __init__(self, plearn = 0.6):
        self.plearn = plearn

    def __str__(self):
        return "BKT " + `self.plearn` 
        
    def process_sequence(self, initskill, ans, qtype, time):
        P = sigmoid(initskill)
        for i in range(len(ans)):
            qt = qtype[i]
            pred = P*(1-slip(qt)) + (1-P)*guess(qt)
            if i > 0: self.save_to_log(pred, ans[i])
            if ans[i] == 1:
                P = P*(1-slip(qt)) / (P*(1-slip(qt)) + (1-P)*guess(qt))
            else:
                P = P*slip(qt) / (P*slip(qt) + (1-P)*(1-guess(qt)))
            P = P + (1-P) * self.plearn
                        
class Elo(ModelC):

    def __init__(self, alpha = 2.0, time_effect = 160.0):
        self.alpha = alpha
        self.time_effect = time_effect

    def __str__(self):
        return  "Elo " + `self.alpha` + ' '+`self.time_effect`
        
    def process_sequence(self, initskill, ans, qtype, time):
        skill = initskill
        skill += self.alpha * (ans[0] - sigmoid_shift(skill, random_factor(qtype[0])))
        for i in range(1, len(ans)):
            timedif = max(0, time[i]-time[i-1])
            local_skill = skill + float(self.time_effect) / ( 1 + timedif )
            pred = sigmoid_shift(local_skill, random_factor(qtype[i]))
            self.save_to_log(pred, ans[i])
            skill += self.alpha * (ans[i] - pred)

class EloBasic(Elo):
    def __init__(self, alpha = 2.0):
        Elo.__init__(self, alpha, 0)

class PFA(ModelC): 

    def __init__(self, Kgood = 1.0, Kbad = 0.8, time_effect = 160):    
#    def __init__(self, Kgood = 0.8, Kbad = 0.4, time_effect = 60):
        self.Kgood = Kgood
        self.Kbad = Kbad
        self.time_effect = time_effect

    def __str__(self):
        return  "PFA " + `self.Kgood` + " " + `self.Kbad` + " " + `self.time_effect`
        
    def process_sequence(self, initskill, ans, qtype, time):
        skill = initskill
        for i in range(len(ans)):
            timedif = max(0, time[i]-time[i-1])
            local_skill = skill + float(self.time_effect) / ( 1 + timedif )
            pred = sigmoid_shift(local_skill, random_factor(qtype[i]))
            if i > 0: self.save_to_log(pred, ans[i])
            if ans[i]: skill += self.Kgood
            else: skill += self.Kbad

########## outdated, probably poor model, not worth further extensions
            
class TimeDecay(ModelC):

    def __init__(self, k = 0.3, decay_fun = exp_fun):
        self.decay_fun = decay_fun(k)
        self.name = "TimeDecay " + `k`

    def __str__(self):
        return self.name
        
    # extra naive
    def process_sequence(self, initskill, ans, qtype, time):
        padding = 5
        tmp = [ sigmoid(initskill) ] * padding
        tmp.extend(ans)
        for i in range(len(ans)):
            if i > 0:
                rf = random_factor(qtype[i])
                pred = rf + (1-rf) * weighted_mean(tmp, padding + i, self.decay_fun)
                self.save_to_log(pred, ans[i])


            
