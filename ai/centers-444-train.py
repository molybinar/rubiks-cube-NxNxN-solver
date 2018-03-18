#!/usr/bin/env python3

import logging
import pandas
import sys
#from pandas.plotting import scatter_matrix
#import matplotlib.pyplot as plt
from sklearn import model_selection
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
#from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
#from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
#from sklearn.naive_bayes import GaussianNB
#from sklearn.svm import SVC
#from sklearn import preprocessing
from pprint import pformat
import pickle

log = logging.getLogger(__name__)


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')

    # Load dataset
    names = ['UD', 'LR', 'FB',
             'UF', 'UL', 'UR', 'UB',
             'LF', 'LB', 'LD', 
             'FR', 'FD',
             'RB', 'RD',
             'BD',
             'OutOfPlace', 'Unpaired', 'move-count']
    filename = 'centers-444-train.data'

    log.info("loading dataset")
    dataset = pandas.read_csv(filename, names=names)
    log.info("loading dataset complete")

    # shape
    print(dataset.shape)

    # head
    print(dataset.head(20))

    # descriptions
    print(dataset.describe())
    print("\n\n")

    # class distribution
    #print(dataset.groupby('class').size())

    # box and whisker plots
    #dataset.plot(kind='box', subplots=True, layout=(2,2), sharex=False, sharey=False)
    #plt.show()

    # histograms
    #dataset.hist()
    #plt.show()


    # scatter plot matrix
    #scatter_matrix(dataset)
    #plt.show()


    # Split-out validation dataset
    DATA_COLUMNS_COUNT = 17

    array = dataset.values
    X = array[:,0:DATA_COLUMNS_COUNT]
    Y = array[:,DATA_COLUMNS_COUNT]
    #validation_size = 0.20
    validation_size = 0.05
    seed = 7

    (X_train, X_validation, Y_train, Y_validation) =\
        model_selection.train_test_split(X, Y, test_size=validation_size, random_state=seed)
    #log.info("pre : %s" % pformat(X_train))
    #X_train = preprocessing.scale(X_train)
    #X_validation = preprocessing.scale(X_validation)

    #X_train = preprocessing.normalize(X_train)
    #X_validation = preprocessing.normalize(X_validation)

    #Y_train = preprocessing.scale(Y_train)
    #Y_validation = preprocessing.scale(Y_validation)
    #log.info("post: %s" % pformat(X_train))

    # Test options and evaluation metric
    scoring = 'accuracy'

    # Spot Check Algorithms
    models = []
    #models.append(('LR', LogisticRegression()))
    #models.append(('LDA', LinearDiscriminantAnalysis()))
    #models.append(('KNN', KNeighborsClassifier()))
    models.append(('CART', DecisionTreeClassifier()))
    #models.append(('NB', GaussianNB()))
    #models.append(('SVM', SVC()))

    # evaluate each model in turn
    '''
    results = []
    names = []
    for (name, model) in models:
        log.info("eval %s" % name)
        kfold = model_selection.KFold(n_splits=10, random_state=seed)
        cv_results = model_selection.cross_val_score(model, X_train, Y_train, cv=kfold, scoring=scoring)
        results.append(cv_results)
        names.append(name)
        msg = "%4s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
        print(msg)

    print("\n\n\n")

    # Compare Algorithms
    fig = plt.figure()
    fig.suptitle('Algorithm Comparison')
    ax = fig.add_subplot(111)
    plt.boxplot(results)
    ax.set_xticklabels(names)
    plt.show()
    '''

    # Make predictions on validation dataset
    cart = DecisionTreeClassifier()
    log.info('fit begin')
    cart.fit(X_train, Y_train)
    log.info('fit end')
    log.info('predictions begin')
    predictions = cart.predict(X_validation)
    log.info('predictions end...pickle to disk')

    # save the model to disk
    filename = 'nn-centers-444.pkl'
    pickle.dump(cart, open(filename, 'wb'))
    #sys.exit(0)

    print(classification_report(Y_validation, predictions))

    stats = {}

    for (predicted, actual) in zip(predictions, Y_validation):
        if actual not in stats:
            stats[actual] = {}

        if predicted not in stats[actual]:
            stats[actual][predicted] = 0

        stats[actual][predicted] += 1

    for actual in sorted(stats.keys()):
        print("Actual\tPredic\tPercent")
        total_count = 0

        for predicted in stats[actual].keys():
            total_count += stats[actual][predicted]

        for predicted in sorted(stats[actual].keys()):
            count = stats[actual][predicted]
            print("%d\t%d\t%s" % (actual, predicted, float(count/total_count) * 100))
        print("")
