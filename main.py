from classifier.regex_classifier import RegexClassifier
from classifier.ngram_classifier import NgramClassifier
from datahandler import data_import as di
import re
import os
import numpy as np
from copy import deepcopy

if __name__ == "__main__":

    debug = False

    if not debug:
        print("Current data folder: {!r}\n".format(os.getenv('DATA_FOLDER')))
        filenames = [os.path.normpath(os.path.join(os.getenv('DATA_FOLDER'), 'smh.ctpa.140.xlsx'))]
        print("Files of interest: {!r}\n".format(filenames))
        #Reading excel data
        data, labels, ids = di.data_from_excel(filenames, data_cols=3, label_cols=12, id_cols=0, repeat_ids=False)
        print("\nTraining data tuples:\n")
        print(list(zip(data, labels, ids)))

        #Reading regex files
        regexes = {}

        regex_dir = os.path.join('examples', 'regexes', 'tb_regexes')
        regex_filenames = [os.path.join('examples', 'regexes', 'tb_regexes', fname) for fname in os.listdir(regex_dir)]

        # regexes = di.regexes_from_csv(filenames, use_customized_score=True)

        for file in regex_filenames:
            split_str = re.split(r'[\\]+', file)
            key_name = split_str[-1].split('.')[0]
            regexes[key_name] = di.regexes_from_csv([file], use_custom_score=True)

        print(regexes)
    else:
        data, labels, ids = [],[],[]

    #Creating TB Classifier
    # tb = NgramClassifier("TB Classifier 1")
    #
    # tb.import_data(data, labels, ids)
    #
    # #Setting all positive examples to 1
    # tb.labels[tb.labels == 'y'] = 1
    # tb.labels[tb.labels == 'n'] = 0
    #
    # #Removing that one example which has value 10 in the labels
    # tb.labels = tb.labels[:-1]
    # tb.data = tb.data[:-1]
    # tb.ids = tb.ids[:-1]
    #
    # tb.labels = tb.labels.astype(np.float)
    #
    # train_ids, valid_ids = tb.create_train_and_valid(.5, 0)
    # ids = {"train": train_ids, "valid": valid_ids}

    #Running TB Classifier
    # tb.run_classifier()

    regex_list = []
    [regex_list.extend(l) for l in regexes.values()]

    #Creating Regex Classifier
    tb_regex = RegexClassifier("TB Classifier Regex", regex_list)
    tb_regex.import_data(data, labels, ids)

    #Setting all positive examples to 1
    tb_regex.labels[tb_regex.labels == 'y'] = 1
    tb_regex.labels[tb_regex.labels == 'n'] = 0

    #Removing that one example which has value 10 in the labels
    tb_regex.labels = tb_regex.labels[:-1]
    tb_regex.data = tb_regex.data[:-1]
    tb_regex.ids = tb_regex.ids[:-1]

    tb_regex.labels = tb_regex.labels.astype(np.float)

    train_ids_regex, valid_ids_regex = tb_regex.create_train_and_valid(0.5,0)
    ids_regex = {"train": train_ids_regex, "valid": valid_ids_regex}

    #Running TB Classifier
    tb_regex.run_classifier()