import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom

social_heals = 0
scrimshander_knife = 1
use_HRelic_on_HellM = 1

RES = np.array(['Echoes', 'Scrip', 'TBScraps', 'MoDS', 'BFragments', 'Peppercaps', 'WAmber', 'CasingCP', 'Moonlit', 'Sw7Necks', 'GenSkeleton', 'WTentacles', 'MRibcage', 'HRelics'])
LENGTH = len(RES)
REFR = {}

mam_avg = np.array([6, 5.538, 5.149, 4.831, 4.594, 4.461, 4.471, 4.694, 5.236, 6.261, 8])
neck7_wander = np.array([5, 5.523, 6, 6.339, 6.499, 6.484, 6.327, 6.074, 5.769, 5.425, 5])
neck7_dark = np.array([1, 0.974, 0.852, 0.647, 0.42, 0.227, 0.096, 0.029, 0.005, 0.0002, 0])
eps = 63.5/125


for i in range(LENGTH):
    REFR[RES[i]] = i

def broad(difficulty, score):
    if (difficulty == 0):
        return 1
    return min(1, 0.6*score/difficulty)
    
def narrow(difficulty, score):
    p = min(1, 1e-1*(score - difficulty) + 0.6)
    return max(p, 1e-1)

broad = np.frompyfunc(broad, 2, 1)
narrow = np.frompyfunc(narrow, 2, 1)


checks = {'broad': broad, 'narrow': narrow}

class recipe:
    
    def __init__(self, name, in_resources, action=0):
        
        self.name = name
        self.resources = np.zeros(LENGTH)
        for KEYS in in_resources:
            self.resources[REFR[KEYS]] = in_resources[KEYS]
            
        self.action_cost = action
        
        self.action_penalty = np.frompyfunc(self.action_penalty, 3, 1)
        self.menace_penalty = np.frompyfunc(self.menace_penalty, 4, 1)
        self.sell_penalty = np.frompyfunc(self.sell_penalty, 5, 1)
        
        
    def action_penalty(self, difficulty, stat, mode='broad'):
        #raises action_cost due to failing checks
        
        p = checks[mode](difficulty, stat)
        
        self.action_cost += 1/p - 1
        return 1/p - 1
        
    #♦self.action_penalty = np.frompyfunc(recipe().action_penalty, 3, 1)
        
    def menace_penalty(self, difficulty, stat, menace, mode='broad'):
        #raises action_cost due to failing checks and needing to heal menaces from said check
        fail = self.action_penalty(difficulty, stat, mode)
        heal = fail*menace/3/(1 + social_heals)
        self.action_cost += heal
        return heal
        
    #self.menace_penalty = np.frompyfunc(recipe().action_penalty, 4, 1)
        
    def sell_penalty(self, multiplier, stat, menace, implausibility, probability):
        
        #raises action cost due to failed sales and healing menaces from implausibility
        #takes two arrays, one with the possible implausibility values and the other with the chance of those values occuring
        
        p = broad(multiplier*implausibility, stat)
        penalty = probability*(1 - p)*(1 + menace/3/(1 + social_heals))
        self.action_cost += penalty
        
        return penalty
        
    
            
        
    
def GetMammoth(stats, strat='patient'):
    
    instance = recipe('Get Ribcage', {'MRibcage': 1, 'HRelics': 2, 'Echoes' : -0.16, 'MoDS' : -40}, 6.96)
    apoc = min(10, stats['aPoC'])
    wander_succ = narrow(6, apoc)
    
    if (strat == 'hasty'):
        
        
        instance.resources[REFR['TBScraps']] = -5
        instance.resources[REFR['Moonlit']] = 1 + 6/(1+wander_succ)
        instance.action_cost += 1 + 6/(1+wander_succ)
        
    else:
        
        instance.resources[REFR['TBScraps']] = -5*(1 - wander_succ**8)
        instance.resources[REFR['Moonlit']] = mam_avg[apoc] + 1-wander_succ**8
        instance.action_cost += mam_avg[apoc] + 1-wander_succ**8
        
    return instance
        
        
def Get7Necks(stats, strat='patient'):
    
    instance = recipe('Get Ribcage', {'Sw7Necks': 1, 'Echoes' : -0.16, 'MoDS' : -40}, 7.96)
    apoc = min(10, stats['aPoC'])
    #wander_succ = narrow(6, apoc)
    
    if (strat == 'hasty'):
        
        
        instance.resources[REFR['TBScraps']] = -5
        instance.resources[REFR['Moonlit']] = 1
        instance.action_cost += 1 
        
    else:
        
        instance.resources[REFR['TBScraps']] = -5*neck7_dark[apoc]
        instance.resources[REFR['Moonlit']] = neck7_wander[apoc] + neck7_dark[apoc]
        instance.action_cost += neck7_wander[apoc] + neck7_dark[apoc]
        
    return instance


def HolyMammoth(stats):
    
    instance = recipe('Holy Mammoth', {'HRelics': -4, 'MRibcage': -1, 'BFragments': -500, 'Peppercaps': -10, 'Echoes' : 192.5}, 10)
    legs_succ = narrow(5, stats['Mith'])
    legs_fail = 1 - legs_succ
    carve_succ = narrow(6, stats['Mith'])
    carve_fail = 1 - carve_succ
    instance.action_penalty(6, stats['Mith'], 'narrow')
    instance.resources[REFR['Echoes']] -= 10*legs_fail
    instance.menace_penalty(6, stats['AotRS'], 2, 'narrow')
    impl = np.array([0, 2, 4, 6, 8, 10])
    supp = np.arange(5)
    temp = binom.pmf(supp, 4, legs_fail)
    instance.sell_penalty(50, stats['Shadowy'], 2, impl[0:-1], temp*carve_succ)
    instance.sell_penalty(50, stats['Shadowy'], 2, impl[1:], temp*carve_fail)
    # prob = np.array([carve_succ*legs_succ**4, carve_fail*legs_succ**4 + 4*carve_succ*legs_fail*legs_succ**3, 4*carve_fail*legs_fail*legs_succ**3 + 6*carve_succ*legs_fail**2*legs_succ**2, 6*carve_fail*legs_fail**2*legs_succ**2 + 4*carve_succ*legs_fail**3*legs_succ, carve_succ*legs_fail**4 + 4*carve_fail*legs_fail**3*legs_succ, carve_fail*legs_fail**4])
    #instance.sell_penalty(50, stats['Shadowy'], 2, impl, prob)
    
    return instance

def UngodlyMammoth(stats):
    
    instance = recipe('Ungodly Mammoth', {'HRelics': -3, 'MRibcage': -1, 'BFragments': -500, 'Peppercaps': -10, 'WTentacles': -2, 'Echoes': 172.5}, 9)
    
    legs_succ = narrow(5, stats['Mith'])
    legs_fail = 1 - legs_succ
    tent_succ = narrow(1, stats['MAnatomy'])
    tent_fail = 1 - tent_succ
    tail_succ = narrow(5, stats['MAnatomy'])
    tail_fail = 1 - tail_succ
    
    instance.resources[REFR['Echoes']] -= 7.5*legs_fail + 2*tent_fail
    instance.menace_penalty(6, stats['AotRS'], 2, 'narrow')    
    
    impl1 = np.array([0, 2, 4, 6, 8])
    impl2 = impl1 +1
    
    supp = np.arange(4)
    temp = binom.pmf(supp, 4, legs_fail)
    instance.sell_penalty(50, stats['Shadowy'], 2, impl1[0:-1], temp*tail_succ*tent_succ)
    instance.sell_penalty(50, stats['Shadowy'], 2, impl1[1:], temp*tail_fail*tent_succ)
    instance.sell_penalty(50, stats['Shadowy'], 2, impl2[0:-1], temp*tail_succ*tent_fail)
    instance.sell_penalty(50, stats['Shadowy'], 2, impl2[1:], temp*tail_fail*tent_fail)
    
    # prob = np.array([tail_succ*legs_succ**3, tail_fail*legs_succ**3 + 3*tail_succ*legs_fail*legs_succ**2, 3*tail_fail*legs_fail*legs_succ**2 +3*tail_succ*legs_succ*fail_succ**2, 3*tail_fail*legs_succ*fail_succ**2 + tail_succ*legs_fail**3, tail_fail*legs_fail**3])
    #     

    #   instance.sell_penalty(50, stats['Shadowy'], 2, impl1, prob*tent_succ) 
    # instance.sell_penalty(50, stats['Shadowy'], 2, impl2, prob*tent_fail)   
    
    return instance
    
def HellMammoth(stats):
    
    instance = recipe('Mammoth from Hell', {'MRibcage': -1, 'BFragments': -1000, 'WAmber': -5, 'Scrip': 125 + 25 + 5*4}, 9)
    
    limb_succ = narrow(11, stats['MAnatomy'])
    limb_fail = 1 - limb_succ
    
    skull_succ = narrow(6, stats['MAnatomy'])
    skull_fail = 1 - skull_succ
    
    tail_succ = narrow(5, stats['MAnatomy'])
    tail_fail = 1 - tail_succ
    
    carve_succ = narrow(6, stats['Mith'])
    carve_fail = 1 - carve_succ
    
    chimera_succ = narrow(11, stats['Mith'])
    chimera_impl = np.array([3, 6])
    chimera_prob = np.array([chimera_succ, 1 - chimera_succ])
    
    #CYOA
    
    #1 success attaching Horned Skull +
    #3 successes on first 3 Fossilised Forelimbs=
    #  use HRelic or UTBone, no tail, 9 Antiquity 2 Menace

    chance = skull_succ*limb_succ**3
    

    instance.resources[REFR['Scrip']] += chance*(25*use_HRelic_on_HellM -5 + 90)
    instance.resources[REFR['HRelics']] -= chance*use_HRelic_on_HellM
    
    if (use_HRelic_on_HellM == 0):        
        instance.sell_penalty(75, stats['Shadowy'], 5, chimera_impl, chance*chimera_prob)
        
    else:
        relic_succ = narrow(5, stats['Mith'])
        relic_fail = 1 - relic_succ
        impla = np.array([3, 6, 5, 8])
        proba = np.empty(4)
        proba[:2] = chimera_prob*chance*relic_succ
        proba[2:] = chimera_prob*chance*relic_fail
        instance.sell_penalty(75, stats['Shadowy'], 5, impla, proba)
        
    
    #1 success attaching Horned Skull +
    #3 successes 1 failure on Fossilised Forelimb (at least 1 fail among first 3)=
    #  add 1 tentacle, 9 Antiquity 2 Menace
    chance = 3*skull_succ*limb_fail*limb_succ**3
    instance.resources[REFR['Scrip']] += chance*(90 + 5)
    instance.resources[REFR['WTentacles']] -= chance
    impla = np.array([3, 6, 5, 8])
    proba = np.empty(4)
    proba[:2] = chimera_prob*chance*tail_succ
    proba[2:] = chimera_prob*chance*tail_fail
    instance.sell_penalty(75, stats['Shadowy'], 5, impla, proba)
    
    #1 success attaching Horned Skull +
    #2 or more failures on Forelimbs = 
    #  do nothing, 9-7 Antiquity 2 Menace
    antiq = np.array([7, 8, 9])
    chance = skull_succ*binom.pmf(antiq-7, 4, limb_succ)
    
    instance.resources[REFR['Scrip']] += 10*np.dot(chance, antiq)
    instance.sell_penalty(75, stats['Shadowy'], 5, chimera_impl, chance.sum()*chimera_prob)
    
    #1 fail on attaching Horned Skull=
    #  add 4 Forelimbs, 11-7 Antiquity 1 Menace :(
    
    numb = np.arange(5)
    chance = skull_fail*binom.pmf(numb, 4, limb_succ)
    antiq = 7 + numb
    instance.resources[REFR['Scrip']] += 5*np.dot(chance, antiq)
    instance.sell_penalty(75, stats['Shadowy'], 5, chimera_impl, chance.sum()*chimera_prob)
    
    return instance
    
def GeneratorSkeleton(stats):
    
    instance = recipe('Generator Skeleton', {'Sw7Necks': -1, 'GenSkeleton': 1, 'Scrip': -940}, 19)
    instance.resources[REFR['Scrip']] += 5*(1 - broad(200, stats['Persuasive']))
    return instance
    
def SellEntrepreneur(stats):
    
    instance = recipe('Sell to Entrepreneuer', {'GenSkeleton': -1, 'Scrip': 4, 'MoDS': 1115})
    impl = np.array([3, 6])
    chimera_succ = narrow(11, stats['Mith'])
    prob = np.array([chimera_succ, 1 - chimera_succ])
    instance.sell_penalty(75, stats['Shadowy'], 2, impl, prob)
    
    return instance
    
def SellPalaeontologist(stats):
    
    instance = recipe('Sell to Palaeontologist', {'GenSkeleton': -1, 'Echoes': 5, 'BFragments': 55505})
    impl = np.array([3, 6])
    chimera_succ = narrow(11, stats['Mith'])
    prob = np.array([chimera_succ, 1 - chimera_succ])
    instance.sell_penalty(40, stats['Shadowy'], 2, impl, prob)
    
    return instance
    
def SellZailor(stats):
    
    instance = recipe('Sell to Zailor', {'GenSkeleton': -1, 'Scrip': 90, 'WAmber': 5575})
    
    limb_succ = narrow(11, stats['MAnatomy'])
    limb_fail = 1 - limb_succ
    instance.resources[REFR['Scrip']] += 10*2*limb_succ*limb_fail + 20*limb_succ**2
    
    impl = np.array([3, 6])
    chimera_succ = narrow(11, stats['Mith'])
    prob = np.array([chimera_succ, 1 - chimera_succ])
    instance.sell_penalty(75, stats['Shadowy'], 2, impl, prob)
    
    return instance
    
def SellNaive(stats):
    
    instance = recipe('Sell to Naive', {'GenSkeleton': -1, 'TBScraps': 222})
    
    impl = np.array([3, 6])
    chimera_succ = narrow(11, stats['Mith'])
    prob = np.array([chimera_succ, 1 - chimera_succ])
    
    instance.sell_penalty(25, stats['Shadowy'], 3.5, impl, prob)
    
    return instance
    
def BasicHelicon(stats):
    
    instance = recipe('Basic Helicon Round', {'Peppercaps': 25, 'Echoes': 0.5, 'Scrip': 3, 'CasingCP': 15}, 6)
    
    return instance
    
def TentacleHelicon1(stats):
    
    instance = recipe('Tentacle Helicon Round 1', {'Peppercaps': 25, 'Echoes': 0.5, 'Scrip': 2}, 6)
    
    draw_succ = narrow(4, stats['SArts'])
    instance.resources[REFR['Scrip']] += 3*draw_succ
    instance.resources[REFR['WTentacles']] += 3*draw_succ
    instance.resources[REFR['WAmber']] -= 5*draw_succ
    
    return instance
    
def MediumLarceny(stats):
    
    instance = recipe('Medium Claywayman Larceny', {'Echoes': 27.5, 'CasingCP': -36}, 1)
    
    return instance
    
def Painting(stats):
    
    instance = recipe('Painting at Balmoral', {'Moonlit': -12, 'Echoes': 85}, 11)
    
    paint_succ = narrow(200, stats['Persuasive'])
    paint_fail = 1 - paint_succ
    
    succ_number = np.array([3, 4, 5, 6])
 
    binomial = binom.pmf(succ_number, 6, paint_succ)
    
    instance.resources[REFR['Echoes']] += 20*binomial.sum()
    
    return instance
    
ALL_STEPS = {'Get Mammoth': GetMammoth, 'Get 7Necks': Get7Necks, 'Holy Mammoth': HolyMammoth, 'Ungodly Mammoth': UngodlyMammoth, 'Mammoth from Hell': HellMammoth, 'Generator Skeleton': GeneratorSkeleton, 'Sell to Entrepreneur': SellEntrepreneur, 'Sell to Palaeontologist': SellPalaeontologist, 'Sell to Zailor': SellZailor, 'Sell to Naive': SellNaive, 'Basic Helicon Round': BasicHelicon, 'Tentacle Helicon Round 1': TentacleHelicon1, 'Medium Larceny': MediumLarceny, 'Painting': Painting}
    
class grind:
    
    def __init__(self, stats, steps):
        
        self.number = len(steps)
        

        temp_matrix = np.empty([self.number, LENGTH + 1])
        self.stats = stats
        
        for i in range(self.number):
            
            temp = ALL_STEPS[steps[i]](stats)
            temp_matrix[i, 1:] = temp.resources
            temp_matrix[i, 0] = temp.action_cost
            
        self.matrix = temp_matrix.transpose()
        l,v,r = np.linalg.svd(self.matrix[3:, :])
        self.values = v
        self.dim_grind = self.number - len(self.values)
        self.vectors = r
        self.sols = r[-self.dim_grind:]
        self.sol = r[-1]
        actions = np.dot(self.sol, self.matrix[0])
        echoes = np.dot(self.sol, self.matrix[1])
        scrip = np.dot(self.sol, self.matrix[2])
        self.epa = (echoes + eps*scrip)/actions
        signs = np.sign(self.sol)
        check1 = np.abs(signs.sum())
        check2 = np.abs(signs).sum()
        # check = np.sign(self.sols)
        # sums = check.sum(1)
        # print(self.sols)
        if (check1 != self.number):
            
            if( check2 < self.number):
                print('warning: unnecessary step')
                
            if( check1 != check2):
                print('erorr: grind not practicable')
            
            
            
        
        

    
    