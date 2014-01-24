from geography_common import *

# models of prior knowledge -- before the first attempt

class ModelP:

    def __init__(self):
        self.student_attempts = {}
        self.place_attempts = {}
    
    # report_predictions -- compatibility with Rasch
    # ale metodicky divny, asi smazat
    def process_data(self, data, verbose=0, report_predictions=1):
        self.log = []  # the log contains results only from last call (presumably test)
        for i in data.index:
            self.student_attempts[data.user[i]] = self.student_attempts.get(data.user[i], 0) + 1
            self.place_attempts[data.place[i]] = self.place_attempts.get(data.place[i], 0) + 1
            pred = self.process_data_point(data.user[i], data.place[i], data.correct[i], data.type[i])
            if verbose: print data.user[i], data.place[i], data.correct[i], pred
            self.log.append((pred, data.correct[i]))

    def process_data_point(self, student, place, correct, qtype):
        pass    

class ConstantModel(ModelP):

    def __init__(self, k):
        ModelP.__init__(self)
        self.prediction = k

    def __str__(self):
        return "Constant " + `self.prediction`
        
    def process_data_point(self, student, place, correct, qtype):
        return self.prediction

class GlobalRatioModel(ModelP):

    def __init__(self):
        ModelP.__init__(self)
        self.correct = 0
        self.total = 0.0

    def __str__(self):
        return "GlobalRatio"            
        
    def process_data_point(self, student, place, correct, qtype):
        if self.total == 0:  prediction = 0.5
        else: prediction = float(self.correct) / self.total
        if correct: self.correct += 1
        self.total += 1
        return prediction


class SuccessRatePlaceModel(ModelP): # simple baseline - only for places

    def __init__(self):
        ModelP.__init__(self)
        self.place_correct = {}

    def __str__(self):
        return "SuccessRatePlace"    
        
    def process_data_point(self, student, place, correct, qtype):
        if not place in self.place_correct:
            self.place_correct[place] = correct
            return 0.5
        prediction = float(self.place_correct[place]) / self.place_attempts[place]
        if correct:
            self.place_correct[place] += 1
        return prediction


class SuccessRateModel(ModelP):

    def __init__(self):
        ModelP.__init__(self)
        self.place_correct = {}   
        self.student_correct = {}
        self.D = {}

    def __str__(self):
        return "SuccessRate"    
        
    def process_data_point(self, student, place, correct, qtype):
        
        if not place in self.place_correct:
            place_rate = 0.5
            self.place_correct[place] = correct
        else:
            place_rate = float(self.place_correct[place]) / self.place_attempts[place]
            if correct:
                self.place_correct[place] += 1
        self.D[place] = float(self.place_correct[place]) / self.place_attempts[place] # jen pro srovnani s jinymi modely

        if not student in self.student_correct:
            student_rate = 0.5
            self.student_correct[student] = correct
        else:
            student_rate = float(self.student_correct[student]) / self.student_attempts[student]
            if correct:
                self.student_correct[student] += 1

        # pred = arith. mean of place success rate and student success rate
        prediction = (place_rate + student_rate) / 2.0
        return prediction
    
class EloModel(ModelP):

    def __init__(self, alpha = 4.0, beta = 0.5):
        ModelP.__init__(self)
        self.name = "Elo "+`alpha`+" "+`beta`        
        self.ufun = lambda x: alpha / (1 + beta * x)
        self.G = {}
        self.D = {}
        self.history = {} # places

    def __str__(self):
        return self.name
        
    def process_data_point(self, student, place, correct, qtype):
        if not student in self.G:
            self.G[student] = 0
        if not place in self.D:
            self.D[place] = 0
            self.history[place] = [0]
        prediction = sigmoid_shift(self.G[student] - self.D[place], random_factor(qtype))
        dif = (correct - prediction)
        self.G[student] = self.G[student] + self.ufun(self.student_attempts[student]) * dif
        self.D[place] = self.D[place] - self.ufun(self.place_attempts[place]) * dif
        self.history[place].append(self.D[place])
        return prediction

###### Rasch model #################

class Rasch:

    def __init__(self):
        self.G = {}
        self.D = {}

    def __str__(self):
        return "Rasch"    
        
    def process_data(self, data, verbose = 0, report_predictions = 0, use_only10=0, it = 2):
        if report_predictions:
            self.log = []
            self.do_predictions(data)

        for _ in range(it):
            self.estimateD(data)
            self.estimateG(data)

    # to je stejne metodicky blbost asi smazat
    def do_predictions(self, data):
        for i in data.index:
            pred = sigmoid_shift(self.G.get(data.user[i],0) - self.D.get(data.place[i],0), random_factor(data.type[i]))
            self.log.append((pred, data.correct[i]))

    def estimateD(self, data):
        for place in data.place.unique():
            d = self.D.get(place,0)
            for _ in range(3): # 3 iterace newtonovy metody, pocet iteraci by nemel byt zasadni
                sumc, sump, sump1p = 0,0,0
                for i in data[data.place==place].index:
                    sumc += data.correct[i]
                    p = sigmoid_shift(self.G.get(data.user[i],0) - d, random_factor(data.type[i]))
                    sump += p
                    sump1p += p*(1-p)
                if sump1p:
                    d = d + (sump - sumc) / sump1p # newtonova metoda, vzorec z knihy
                    d = max(min(d, 5), -5)  # drzime v intervalu -5, 5
            self.D[place] = d
#            print place, self.D[place]

    def estimateG(self, data):
        for student in data.user.unique():
            g = self.G.get(student, 0)
            for _ in range(3):
                sumc, sump, sump1p = 0,0,0
                for i in data[data.user==student].index:
                    sumc += data.correct[i]
                    p = sigmoid_shift(g - self.D.get(data.place[i],0), random_factor(data.type[i]))
                    sump += p
                    sump1p += p*(1-p)
                if sump1p:
                    g = g + (sumc - sump) / sump1p # newtonova metoda, vzorec z
                    g = max(min(g, 5), -5)  # drzime v intervalu -5, 5
            self.G[student] = g
#            print "\t",student, self.G[student]
        # normalizace
        m = np.mean(np.array(self.G.values()))
        for s in self.G.keys():
            self.G[s] = self.G[s] - m
