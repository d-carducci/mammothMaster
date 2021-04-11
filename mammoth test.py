import mammothMaster as mm
import numpy as np
import matplotlib.pyplot as plt

scores = dict(Persuasive=300, Watchful=300, Shadowy=300, Dangerous=300, Mith=10, SArts=10, AotRS=10, aPoC=10,
              MAnatomy=10, Katatox=10)

#scores = {'Persuasive': 269, 'Watchful': 277, 'Shadowy': 265, 'Dangerous': 265, 'Mith' : 8, 'SArts' : 8, 'AotRS' : 8, 'aPoC' : 7, 'MAnatomy': 8}

mamRecipes = [['Mammoth from Hell', 'Duplicate Ox Skull'],
              ['Mammoth of the Zee', 'Sell to Theologian', 'Duplicate Seal Skull'],
              ['One-winged Mammoth']]
helRecipes = ['Basic Helicon Round', 'Tentacle Helicon Round 2', 'Ungodly Mammoth']

dictio = {}

toomany = ['WTentacles']
toomany = []

# for i in range(len(step1)):
#     dictio[step[i]] = i

total = np.empty([3, 9])

test_stat = 'MAnatomy'
text=['no', 'yes']

for i in range(3):
    scores[test_stat] = 7


    for j in range(9):
        print(mamRecipes[i])
        trial = mm.ranching(mamRecipes[i], helRecipes, stats=scores, overflow_list=toomany)
        #print(trial.grind_dim)
        total[i, j] = trial.epaTotal
        #echoesOnly[i, j] = trial.epa
        #helicon1[i, j] = trial.sol[dictio['Tentacle Helicon Round 1']]
        #helicon2[i, j] = trial.sol[dictio['Basic Helicon Round']]
        scores[test_stat] += 1
        #print(trial.matrix('URRumours'))
        
    plt.scatter(7+np.arange(9), total[i], label=mamRecipes[i][0])
    #plt.scatter(8 + np.arange(8), echoesOnly[i], label="Echoes only, SC Knife: %s" % text[i])
    #plt.scatter(8+np.arange(8), helicon1[i], label="Use HRelics on Hell Mammoth: %s" % text[i])
    #plt.scatter(8+np.arange(8), helicon2[i], label="Use HRelics on Hell Mammoth: %s" % text[i])


plt.legend()
plt.xlabel(test_stat)
plt.ylabel('Epa')
plt.savefig('author_variants_ungodly.png')
plt.show()
