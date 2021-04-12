import numpy as np
from scipy.optimize import minimize, LinearConstraint
from .mammothRecipe import ALL_STEPS, RES, REFR, LENGTH, EPS, Overflow

# The grind class:
# the class storing the meat of the mathematical machinery needed to solve the grind

class Grind:
    
    def __init__(self, stats, steps, overflow_list=[], blacklist=None, add_parameters={'NO':0}):
        """

        :param stats: dictionary containing all the player stats as entries of the form {'statname': score}.
        :param steps: list of the steps involved in the cycle,
            each stored as the string corresponding to the function in the ALL_STEPS dictionary.
        :param overflow_list: list of resources that are involved in the grind but aren't required to be completely consumed;
            will create additional "overflow" steps for each one to be put into.
        :param blacklist: list of resources that should always be ignored when evaluating the cycle.
        :param add_parameters: additional arguments to be passed along to certain steps that accept additional inputs
            (example: strategies for balmoral runs), of the form dict('step name': [list of parameters])
        """
        self.dim1 = len(steps)
            
        self.ref = {} #dictionary reference of the resources involved in the cycle
        self.steps = [] #internal list of steps to take
        self.overflow_list = overflow_list
        
        temp_matrix = [] #temporary list-of-arrays in which to store the resource arrays
        self.stats = stats
        inv_mask = np.zeros(LENGTH) #blank boolean mask with which to index the relevant resources from RES
        
        self.step_ref = {} #internal dictionary reference of the steps involved in the cycle
        
        if blacklist is not None: #adds the item blacklist to inv_mask so that they may be ignored
            for item in blacklist:
                inv_mask[REFR[item]] = 1

        i = 0
        #collates the resource matrix
        for stp_name in steps:

            if stp_name in add_parameters: #check if kwargs include additional inputs for this step
                temp = ALL_STEPS[stp_name](stats, add_parameters[stp_name])
                
            else:
                temp = ALL_STEPS[stp_name](stats)
            # some recipe initialization functions may return 0 rather than an instance, such as when trying
            # to add Holy Mammoths to the cycle with scrimshander_knife == 0; the if branch avoids it being added
            
            if temp:        
                temp_matrix.append(temp.resources)
                self.step_ref[stp_name] = i
                self.steps.append(stp_name)
                i += 1
                if temp.OFresources:
                    # if the recipe involves resources that can both be sold or used in further steps, add them to
                    # the overflow list
                    for item in temp.OFresources:
                        if item not in overflow_list:
                            self.overflow_list.append(item)

        if overflow_list:
            
            for item in overflow_list:
                
                temp = Overflow(item)
                temp_matrix.append(temp.resources)
                self.step_ref[item + ' Overflow'] = i
                self.steps.append(item + ' Overflow')
                i += 1
        
        a = np.asarray(temp_matrix).transpose()         #puts it in the correct shape (resources-rows, steps-columns)
        inv_mask = np.logical_or(inv_mask, (a==0).all(1))#adds unused items to list of resources to ignore
        self.matrix = a[~inv_mask]          #removes all unused resources
        self.reses = RES[~inv_mask]         #creates view of the RES array involving only relevant resources
        self.dim0 = len(self.reses)
        self.dim1 = len(self.steps)
        if self.dim1 != i:
            print('FUCK')

        #create an internal reference for only the relevant resources
        for i in range(self.dim0):          
            self.ref[self.reses[i]] = i

        #find the epa and solution vector
        self.solve()
        
        
    def solve(self):
        
        # Singular value decomposition: decomposes the resource matrix as l*V*r^-1, where
        # v is a list of the resource matrix's principal values (some of which may be 0),
        # the rows of r correspond to an orthonormal basis for the space of possible cycles, and the l matrix
        # is of no use to us.
        # We are interested in the rows of r that are null'd by multiplication with the resource matrix,
        # which in this decomposition correspond to the last d rows of r, where d is the difference
        # between the number of steps and the number of non-zero singular values
        
        l,v,r = np.linalg.svd(self.matrix[3:])
        
        # Calculate dimension of the kernel, based on number of vectors corresponding to null columns
        # plus number of vectors corresponding to null singular values.
        # np.isclose(v, 0, atol=5e-16) is a boolean array indicating whether each singular value is close enough
        # to zero so that the .sum() may count the number of Trues.
        self.grind_dim = self.dim1 - len(v) + np.isclose(v, 0, atol=5e-16).sum()
        
        # Calculates the total echo gain of each step, converting scrip to echoes through hambitrage.
        self.gain = self.matrix[1] + EPS*self.matrix[2]
        
        # If self.grind_dim == 1 that means there is only one possible solution,
        # stored as the last row of the r array.
        if self.grind_dim == 1:

            self.solution = r[-1]
            
        # If grind_dim == 0 that means that there is no way to chain all or some of these steps into a
        # self-sufficient cycle.
        
        elif self.grind_dim == 0:
            
            print('warning: grind not practicable (no solutions)')
            
        # If dim_grind > 1 that means there is an infinite number of possible solutions, all of which can
        # be represented as a linear combination of the last dim_grind rows of r (up to a scale factor);
        # we must use scipy.optimize.minimize to find the optimal one while imposing the reality constraint
        # of a positive number for all steps (they can't be undone!).
        
        else:
            
            self.basis = r[-self.grind_dim:].transpose() #basis for the resource matrix's nullspace
            # We need to find the linear combination of our basis vectors that maximizes epa, with the constraint
            # that it has to have all non-negative entries.

            # To do so we write a "calculate one over epa" function such that it takes as input the (self.grind_dim)
            # coefficients of said linear combination and use scipy.optimize.minimize to minimize it while respecting
            # our reality constraint.

            # Because minimize() only looks for local minima we choose the starting guess x_0
            # such that it is as close as possible to the all-positive np.ones(number of steps) vector, thus
            # improving the chances of it respecting our constraint; because self.basis is orthonormal this
            # can be easily implemented by summing over its rows using ndarray.sum(0).

            self.X = np.matmul(self.gain, self.basis)
            self.Y = np.matmul(self.matrix[0], self.basis)
            x_0 = self.basis.sum(0)
            reality_constr = LinearConstraint(self.basis, 0, +np.inf)
            result = minimize(self.calc_invepa, x_0, method='SLSQP', constraints=reality_constr)

            if result.success:
                
                print('optimization successful')
                self.solution = np.matmul(self.basis, result.x)

        actions = np.dot(self.solution, self.matrix[0])
        echoes = np.dot(self.solution, self.matrix[1])
        scrip = np.dot(self.solution, self.matrix[2])
        echoesTotal = np.dot(self.solution, self.gain)
        # scrip = np.dot(self.sol, self.matrix[2])
        self.epaTotal = echoesTotal / actions
        self.epa = echoes / actions
        self.spa = scrip / actions

        # Check that the solution found is a valid one and actually respects our reality constraint:
        # all entries need to either be zero (which is signalled, as it means that one step is superfluous) or
        # of the same sign as otherwise the grind would require some steps to be undone, which is obviously impossible.


        signs = np.sign(self.solution)  # array of signs of every entry in the solution
        check1 = np.abs(signs.sum())    # diff between number of positive entries and number of negative entries
        check2 = np.abs(signs).sum()    # number of non-zero entries

        if check1 != self.dim1:         # if check1 == dim1 all entries are of same sign so no issue, otherwise:

            if check2 < self.dim1:      # if check2 < dim1 some entries are zero
                print('warning: unnecessary step')
                
            if check1 != check2:        # if check1 != check2 then some nonzero entries have different signs
                print('erorr: grind not practicable')
                
    def calc_invepa(self, v):
        
        echoes = np.matmul(self.X, v)
        actions = np.matmul(self.Y, v)
        
        return actions/echoes
        
    # Prints the frequency of each step in the optimal cycle, relative to the first step in the list.
    # Example: if your grind consists of 'get whirring contraptions from wilmot's end' and 'publish a newspaper'
    # then the result will appear as:
    # 'get whirring contraptions from wilmot's end': 1.000000
    # 'publish a newspaper': 0.500000
    
    def print_ratios(self):
        
        for i in range(self.dim1):
            ratio = self.solution[i]/self.solution[0]
            print(self.steps[i] + ': %.15f' % ratio)

    def matrix(self, name='Actions'):
        if name in self.reses:
            return self.matrix[self.ref[name]]
        if name in self.steps:
            return self.matrix[:self.step_ref[name]]

def ranching(*args, stats, overflow_list=[], blacklist=None, add_parameters={'NO':0}):

    default = ['Get Mammoth', 'Get 7Necks', 'Generator Skeleton', 'Sell to Entrepreneur',
               'Sell to Palaeontologist', 'Sell to Zailor', 'Sell to Naive', 'Medium Larceny',
               'Painting', 'Upconvert MoDS']

    for lists in args:
        default = [*default, *lists]

    return Grind(stats, default, overflow_list, blacklist, add_parameters)
