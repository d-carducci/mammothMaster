import mammothMaster as mm
import numpy as np
import matplotlib.pyplot as plt

scores = {'Persuasive': 300, 'Watchful': 300, 'Shadowy': 300, 'Dangerous': 300, 'Mith' : 10, 'SArts' : 10, 'AotRS' : 10, 'aPoC' : 10, 'MAnatomy': 10}

#scores = {'Persuasive': 269, 'Watchful': 277, 'Shadowy': 265, 'Dangerous': 265, 'Mith' : 8, 'SArts' : 8, 'AotRS' : 8, 'aPoC' : 7, 'MAnatomy': 8}

step = np.array(['Get Mammoth', 'Get 7Necks', 'Ungodly Mammoth', 'Mammoth from Hell', 'Generator Skeleton', 'Sell to Entrepreneur', 'Sell to Palaeontologist', 'Sell to Zailor', 'Basic Helicon Round', 'Tentacle Helicon Round 1', 'Medium Larceny', 'Painting', 'Duplicate Ox Skull'])

#step = ['Get Mammoth', 'Get 7Necks', 'Holy Mammoth', 'Mammoth from Hell', 'Generator Skeleton', 'Sell to Entrepreneur', 'Sell to Palaeontologist', 'Sell to Zailor', 'Sell to Naive', 'Basic Helicon Round', 'Tentacle Helicon Round 1', 'Medium Larceny', 'Painting', 'Dig at SVIII', 'Discover HSkull', 'Bone Newspaper']

#step = np.array(['Get Mammoth', 'Get 7Necks', 'Ungodly Mammoth', 'Mammoth from Hell', 'Generator Skeleton', 'Sell to Entrepreneur', 'Sell to Palaeontologist', 'Sell to Zailor', 'Sell to Naive', 'Basic Helicon Round', 'Tentacle Helicon Round 1', 'Medium Larceny', 'Painting', 'Dig at SVIII', 'Discover HSkull', 'Bone Newspaper'])

#step1 = ['Get Mammoth', 'Get 7Necks', 'Ungodly Mammoth', 'Mammoth of the Zee', 'Generator Skeleton', 'Sell to Entrepreneur', 'Sell to Palaeontologist', 'Sell to Zailor', 'Sell to Naive', 'Basic Helicon Round', 'Tentacle Helicon Round 1', 'Medium Larceny', 'Painting', 'Duplicate Seal Skull', 'Sell HRelic for IBiscuits']

dictio = {}

ignore = ['JBStinger', 'PTBones']
toomany = ['Peppercaps']
toomany = 0

# for i in range(len(step1)):
#     dictio[step[i]] = i

support = np.empty([3, 8])
helicon1 = np.empty([2, 8])
helicon2 = np.empty([2, 8])
text=['no', 'yes']
#trial = mm.grind(scores, step)

labels = ['No knife, use HRelics', 'No Knife, no HRelics', 'Use Knife']
argus = [(0, 1), (0, 0), (1, 0)]

for i in range(3):
    scores['MAnatomy'] = 8
    #mm.scrimshander_knife = i
    print(labels[i])
    for j in range(8):
        trial = mm.grind(scores, step, toomany, ignore, {'Mammoth from Hell': argus[i]})
        print(trial.grind_dim)
        support[i, j] = trial.epa
        #helicon1[i, j] = trial.sol[dictio['Tentacle Helicon Round 1']]
        #helicon2[i, j] = trial.sol[dictio['Basic Helicon Round']]
        scores['MAnatomy'] += 1
        trial.print_ratios()
        
    plt.scatter(8+np.arange(8), support[i], label=labels[i])
    #plt.scatter(8+np.arange(8), helicon1[i], label="Use HRelics on Hell Mammoth: %s" % text[i])
    #plt.scatter(8+np.arange(8), helicon2[i], label="Use HRelics on Hell Mammoth: %s" % text[i])
    
plt.legend()
plt.show()