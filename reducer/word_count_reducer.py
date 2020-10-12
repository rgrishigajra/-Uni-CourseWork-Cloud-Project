from collections import defaultdict
import marshal
import os
import sys
import re


def word_count_reducer(input_list):
    word_dict = defaultdict(int)
    for word in input_list:
        word_dict[word[0]] += int(word[1])
    word_list = [(key, word_dict[key]) for key in word_dict.keys()]
    word_list.sort()
    return word_list


code_string = marshal.dumps(word_count_reducer.__code__)
with open(os.path.join(sys.path[0], 'word_count_reducer_serialized'), 'wb') as fd:
    fd.write(code_string)
fd.close()
