import sys
import json

from variable_classifiers.base_runner import Runner
from datahandler import data_import as di
import numpy as np
import functools
import os
from web.report_generator import generate_error_report
from stats.basic import calculate_accuracy
from sklearn.metrics import confusion_matrix
from stats.basic import plot_confusion_matrix, get_classification_stats, compute_ppv_accuracy_ova, \
    compute_ppv_accuracy_capture, get_classification_stats_capture
from datahandler.helpers import import_regex, import_regexes
from datahandler.preprocessors import replace_filter_by_label, replace_labels_with_required, \
    replace_label_with_required, replace_filter, convert_repeated_data_to_sublist
from classifier.classification_functions import sputum_classify, max_classify, max_month
from util.tb_country import preprocess
from util.pwd_preprocessors import PwdPreprocessor2

import os
import sys
orig_stdout = sys.stdout
f = open(os.devnull, 'w')
#sys.stdout = f
os.environ['DATA_FOLDER'] = "Z:\\GEMINI-SYNCOPE\\NLP Validation Project\\training\\fixed set"
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
# Define after imports and globals
available_funcs = {}


def exposed_function(func):
    available_funcs[getattr(func,'__name__')] = func


'''
####
Expose certain functions that allow the following:
- Run classifier
- Change variable, datafiles/columns and labelfiles/columns
- 
####
'''
# simple JSON echo script


def respond(message):
    if not type(message) == dict:
        message = {'message': message}
    print(json.dumps(message), file=orig_stdout)
    orig_stdout.flush()


# MAIN RUNNING CODE

def create_regex_based_classifier(rule_path=None):
    """Creates a Regex based classifier Runner object which is later used to run the classifier

    Arguments:
        rule_path {String} -- Path to the rule directory (in the case of multiclass classification)
            or a rule file (in the case of single class classificatoin)
        ids_list {list} -- List of ids
        data_list {list} -- List of data (string) for each id

    Keyword Arguments:
        labels_list {list} -- List of labels (default: {None})
        training_mode {bool} -- Whether to run the classifier in training mode. If in training mode creates training
            and validation datasets (default: {False})
        l_id_col {int} -- Column in which label_file's ids are located starting from 0 (default: {None})
        l_label_col {int} -- Column in which label_file's labels are located starting from 0 (default: {None})
        l_first_row {int} -- From which row to start reading the data (default: {None})
        label_file {String} -- Path pointing to label file (default: {None})
        repeat_ids {bool} -- If False, ids are not considered unique and the data is appended (default: {False})
        train_percent {float} -- Percentage of training examples (default: {0.6})

    Returns:
        classifier_runner {Runner} -- Returns a Runner object which is used to run the classifier
    """

    # Import rule directory or rule file and updating classifier_args
    # Creating the Runner object with specified classifier_args
    classifier_type, classifier_args, regexes_dict = import_regexes(rule_path) \
        if os.path.isdir(rule_path) else import_regex(rule_path)
    classifier_args.update({"regexes": regexes_dict})
    runner = Runner(classifier_type, **classifier_args)

    return runner


def load_classifier_data(runner, classifier_data_list, labels_list, classifier_ids_list, dataset=None,
                         create_train_valid=False, train_percent=.6, random_seed=0):
    # If training is enabled
    # Storing data within classifier and creating validation and training sets
    classifier_data_list = np.array(classifier_data_list) if classifier_data_list else None
    labels_list = np.array(labels_list) if labels_list else [None] * len(classifier_data_list)
    classifier_ids_list = np.array(classifier_ids_list) if classifier_ids_list else [None] * len(classifier_data_list)

    if not create_train_valid:
        runner.classifier.load_dataset(dataset, data=classifier_data_list, labels=labels_list, ids=classifier_ids_list)
    else:
        runner.classifier.create_train_and_valid(data=classifier_data_list, labels=labels_list, ids=classifier_ids_list,
                                                 train_percent=train_percent, random_seed=random_seed)
    return runner


@exposed_function
def run_variable(variable):
    debug = False

    print_none = False
    print_minimal = False
    print_verbose = False

    # Web setup
    template_directory = os.path.join('web', 'templates')
    effects = ["a", "aa", "ab", "r", "rb", "ra"]
    effect_colours = dict.fromkeys(["a", "aa", "ab"], "rgb(0,0,256)")
    effect_colours.update(dict.fromkeys(["r", "rb", "ra"], "rgb(256,0,0)"))

    # Setup code
    pwds = di.import_pwds([os.path.join("dictionaries", dict_name) for dict_name in os.listdir("dictionaries")])

    # filename = os.path.join(os.getenv('DATA_FOLDER'), 'ctpa', 'all0.xlsx')
    # filename = os.path.join(os.getenv('DATA_FOLDER'), 'all.xlsx')
    filenames = {}
    filenames["ctpa"] = [os.path.join(os.getenv('DATA_FOLDER'), 'ctpa', file) for file in os.listdir(os.path.join(os.getenv('DATA_FOLDER'), "ctpa")) if ('~' not in file and file.endswith('.xlsx'))]
    filenames["vq"] = [os.path.join(os.getenv('DATA_FOLDER'), "vq", "all.xlsx")]
    filenames["dvt_iterative"] = [os.path.join(os.getenv('DATA_FOLDER'), "du", "all0.xlsx")]
    label_files_dict = dict()
    #print(os.getenv('DATA_FOLDER'))
    vq_label_filename = os.path.join(os.getenv('DATA_FOLDER'), "vq","all.xlsx")
    rules_path = os.path.join(os.getenv('DATA_FOLDER'), 'Regexes')

    dvt_label_filename = os.path.join(os.getenv('DATA_FOLDER'), "du","all0.xlsx")

    # loading data
    if not debug:
        print(filenames)
        data_loader = di.data_from_csv if filenames[variable][0].endswith('.csv') else di.data_from_excel
        print(data_loader)
        data_list, _, ids_list = data_loader(filenames[variable], data_cols=2, first_row=1, id_cols=1, repeat_ids=False)
    else:
        pass
    # TODO: Update Headers
    ctpa_rules = rules_path
    file_to_args = {"dvt_iterative": {"Runner Initialization Params": {"l_label_col": 4, "l_id_col": 1, "l_first_row": 1},
                                      "label_file": dvt_label_filename},
                    "vq": {"Runner Initialization Params": {"l_label_col": 5, "l_id_col": 0, "l_first_row": 1,
                                                            "label_file": vq_label_filename}}
                    }
    datasets = ["train", "valid"]

    for each in file_to_args:
        if each == variable or each == variable + ".txt":
            variable = each
            break
    cur_run = [variable]
    # cur_run = ["inh_medication_2.txt"]

    # TODO: Add functools label_funcs for some of the classifiers
    # TODO: Use country preprocessor from old code
    row_start = {"train": 29,
                 "valid": 20,
                 "test": 53
                 }


    label_files_dict["train"] = os.path.join(os.getenv('DATA_FOLDER'), 'ctpa', 'train.csv')
    label_files_dict["valid"] = os.path.join(os.getenv('DATA_FOLDER'), 'ctpa', 'valid.csv')

    # excel_column_headers = ["Ids"]
    for rule in cur_run:
        rule_name = rule.split(sep=".txt")[0]

        print("=" * 100)
        rule_file = os.path.join(ctpa_rules, rule)

        classifier_runner = create_regex_based_classifier(rule_file)
        cur_params = file_to_args[rule]["Runner Initialization Params"]
        if "data_list" not in cur_params:
            cur_params["data_list"] = data_list
        if "ids_list" not in cur_params:
            cur_params["ids_list"] = ids_list

        data = {}
        labels = {}
        ids = {}
        if "label_file" in cur_params:
            print("HEREEEEEE")
            ids["all"], data["all"], labels["all"] = di.get_labeled_data(**cur_params)
            print("NOT HEREEEEEE")
            classifier_runner = load_classifier_data(classifier_runner, data["all"], labels['all'], ids["all"],
                                                     create_train_valid=True, train_percent=.6, random_seed=0)
        else:
            for cur_dataset in datasets:
                if "use_row_start" in file_to_args[rule]:
                    cur_params['l_first_row'] = row_start[cur_dataset]
                cur_params["label_file"] = label_files_dict[cur_dataset]
                ids[cur_dataset], data[cur_dataset], labels[cur_dataset] = di.get_labeled_data(**cur_params)
                classifier_runner = load_classifier_data(classifier_runner, data[cur_dataset], labels[cur_dataset],
                                                         ids[cur_dataset], dataset=cur_dataset)
        for cur_dataset in datasets:
            all_classifications = []
            print("\nRunning on rule: {} - {}".format(rule_name, cur_dataset))

            # classifier_runner.classifier.dataset[cur_dataset]["ids"] = [classifier_runner.classifier.dataset[cur_dataset]["ids"][2]]
            # classifier_runner.classifier.dataset[cur_dataset]["data"] = [classifier_runner.classifier.dataset[cur_dataset]["data"][2]]
            if "Runtime Params" in file_to_args[rule]:
                classifier_runner.run(datasets=[cur_dataset], **file_to_args[rule]["Runtime Params"])
            else:
                classifier_runner.run(datasets=[cur_dataset])

            failures_dict = {}
            print(classifier_runner.classifier.dataset[cur_dataset]["labels"].tolist())
            cur_labels_list = sorted(list(set(classifier_runner.classifier.dataset[cur_dataset]["preds"].tolist()) |
                                          set(classifier_runner.classifier.dataset[cur_dataset]["labels"].tolist())))
            accuracy, \
            incorrect_indices = calculate_accuracy(classifier_runner.classifier.dataset[cur_dataset]["preds"],
                                                   classifier_runner.classifier.dataset[cur_dataset]["labels"])

            print("\nAccuracy: ", accuracy)
            print("\nIds: ", classifier_runner.classifier.dataset[cur_dataset]["ids"])
            print("Predictions: ", classifier_runner.classifier.dataset[cur_dataset]["preds"])
            print("Labels: ", classifier_runner.classifier.dataset[cur_dataset]["labels"])

            print("\nIncorrect Ids: ", classifier_runner.classifier.dataset[cur_dataset]["ids"][incorrect_indices])
            print("Incorrect Predictions: ",
                  classifier_runner.classifier.dataset[cur_dataset]["preds"][incorrect_indices])
            print("Incorrect Labels: ", classifier_runner.classifier.dataset[cur_dataset]["labels"][incorrect_indices])

            classifier_type = classifier_runner.classifier_type.__name__
            classifier_classes = sorted(list(classifier_runner.classifier_parameters["regexes"]))

            if classifier_type == "CaptureClassifier":
                cnf_matrix = None


                ppv_and_accuracy = compute_ppv_accuracy_capture(
                    classifier_runner.classifier.dataset[cur_dataset]["labels"],
                    classifier_runner.classifier.dataset[cur_dataset]["preds"],
                    classifier_classes, classifier_runner.classifier.negative_label)

                predicted_positive, positive_cases, predicted_negative_cases, negative_cases, \
                false_positives, false_negatives = get_classification_stats_capture(
                    classifier_runner.classifier.dataset[cur_dataset]["labels"],
                    classifier_runner.classifier.dataset[cur_dataset]["preds"],
                    classifier_classes, classifier_runner.classifier.negative_label)

                cur_labels_list = classifier_classes

            else:

                cnf_matrix = confusion_matrix(classifier_runner.classifier.dataset[cur_dataset]["labels"],
                                              classifier_runner.classifier.dataset[cur_dataset]["preds"])
                ppv_and_accuracy = compute_ppv_accuracy_ova(cnf_matrix, cur_labels_list)
                predicted_positive, positive_cases, predicted_negative_cases, negative_cases, \
                false_positives, false_negatives = get_classification_stats(cnf_matrix, cur_labels_list)

            print("Confusion Matrix: ")

            print("OVA PPV and Accuracy: ", ppv_and_accuracy)

            print("Number of Positive Predictions: ", predicted_positive)
            print("Actual number of Positive Cases: ", positive_cases)
            print("Number of Predicted Negative Cases: ", predicted_negative_cases)
            print("Actual Number of Negative Cases: ", negative_cases)

            for index in incorrect_indices:
                cur_patient_id = classifier_runner.classifier.dataset[cur_dataset]["ids"][index]
                cur_pred = classifier_runner.classifier.dataset[cur_dataset]["preds"][index]
                cur_label = classifier_runner.classifier.dataset[cur_dataset]["labels"][index]
                cur_match_obj = classifier_runner.classifier.dataset[cur_dataset]["matches"][index]
                cur_score = classifier_runner.classifier.dataset[cur_dataset]["scores"][index]
                cur_text = classifier_runner.classifier.dataset[cur_dataset]["data"][index]

                failures_dict[cur_patient_id] = {"label": cur_label, "data": cur_text, "pred": cur_pred,
                                                 "matches": cur_match_obj, "score": cur_score}

            if not all_classifications:
                all_classifications.append(classifier_runner.classifier.dataset[cur_dataset]["ids"].tolist())

            all_classifications.append(classifier_runner.classifier.dataset[cur_dataset]["preds"].tolist())

            if cur_dataset != "test":
                all_classifications.append(classifier_runner.classifier.dataset[cur_dataset]["labels"].tolist())

            # excel_column_headers.append(file_to_header[rule])
            # excel_column_headers.append("Label")

            gen_path = os.path.join("generated_data", rule_name, cur_dataset)

            if not os.path.exists(gen_path):
                os.makedirs(gen_path)

            # TODO: FIX STAT CREATION FOR CAPTURE CLASSIFIERS
            error_data = {"Predicted Positive": predicted_positive, "Positive Cases": positive_cases,
                          "Predicted Negative": predicted_negative_cases, "Negative Cases": negative_cases,
                          "False Positives": false_positives, "False Negatives": false_negatives,
                          "Confusion Matrix": cnf_matrix.tolist() if cnf_matrix is not None else [],
                          "OVA PPV and Accuracy": ppv_and_accuracy, "Ordered Labels": cur_labels_list,
                          "Negative Label": classifier_runner.classifier.negative_label,
                          "Classifier Type": classifier_type}

            custom_class_colours = None

            if len(classifier_classes) == 2:
                negative_label = classifier_runner.classifier.negative_label
                positive_label = next(filter(lambda i: i != negative_label, classifier_classes))
                custom_class_colours = {negative_label: "hsl({},{}%,{}%)".format(15,71.4,89),
                                        positive_label: "hsl({},{}%,{}%)".format(97,81,91.8)}

            generate_error_report(os.path.join("generated_data", rule_name, cur_dataset),
                                  template_directory, "{}".format(rule_name),
                                  classifier_runner.classifier.regexes.keys(), failures_dict, effects,
                                  custom_effect_colours=effect_colours, addition_json_params=error_data,
                                  custom_class_colours=custom_class_colours)

            conf_path = os.path.join("generated_data", rule_name, cur_dataset)

            if cnf_matrix is not None:
                plot_confusion_matrix(cnf_matrix, cur_labels_list, conf_path)

            # de.export_data_to_excel("{}.xlsx".format(excel_path), all_classifications, headers, mode="r")

def run(**kwargs):
    respond({'function': 'run', 'params': kwargs})

def save(**kwargs):
    respond({'function': 'save', 'params': kwargs})

x = {}
x['function'] = "run_variable"
x['params'] = {"variable": "dvt_iterative"}
available_funcs[x['function']](**x['params'])
exit()
# respond({'status': 'Ready'})
for line in sys.stdin:
    x = json.loads(line)
    if x['function'] in available_funcs:
        available_funcs[x['function']](**x['params'])
        #    respond(available_funcs)
        # sys.stdout.flush()
        # globals()[x['function']](**x['params'])
        #print(json.dumps(json.loads(line)))
        respond({'status': 200})
    else:
        respond({'status': 404})
