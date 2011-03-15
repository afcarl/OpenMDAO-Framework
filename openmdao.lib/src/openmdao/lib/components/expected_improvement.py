"""Expected Improvement calculation for one or more objectives.""" 

from numpy import exp, abs, pi
from scipy.special import erf

from openmdao.lib.datatypes.api import Instance, Str, Float

from openmdao.main.api import Component

from openmdao.main.interfaces import ICaseIterator
from openmdao.main.uncertain_distributions import NormalDistribution


class ExpectedImprovement(Component):
    best_case = Instance(ICaseIterator, iotype="in",
                    desc="CaseIterator which contains a single case, "
                         "representing the criteria value.", required=True)
    
    criteria = Str(iotype="in",
                    desc="Name of the variable to maximize the expected "
                         "improvement around. Must be a NormalDistrubtion type.")
    
    predicted_value = Instance(NormalDistribution,iotype="in",
                               desc="the Normal Distribution of the predicted value for some \
                               function at some point where you wish to calculate the EI.")
    
    EI = Float(0.0, iotype="out", desc="The expected improvement of the "
                                       "predicted_value")
    
    PI = Float(0.0, iotype="out", desc="The probability of improvement of the predicted_value")
    
    def execute(self): 
        """ Calculates the expected improvement of the model at a given point.
        """
        
        mu = self.predicted_value.mu
        sigma = self.predicted_value.sigma
        best_case = self.best_case[0]
        target = False
        for output in best_case.outputs: 
            if output[0] == self.criteria: 
                #TODO: check that criteria is only one thing, error if not
                target = output[2]
                break
                
        if target is False: 
            self.raise_exception("best_case did not have an output which "
                                 "matched the criteria, '%s'"%self.criteria,
                                 ValueError)  
        try:
            
            self.PI = 0.5+0.5*erf((1/2**.5)*(target-mu/sigma))
            
            T1 = (target-mu)*.5*(1.+erf((target-mu)/(sigma*2.**.5)))
            T2 = sigma*((1./((2.*pi)**.05))*exp(-0.5*((target-mu)/sigma)**2.))
            self.EI = abs(T1+T2)
        except (ValueError,ZeroDivisionError): 
            self.EI = 0
            self.PI = 0
            
        #print "ei: ", self.EI
            
            
    
    
