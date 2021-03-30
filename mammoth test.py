import mammothMaster as mm
import numpy as np
import matplotlib.pyplot as plt

scores = {'Persuasive': 300, 'Watchful': 300, 'Shadowy': 300, 'Dangerous': 300, 'Mith' : 10, 'SArts' : 10, 'AotRS' : 10, 'aPoC' : 10, 'MAnatomy': 10}

step = np.array(['Get Mammoth', 'Get 7Necks', 'Holy Mammoth', 'Mammoth from Hell', 'Generator Skeleton', 'Sell to Entrepreneur', 'Sell to Palaeontologist', 'Sell to Zailor', 'Sell to Naive', 'Basic Helicon Round', 'Tentacle Helicon Round 1', 'Medium Larceny', 'Painting'])

dictio = {}

for i in range(len(step)):
    dictio[step[i]] = i

support = np.empty([2, 8])
helicon1 = np.empty([2, 8])
helicon2 = np.empty([2, 8])
text=['no', 'yes']
#trial = mm.grind(scores, step)

for i in (0, 1):
    scores['MAnatomy'] = 8
    mm.use_HRelic_on_HellM = i
    print("Use HRelics on Hell Mammoth: %s" % text[i])
    for j in range(8):
        trial = mm.grind(scores, step)
        print(trial.dim_grind)
        support[i, j] = trial.epa
        helicon1[i, j] = trial.sol[dictio['Tentacle Helicon Round 1']]
        helicon2[i, j] = trial.sol[dictio['Basic Helicon Round']]
        scores['MAnatomy'] += 1
        
    plt.scatter(8+np.arange(8), support[i], label="Use HRelics on Hell Mammoth: %s" % text[i])
    #plt.scatter(8+np.arange(8), helicon1[i], label="Use HRelics on Hell Mammoth: %s" % text[i])
    #plt.scatter(8+np.arange(8), helicon2[i], label="Use HRelics on Hell Mammoth: %s" % text[i])
    
plt.legend()
plt.show()