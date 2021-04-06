import numpy as np
from scipy.stats import binom

## social heals:
#  Determines whether the menace healing rate is set to the 6 cp/action from social heals or to the 3 cp/action from many late-game single-player options.
## scrimshander_knife:
#  Determines whether to account for the possibility of removing Antiquity using the event-locked Scrimshander Carving Knife.
## use_HRelic_on_HellM:
#  Determines whether to fill unused limb slots on Mammoths from Hell using Unidentified Thigh Bones or Holy Relics of the Thigh of St Fiacre.

social_heals = 1
debonair_palaeontologist = 1

## The RES dictionary
#  RES is a list containing the name of every resource involved in the grind; the REFR dictionary is an hack to reference array entries using the in-game resouce name rather than the index number without having to deal with panda dataframes.

#  do always keep actions/echoes/scrip in that order as the first three elements though, otherwise it makes some stuff much more cumbersome.

RES = np.array(['Actions', 'Echoes', 'Scrip', 'TBScraps', 'MoDS', 'BFragments', 'Peppercaps', 'WAmber', 'CasingCP', 'Moonlit', 'Sw7Necks', 'GenSkeleton', 'WTentacles', 'MRibcage', 'HRelics', 'BSurveys', 'PDiscovery', 'JBStinger', 'PTBones', 'HSkull', 'JThigh', 'IBiscuits', 'PSkull'])
LENGTH = len(RES)
REFR = {}
EPS = 63.5/125 #scrip-to-epa conversione rate from hambitrage (Ham arbitrage)


for i in range(LENGTH):
    REFR[RES[i]] = i

## Balmoral stuff
#  these are all average numbers of actions taken while in the Balmoral woods assuming particular strategies and aPoC scores (aPoC = array index); all numbers were calcuated simulating and averaging 1e7 rounds through the woods.

#  mam_avg = average number of actions spent wandering the woods when sourcing Mammoth Ribcages, assuming you only darken when it becomes necessary.
#  neck7_wander = average number of actions spent wandering the woods when sourcing Skeletons with 7 Necks, assuming you only darken when it becomes necessary.
#  neck7_dark = probability of needing to darken the woods when sourcing Skeletons with 7 Necks, assuming you only darken when it becomes necessary.

mam_avg = np.array([6, 5.538, 5.149, 4.831, 4.594, 4.461, 4.471, 4.694, 5.236, 6.261, 8])
neck7_wander = np.array([5, 5.523, 6, 6.339, 6.499, 6.484, 6.327, 6.074, 5.769, 5.425, 5])
neck7_dark = np.array([1, 0.974, 0.852, 0.647, 0.42, 0.227, 0.096, 0.029, 0.005, 0.0002, 0])



## check difficulties:
#  ufuncs calculating the success chance of a check, with the same convention of difficulty = (score at which you have a 60% chance of succeeding).

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
    

## the recipe class
#  each instance represents a different possible step in the grind; the main feature is the self.resources array, containing the item changes involved in it. 
#  in_resources is a dictionary where each entry is of the form {'resource name': change} and only the desired non-zero entries needing to be specified (thanks to self.resources being initialized with np.zeros rather than np.empty).

# index 0 ('Actions') is the only one where an expense is recorded as a positive number rather than a negative number, since there's no way to gain actions during regular play.

# the self.(*)_penalty functions come in handy when calculating the resources array of steps where a player's stats influence the outcome.

# the self.(*)_resource functions allows quick access to the self.resources array through the resource name rather than its index in RES

class recipe:
    
    def __init__(self, name, in_resources):
        
        self.name = name
        self.resources = np.zeros(LENGTH)
        for KEYS in in_resources:
            self.resources[REFR[KEYS]] = in_resources[KEYS]
            

        
        self.action_penalty = np.frompyfunc(self.action_penalty, 3, 1)
        self.menace_penalty = np.frompyfunc(self.menace_penalty, 4, 1)
        self.sell_penalty = np.frompyfunc(self.sell_penalty, 5, 1)
        self.get_resource = np.frompyfunc(self.get_resource, 1, 1)
        self.add_resource = np.frompyfunc(self.add_resource, 2, 0)
        self.remove_resource = np.frompyfunc(self.remove_resource, 2, 0)
        
    
    def get_resource(self, key):
        
        return self.resources[REFR[key]]
        
    def add_resource(self, key, amnt):
        
        self.resources[REFR[key]] += amnt
        
    def remove_resource(self, key, amnt):
        
        self.resources[REFR[key]] -= amnt
    
    #raises action_cost due to failing checks
    
    def action_penalty(self, difficulty, stat, mode='broad'):
        
        
        p = checks[mode](difficulty, stat)
        
        self.resources[0] += 1/p - 1
        return 1/p - 1
        
    #raises action_cost due to failing checks and needing to heal menaces from said failed checks
    
    def menace_penalty(self, difficulty, stat, menace, mode='broad'):
        
        fail = self.action_penalty(difficulty, stat, mode)
        heal = fail*menace/3/(1 + social_heals)
        self.resources[0] += heal
        return heal
            
    #raises action cost due to failed sales and healing menaces from implausibility.
    #takes two arrays, one with the possible implausibility values and the other with the chance of those values occuring
        
    def sell_penalty(self, multiplier, stat, menace, implausibility, probability):
        
        
        
        p = broad(multiplier*implausibility, stat)
        penalty = probability*(1/p - 1)*(1 + menace/3/(1 + social_heals))
        self.resources[0] += penalty
        
        return penalty
        



## The Recipe List

#  Here we define every possible steps of the grind using functions that return specific instances of the recipe class.

#  *stats*: the stats input is a dictionary containing all the player stats as entries of the form {'statname': score}.
#  *strat*: the Balmoral woods step have an additional input, a string which specifies what strategy to follow with regards to Darken the woods; by default it chooses the one that's more optimal, based on the Player of Chess score submitted.

#  Some resources are set at initialization while others in the body of the function; this is done following the criteria that 1) the resources specified at initialization should be fixed and 2) there should be as few instance.add_resource calls as possible.
        
    
def GetMammoth(stats, strat='best'):
    
    instance = recipe('Get Ribcage', {'Actions': 6.96, 'MRibcage': 1, 'HRelics': 2, 'Echoes' : -0.16, 'MoDS' : -40})
    apoc = min(10, stats['aPoC'])
    wander_succ = narrow(6, apoc)
    
    if strat == 'best':
        
        strat = 'hasty' if apoc < 9 else 'patient'
            
    
    if strat == 'hasty':
        
        
        instance.remove_resource('TBScraps', 5)
        instance.add_resource('Moonlit', 1 + 6/(1+wander_succ))
        instance.resources[0] += 1 + 6/(1+wander_succ)
        
    else:
        
        instance.remove_resource('TBScraps', 5*(1 - wander_succ**8))
        instance.add_resource('Moonlit', mam_avg[apoc] + 1-wander_succ**8)
        instance.resources[0] += mam_avg[apoc] + 1-wander_succ**8
        
    return instance
        
        
def Get7Necks(stats, strat='best'):
    
    instance = recipe('Get Ribcage', {'Actions': 7.96, 'Sw7Necks': 1, 'Echoes' : -0.16, 'MoDS' : -40})
    apoc = min(10, stats['aPoC'])
    #wander_succ = narrow(6, apoc)
    
    if strat == 'best':
        
        strat = 'hasty' if apoc < 3 else 'patient'
    
    if (strat == 'hasty'):
        
        
        instance.resources[REFR['TBScraps']] -= 5
        instance.resources[REFR['Moonlit']] += 1
        instance.resources[0] += 1 
        
    else:
        
        instance.resources[REFR['TBScraps']] -= 5*neck7_dark[apoc]
        instance.resources[REFR['Moonlit']] += neck7_wander[apoc] + neck7_dark[apoc]
        instance.resources[0] += neck7_wander[apoc] + neck7_dark[apoc]
        
    return instance

def SVIIIdig(stats):
    
    instance = recipe('Dig near Station VIII', {'Actions': 3, 'Echoes': -3.5, 'BSurveys': -150, 'PDiscovery': 6, 'BFragments': 27})
    return instance
    
def PDMRibcage(stats):
    
    instance = recipe('Get a Mammoth Ribcage', {'MRibcage': 1, 'PDiscovery': -5})
    return instance
    
def PDHSkull(stats):
    
    instance = recipe('Get a Horned Skull', {'HSkull': 1, 'PDiscovery': -1})
    return instance
    
def PDJThigh(stats):
    
    instance = recipe('Get a Femur of a Jurassic Beast', {'JThigh': 5, 'PDiscovery': -1})
    return instance
    
def PDBFragments(stats):
    
    instance = recipe('Get Bone Fragments', {'BFragments': 1250, 'PDiscovery': -1})
    return instance
    
def BoneNewspaper(stats, PLrate=0, debonair_palaeontologist=False):
    instance = recipe('Exposé on Palaeontology', {'Actions': 22.5, 'BSurveys': 72, 'HRelics': 2, 'WTentacles': 4.5, 'JBStinger': 1.5, 'PTBones':1, 'Scrip': 2, 'Echoes': 5})
    
    instance.resources[0] += debonair_palaeontologist + PLrate
    instance.add_resource('BSurveys', 13*(debonair_palaeontologist + PLrate))
    instance.add_resource('Echoes', 2*debonair_palaeontologist)
    
    return instance

def DuplicateHSkull(stats):
    
    instance = recipe('Duplicate Ox Skull', {'Actions':1, 'BFragments': -1000, 'WAmber': -5, 'HSkull': 1})
    return instance
    
    
def DuplicatePSkull(stats):
    
    instance = recipe('Duplicate Seal Skull', {'Actions':1, 'BFragments': -1750, 'WAmber': -25, 'IBiscuits': -1, 'PSkull': 1})
    return instance
    
def ZeeMammoth(stats):
    
    instance = recipe('Mammoth of the Zee', {'Actions': 9, 'MRibcage': -1, 'PSkull': -1, 'Scrip': 125 + 50 + 5*4})
    
    skull_succ = narrow(4, stats['MAnatomy'])
    skull_fail = 1 - skull_succ
    
    tail_succ = narrow(5, stats['MAnatomy'])
    tail_fail = 1 - tail_succ
    
    chimera_succ = narrow(11, stats['Mith'])
    chimera_impl = np.array([3, 6])
    chimera_prob = np.array([chimera_succ, 1 - chimera_succ])
    
    limb_succ = narrow(11, stats['MAnatomy'])
    limb_fail = 1 - limb_succ
    
    #if skull attachment succeeds, attach all legs and if all succeed also add tentacle
    
    needtail_chance = skull_succ*limb_succ**4
    antiq = np.array([6, 7, 8, 9])
    chance = skull_succ*binom.pmf(antiq-6, 4, limb_succ)
    chance[-1] += needtail_chance
    instance.add_resource('Scrip', 10*np.dot(antiq, chance) + 5*needtail_chance)
    
    #if skull attachment fails attach all legs (1 Menace 6-10 Antiquity)
    
    antiq = np.array([6, 7, 8, 9, 10])
    chance = skull_fail*binom.pmf(antiq-6, 4, limb_succ)
    instance.add_resource('Scrip', 5*np.dot(antiq, chance))
    
    #account for failed sales
    
    impla = np.array([3, 6, 5, 8])
    proba = np.empty(4)
    proba[:2] = chimera_prob*needtail_chance*tail_succ
    proba[2:] = chimera_prob*needtail_chance*tail_fail
    instance.sell_penalty(75, stats['Shadowy'], 5, impla, proba)
    
    return instance
    

def EasyMammoth(stats):
    
    instance = recipe('Easy Mammoth', {'Actions': 9, 'MRibcage': -1, 'HSkull': -1, 'Scrip': 125 + 25 +5*4})
    
    skull_succ = narrow(6, stats['MAnatomy'])
    skull_fail = 1 - skull_succ
    
    tail_succ = narrow(5, stats['MAnatomy'])
    tail_fail = 1 - tail_succ
    
    carve_succ = narrow(6, stats['Mith'])
    carve_fail = 1 - carve_succ
    
    chimera_succ = narrow(11, stats['Mith'])
    chimera_impl = np.array([3, 6])
    chimera_prob = np.array([chimera_succ, 1 - chimera_succ])
    
    limb_succ = narrow(11, stats['MAnatomy'])
    limb_fail = 1 - limb_succ
    
    #if skull fails: 
    #put JBStinger, 1 success on forelimb: Jthigh, 2 extra limbs
    #put JBStinger, 1 failure on forelimb, then 1 success on forelimb: 2 extra limbs
    #put JBStinger, 2 failures on forelimb: Jthigh, 1 extra limb
    #3 menace, 6 antiquity
    chance = skull_fail*limb_succ
    
    instance.resources[REFR['Scrip']] += chance*(1 + 6 + 4 -15)
    
    
    chance = chance*limb_fail
    instance.resources[REFR['Scrip']] += chance*(1 + 4 - 10)
    
    chance = skull_fail*limb_fail**2
    instance.resources[REFR['Scrip']] += chance*(1 - 10 + 6 + 2)
    instance.resources[REFR['JThigh']] -= chance
    
    instance.resources[REFR['Scrip']] += skull_fail*90
    instance.sell_penalty(75, stats['Shadowy'], 5, chimera_impl, skull_fail*chimera_prob)
    
    #if skull succeeds: 
    
    if (scrimshander_knife == 0):
    
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
            
    else:   #4 successess: scrimshander knife
        
        chance = skull_succ*limb_succ**4
        instance.resources[REFR['Scrip']] += chance*90
        
        carve_succ = narrow(6, stats['Mith'])
        carve_fail = 1 - carve_succ
        instance.action_penalty(6, stats['Mith'], 'narrow')
        
        impla = np.array([3, 6, 5, 8])
        proba = np.empty(4)
        proba[:2] = chimera_prob*chance*carve_succ
        proba[2:] = chimera_prob*chance*carve_fail
        instance.sell_penalty(75, stats['Shadowy'], 5, impla, proba)
    
    
    
    #1 success attaching Horned Skull +
    #3 successes 1 failure on Fossilised Forelimb 
    #(if no scrimshander carving knife, at least 1 fail among first 3)=
    #  add 1 tentacle, 9 Antiquity 2 Menace
    if scrimshander_knife == 0:
        chance = 3*skull_succ*limb_fail*limb_succ**3
    
    else:
        chance = 4*skull_succ*limb_fail*limb_succ**3
        
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
    
    return instance
    
    

def HolyMammoth(stats, scrimshander_knife=1):
    
    if scrimshander_knife == 0:
        
        return 0
        
    else:
        
        instance = recipe('Holy Mammoth', {'Actions': 10, 'HRelics': -4, 'MRibcage': -1, 'BFragments': -500, 'Peppercaps': -10, 'Echoes' : 192.5})
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
    
    instance = recipe('Ungodly Mammoth', {'Actions': 9, 'HRelics': -3, 'MRibcage': -1, 'BFragments': -500, 'Peppercaps': -10, 'WTentacles': -2, 'Echoes': 172.5})
    
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
    
    return instance
    
def HellMammoth(stats, scrimshander_knife=1, use_HRelic_on_HellM=0):
    
    instance = recipe('Mammoth from Hell', {'Actions': 9, 'MRibcage': -1, 'HSkull': -1, 'Scrip': 125 + 25 + 5*4})
    
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
    #  if no scrimshander carving knife:
    #1 success attaching Horned Skull +
    #3 successes on first 3 Fossilised Forelimbs=
    #  use HRelic or UTBone, no tail, 9 Antiquity 2 Menace
    
    if (scrimshander_knife == 0):
        
        print('no scrimshander')
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
            
        
            
    else:   #4 successess: scrimshander knife
        
        chance = skull_succ*limb_succ**4
        instance.resources[REFR['Scrip']] += chance*90
        
        carve_succ = narrow(6, stats['Mith'])
        carve_fail = 1 - carve_succ
        instance.action_penalty(6, stats['Mith'], 'narrow')
        
        impla = np.array([3, 6, 5, 8])
        proba = np.empty(4)
        proba[:2] = chimera_prob*chance*carve_succ
        proba[2:] = chimera_prob*chance*carve_fail
        instance.sell_penalty(75, stats['Shadowy'], 5, impla, proba)
    
    
    
    #1 success attaching Horned Skull +
    #3 successes 1 failure on Fossilised Forelimb 
    #(if no scrimshander carving knife, at least 1 fail among first 3)=
    #  add 1 tentacle, 9 Antiquity 2 Menace
    if scrimshander_knife == 0:
        chance = 3*skull_succ*limb_fail*limb_succ**3
    
    else:
        chance = 4*skull_succ*limb_fail*limb_succ**3
        
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
    
    instance = recipe('Generator Skeleton', {'Actions': 19, 'Sw7Necks': -1, 'GenSkeleton': 1, 'Scrip': -975})
    instance.resources[REFR['Scrip']] += 5*broad(200, stats['Persuasive'])
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
    
    instance = recipe('Basic Helicon Round', {'Actions': 6, 'Peppercaps': 25, 'Echoes': 0.5, 'Scrip': 3, 'CasingCP': 15})
    
    return instance
    
def TentacleHelicon1(stats):
    
    instance = recipe('Tentacle Helicon Round 1', {'Actions': 6, 'Peppercaps': 25, 'Echoes': 0.5, 'Scrip': 2})
    
    draw_succ = narrow(4, stats['SArts'])
    instance.resources[REFR['Scrip']] += 3*draw_succ
    instance.resources[REFR['WTentacles']] += 3*3*draw_succ
    instance.resources[REFR['WAmber']] -= 5*3*draw_succ
    
    return instance
    
def MediumLarceny(stats):
    
    instance = recipe('Medium Claywayman Larceny', {'Actions': 1, 'Echoes': 27.5, 'CasingCP': -36})
    
    return instance
    
def Painting(stats):
    
    instance = recipe('Painting at Balmoral', {'Actions': 11, 'Moonlit': -12, 'Echoes': 85})
    
    paint_succ = narrow(200, stats['Persuasive'])
    paint_fail = 1 - paint_succ
    
    succ_number = np.array([3, 4, 5, 6])
 
    binomial = binom.pmf(succ_number, 6, paint_succ)
    
    instance.resources[REFR['Echoes']] += 20*binomial.sum()
    
    return instance
    
def SellHRelicBF(stats):
    
    instance = recipe('Sell HRelic for BFragments', {'Actions': 1, 'HRelics': -1, 'BFragments': 1250})
    return instance
    
def SellHRelicIB(stats):
    
    instance = recipe('Sell HRelic for IBiscuits', {'Actions': 1, 'HRelics': -1, 'IBiscuits': 6})
    return instance

def Overflow(resource):
    
    instance = recipe(resource + ' Overflow', {resource: -1})
    return instance
    

    


# ALL_STEPS: dictionary containing all the recipe funcionts, indexed by their name (yeah it doesn't always math with the one in the recipe initialization)

ALL_STEPS = {'Get Mammoth': GetMammoth, 'Get 7Necks': Get7Necks, 'Holy Mammoth': HolyMammoth, 'Ungodly Mammoth': UngodlyMammoth, 'Mammoth from Hell': HellMammoth, 'Generator Skeleton': GeneratorSkeleton, 'Sell to Entrepreneur': SellEntrepreneur, 'Sell to Palaeontologist': SellPalaeontologist, 'Sell to Zailor': SellZailor, 'Sell to Naive': SellNaive, 'Basic Helicon Round': BasicHelicon, 'Tentacle Helicon Round 1': TentacleHelicon1, 'Medium Larceny': MediumLarceny, 'Painting': Painting, 'Duplicate Ox Skull': DuplicateHSkull, 'Duplicate Seal Skull': DuplicatePSkull}

ALL_STEPS['Dig at SVIII'] = SVIIIdig
ALL_STEPS['Discover Mammoth'] = PDMRibcage
ALL_STEPS['Discover HSkull'] = PDHSkull
ALL_STEPS['Discover JThigh'] = PDJThigh
ALL_STEPS['Bone Newspaper'] = BoneNewspaper
ALL_STEPS['Easy Mammoth'] = EasyMammoth
ALL_STEPS['Discover BFragments'] = PDBFragments
ALL_STEPS['Sell HRelic for BFragments'] = SellHRelicBF
ALL_STEPS['Sell HRelic for IBiscuits'] = SellHRelicIB
ALL_STEPS['Mammoth of the Zee'] = ZeeMammoth

    
    
## the grind class:
#  the math meat of the library, each instance takes as input a stat array and a steps array containing the string name for every step in the hypothetical grind you wish to analyze; for each step it creates an instance, shoves its self.resources array in its 2d matrix and transposes it at the end, so that each *row* corresponds to one resource and each *column* corresponds to one step; then numpy.linal.svd() does its math and solves the grind for us
    

            
            
            
            
        
        

    
    