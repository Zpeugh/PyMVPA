### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#    Unit tests for PyMVPA pattern handling
#
#    Copyright (C) 2007 by
#    Michael Hanke <michael.hanke@gmail.com>
#
#    This package is free software; you can redistribute it and/or
#    modify it under the terms of the MIT License.
#
#    This package is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the COPYING
#    file that comes with this package for more details.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import unittest
import numpy as N
import mvpa.maskeddataset
import mvpa.crossval
import mvpa.knn as knn
import mvpa.nfoldsplitter
import mvpa.mmatchprocessor

def pureMultivariateSignal(patterns, origin, signal2noise = 1.5):
    """ Create a 2d dataset with a clear multivariate signal, but no
    univariate information.

    %%%%%%%%%
    % O % X %
    %%%%%%%%%
    % X % O %
    %%%%%%%%%
    """

    # start with noise
    data=N.random.normal(size=(4*patterns,2))

    # add signal
    data[:2*patterns,1] += signal2noise
    data[2*patterns:4*patterns,1] -= signal2noise
    data[:patterns,0] -= signal2noise
    data[2*patterns:3*patterns,0] -= signal2noise
    data[patterns:2+patterns,0] += signal2noise
    data[3*patterns:4*patterns,0] += signal2noise

    # two conditions
    regs = [0 for i in xrange(patterns)] \
        + [1 for i in xrange(patterns)] \
        + [1 for i in xrange(patterns)] \
        + [0 for i in xrange(patterns)]
    regs = N.array(regs)

    return mvpa.maskeddataset.MaskedDataset(data, regs, origin)


class CrossValidationTests(unittest.TestCase):

    def getMVPattern(self, s2n):
        run1 = pureMultivariateSignal(5, 1, s2n)
        run2 = pureMultivariateSignal(5, 2, s2n)
        run3 = pureMultivariateSignal(5, 3, s2n)
        run4 = pureMultivariateSignal(5, 4, s2n)
        run5 = pureMultivariateSignal(5, 5, s2n)
        run6 = pureMultivariateSignal(5, 6, s2n)

        data = run1 + run2 + run3 + run4 + run5 + run6

        return data


    def testSimpleNMinusOneCV(self):
        data = self.getMVPattern(3)

        self.failUnless( data.nsamples == 120 )
        self.failUnless( data.nfeatures == 2 )
        self.failUnless(
            (data.labels == [0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0]*6 ).all() )
        self.failUnless(
            (data.chunks == \
                [ k for k in range(1,7) for i in range(20) ] ).all() )


        cv = mvpa.crossval.CrossValidation( 
                mvpa.nfoldsplitter.NFoldSplitter(cvtype=1),
                knn.kNN(),
                mvpa.mmatchprocessor.MeanMatchProcessor() )

        results = cv(data)
        self.failUnless( N.mean(results) > 0.8 and N.mean(results) <= 1.0 )
        self.failUnless( len( results ) == 6 )


    def testNoiseClassification(self):
        # get a dataset with a very high SNR
        data = self.getMVPattern(10)

        # do crossval
        cv = mvpa.crossval.CrossValidation( 
                mvpa.nfoldsplitter.NFoldSplitter(cvtype=1),
                knn.kNN(),
                mvpa.mmatchprocessor.MeanMatchProcessor() )
        results = cv(data)

        # must be perfect
        self.failUnless( N.array(results).mean() == 1.0 )

        # do crossval with permutated regressors
        cv = mvpa.crossval.CrossValidation( 
                mvpa.nfoldsplitter.NFoldSplitter(cvtype=1, permutate=True),
                knn.kNN(),
                mvpa.mmatchprocessor.MeanMatchProcessor() )
        results = cv(data)

        # must be at chance level
        pmean = N.array(results).mean()
        self.failUnless( pmean < 0.58 and pmean > 0.42 )


def suite():
    return unittest.makeSuite(CrossValidationTests)


if __name__ == '__main__':
    unittest.main()

