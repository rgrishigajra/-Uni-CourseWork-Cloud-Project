from collections import defaultdict
import marshal
import os
import sys
import re


def inverted_index_reducer(input_list):
    word_dict = defaultdict(lambda: defaultdict(int))
    for word in input_list:
        word_dict[word[0]][word[1]] += 1
    word_list = []
    for word in word_dict.keys():
        val=''
        for fil in word_dict[word].keys():
            val+=str(fil)+":"+str(word_dict[word][fil])+','
        word_list.append((word, val[:-1]))
    word_list.sort()
    return word_list


code_string=marshal.dumps(inverted_index_reducer.__code__)
with open(os.path.join(sys.path[0], 'inverted_index_reducer_serialized'), 'wb') as fd:
    fd.write(code_string)
fd.close()
