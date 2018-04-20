def max_classify(class_matches, class_captures, class_capture_scores, negative_label="None"):
    del(class_capture_scores['None'])
    return max(class_capture_scores, key=int) if len(class_capture_scores) > 0 else negative_label


def min_classify(class_matches, class_captures, class_capture_scores, negative_label="None"):
    return min(class_capture_scores, key=int) if class_capture_scores else negative_label


# ONLY WORKS IF NOT USING RE.ITER AND 1 CAPTURE
def sputum_classify(class_matches, class_captures, class_capture_scores, negative_label="None"):
    sputum_matches = class_matches["Sputum conversion"]
    date_matches = class_matches["Sputum Date"]

    if all(map(lambda case: not case, sputum_matches)):
        return negative_label

    for case_index, case_matches in enumerate(sputum_matches):
        case_matches_values = case_matches.values()

        if not case_matches_values:
            continue

        # print(case_matches_values)
        for i, sentence_matches in enumerate(case_matches_values):
            # print(sentence_matches)
            matches = sentence_matches["matches"]
            for match in matches:
                if match["name"] == "reg0-Sputum conversion":
                    print("HERE")
                    return match["matches"][0].groups(0)[0]

            sentence = None
            for match in matches:
                for secondary_match in match["secondary_matches"]:
                    if secondary_match["effect"] == "r" and secondary_match["pattern"] == ".*":
                        sentence = secondary_match["matches"][0].group()

            print(sentence)

    return negative_label

