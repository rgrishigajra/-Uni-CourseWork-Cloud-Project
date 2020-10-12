from collections import defaultdict
import marshal
import os
import sys
import re


def inverted_index_mapper(key, value):
    words = re.findall(r'\w+', value)
    word_dict = defaultdict(list)
    word_list = []
    for word in words:
        if word.isdigit():
            continue
        word_list.append((word.lower(), key))
    return word_list


code_string = marshal.dumps(inverted_index_mapper.__code__)
with open(os.path.join(sys.path[0], 'inverted_index_mapper_serialized'), 'wb') as fd:
    fd.write(code_string)
fd.close()
