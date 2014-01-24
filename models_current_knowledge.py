from geography_common import *

# models of current knowledge based on sequence of repeated attempts

class ModelC:

    def __init__(self):
        pass

    def process_data(self, data, verbose = 0):
        self.log = []
        self.verbose = verbose
        for s, p in data.keys():
            self.process_sequence(
                data[s,p]['initskill'],
                data[s,p]['ans'],
                data[s,p]['qtype'],
                data[s,p]['time']
                )
            if verbose:
                print "\n", s, p

    # todo - tady si pripadne pamatovat kontext a pridelat logmap
    def save_to_log(self, pred, ans):
        self.log.append((pred, ans))
        if self.verbose:
            print pred, ans, ";", 
            
    # implementuji dilci modely, vraci seznam dvojic (pred, ans)
    def process_sequence(self, initskill, ans, qtype, time):
        pass 


class BKT(ModelC):

    def __init__(self, plearn = 0.3):
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
            
class EloBasic(ModelC):

    def __init__(self, alpha = 0.5):
        self.alpha = alpha

    def __str__(self):
        return  "EloBasic " + `self.alpha`
        
    def process_sequence(self, initskill, ans, qtype, time):
        skill = initskill
        for i in range(len(ans)):
            pred = sigmoid_shift(skill, random_factor(qtype[i]))
            if i > 0: self.save_to_log(pred, ans[i])
            skill += self.alpha * (ans[i] - pred)

class EloTime(ModelC):

    def __init__(self, time_effect = 1.0, alpha = 0.5):
        self.alpha = alpha
        self.time_effect = time_effect

    def __str__(self):
        return  "EloTime " + `self.alpha` + ' '+`self.time_effect`
        
    def process_sequence(self, initskill, ans, qtype, time):
        skill = initskill
        for i in range(len(ans)):
            local_skill = skill
            if i > 0:
                timedif = (time[i]-time[i-1]) / 100
                local_skill += self.time_effect*math.exp(-timedif)
            pred = sigmoid_shift(local_skill, random_factor(qtype[i]))
            if i > 0: self.save_to_log(pred, ans[i])
            skill += self.alpha * (ans[i] - pred)            
                        
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


# jednoducha kombinace - oboje zaraz a sectu
# cut&paste hack ... upravit nejak, aby ty kombinace sly delat snadneji?
class BKT_Elo(ModelC):

    def __init__(self, plearn = 0.3, alpha = 1.0):
        self.plearn = plearn
        self.alpha = alpha

    def __str__(self):
        return "BKT_Elo 0.5 " + `self.plearn` + ' ' + `self.alpha`
        
    def process_sequence(self, initskill, ans, qtype, time):
        P = sigmoid(initskill)
        skill = initskill
        for i in range(len(ans)):
            qt = qtype[i]
            pred = P*(1-slip(qt)) + (1-P)*guess(qt)
            pred2 = sigmoid_shift(skill, random_factor(qtype[i]))
            if i > 0: self.save_to_log((pred + pred2)/2, ans[i])            
            skill += self.alpha * (ans[i] - pred2)
            if ans[i] == 1:
                P = P*(1-slip(qt)) / (P*(1-slip(qt)) + (1-P)*guess(qt))
            else:
                P = P*slip(qt) / (P*slip(qt) + (1-P)*(1-guess(qt)))
            P = P + (1-P) * self.plearn
            