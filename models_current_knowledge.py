from geography_common import *

# models of current knowledge based on sequence of repeated attempts

RTIME_MEAN = 11.84

class ModelC:

    def __init__(self):
        pass

    def process_data_place(self, data, p):
        for s in data[p].keys():
            self.sp = (s,p)
            self.i = 1
            if self.verbose: print "\n", s, p
            self.process_sequence(
                data[p][s]['initskill'],
                data[p][s]['ans'],
                data[p][s]['qtype'],
                data[p][s]['time'],
                data[p][s]['rtime'])
    
    def process_data(self, data, place = None, verbose = 0):
        self.log = []
        self.logmap = {}
        self.verbose = verbose
        if place == None:
            for p in data.keys():
                self.process_data_place(data,p)
        else:
            self.process_data_place(data, place)                

    def save_to_log(self, pred, ans):
        self.log.append((pred, ans))
        self.logmap[self.sp[0], self.sp[1], self.i] = (pred, ans)
        self.i += 1
        if self.verbose:
            print "\t", ans, pred
            
    # implementuji dilci modely, vraci seznam dvojic (pred, ans)
    def process_sequence(self, initskill, ans, qtype, time, rtime):
        pass 


class BKT(ModelC):

    def __init__(self, plearn = 0.6, pslip = 0.06, pguess10 = 0.12):
        self.plearn = plearn
        self.pslip = pslip
        self.pguess10 = pguess10

    def __str__(self):
        return "BKT " + `self.plearn` + ' ' + `self.pslip`

    def guess(self, qtype):
        if qtype == 10: return self.pguess10
        return 1.0 / (qtype - 10*(qtype//10))
    
    def process_sequence(self, initskill, ans, qtype, time, rtime):
        P = sigmoid(initskill)
        for i in range(len(ans)):
            qt = qtype[i]
            pred = P*(1-self.pslip) + (1-P)*self.guess(qt)
            if i > 0: self.save_to_log(pred, ans[i])
            if ans[i] == 1:
                P = P*(1-self.pslip) / (P*(1-self.pslip) + (1-P)*self.guess(qt))
            else:
                P = P*self.pslip / (P*self.pslip + (1-P)*(1-self.guess(qt)))
            P = P + (1-P) * self.plearn

class PFAplus(ModelC): 

    def __init__(self, Kgood = 3.4, Kbad = -0.2, time_effect = 80, rtime_effect = 0.25, use_prob = 1):
        self.use_prob = use_prob
        self.Kgood = Kgood
        self.Kbad = Kbad
        self.time_effect = time_effect
        self.rtime_effect = rtime_effect

    def __str__(self):
        return  "PFAplus(" + ",".join(map(str,[self.use_prob, self.Kgood, self.Kbad, self.time_effect,self.rtime_effect])) + ")"
        
    def process_sequence(self, initskill, ans, qtype, time, rtime):
        skill = initskill
        for i in range(len(ans)):
            local_skill = skill
            if i > 0:
                timedif = max(0, time[i]-time[i-1])
                local_skill += float(self.time_effect) / ( 1 + timedif )
            pred = sigmoid_shift(local_skill, random_factor(qtype[i]))
            
            if i > 0: self.save_to_log(pred, ans[i])
            
            if ans[i]:
                K = self.Kgood
                K = K * (1 + (RTIME_MEAN - rtime[i]) * self.rtime_effect)
                if self.use_prob:
                    K = K * (1-pred)
            else:
                K = self.Kbad
                if self.use_prob:
                    K = K * pred
            skill += K            
                
        
class PFAtime(PFAplus): 

    def __init__(self, Kgood = 0.75, Kbad = 0.2, time_effect = 90, rtime_effect = 0.3):
        PFAplus.__init__(self, Kgood, Kbad, time_effect, rtime_effect, 0)

    def __str__(self):
        return  "PFAtime(" + ",".join(map(str,[self.use_prob, self.Kgood, self.Kbad, self.time_effect,self.rtime_effect])) + ")"

class PFAbasic(PFAplus): 

    def __init__(self, Kgood = 0.9, Kbad = 0.6):
        PFAplus.__init__(self, Kgood, Kbad, 0, 0, 0)

    def __str__(self):
        return  "PFAbasic(" + ",".join(map(str,[self.use_prob, self.Kgood])) + ")"

class PFAprob(PFAplus): 

    def __init__(self, Kgood = 3.4, Kbad = 0.2):
        PFAplus.__init__(self, Kgood, Kbad, 0, 0, 1)

    def __str__(self):
        return  "PFAprob(" + ",".join(map(str,[self.use_prob, self.Kgood])) + ")"
    
            
########## outdated, probably poor model, not worth further extensions
###### hmmm.... with rmse2 quite good...
            
class TimeDecay(ModelC):

    def __init__(self, k = 0.3, decay_fun = exp_fun):
        self.decay_fun = decay_fun(k)
        self.name = "TimeDecay " + `k`

    def __str__(self):
        return self.name
        
    # extra naive
    def process_sequence(self, initskill, ans, qtype, time, rtime):
        padding = 5
        tmp = [ sigmoid(initskill) ] * padding
        tmp.extend(ans)
        for i in range(len(ans)):
            if i > 0:
                rf = random_factor(qtype[i])
                pred = rf + (1-rf) * weighted_mean(tmp, padding + i, self.decay_fun)
                self.save_to_log(pred, ans[i])


############ outdated .... out of favour
                
class Elo(ModelC):

    def __init__(self, alpha = 2.0, time_effect = 160.0, rtime_effect = 0):
        self.alpha = alpha
        self.time_effect = time_effect
        self.rtime_effect = rtime_effect

    def __str__(self):
        return  "Elo " + `self.alpha` + ' '+`self.time_effect` + ' '+ `self.rtime_effect`
        
    def process_sequence(self, initskill, ans, qtype, time, rtime):
        skill = initskill
        skill += self.alpha * (ans[0] - sigmoid_shift(skill, random_factor(qtype[0])))
        for i in range(1, len(ans)):
            timedif = max(0, time[i]-time[i-1])
            local_skill = skill + float(self.time_effect) / ( 1 + timedif )
            pred = sigmoid_shift(local_skill, random_factor(qtype[i]))
            self.save_to_log(pred, ans[i])
            
            alpha = self.alpha * (1 + (RTIME_MEAN - rtime[i]) * self.rtime_effect)
            skill += alpha * (ans[i] - pred)
            
class EloBasic(Elo):
    def __init__(self, alpha = 2.0):
        Elo.__init__(self, alpha, 0)
            
