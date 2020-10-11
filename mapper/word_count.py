from collections import defaultdict
import marshal
import os
import sys
import re


def word_count(key, value):
    words = re.findall(r'\w+', value)
    word_dict = defaultdict(int)
    for word in words:
        word_dict[word.lower()] += 1
    word_list = [(key, word_dict[key]) for key in word_dict.keys()]
    return word_list


code_string = marshal.dumps(word_count.__code__)
with open(os.path.join(sys.path[0], 'word_count_serialized'), 'wb') as fd:
    fd.write(code_string)
fd.close()
