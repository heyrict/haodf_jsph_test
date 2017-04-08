# coding: utf-8
def flip_dict(dict_to_flip):
    return dict([i[::-1] for i in dict_to_flip.items()])
def split_wrd(string,sep=None,rep=''):
    if type(rep)==str:
        for i in sep:
            string = rep.join(string.split(i))
        return string
    elif type(rep)==list:
        for i,j in zip(sep,rep):
            string = j.join(string.split(i))
        return string
    
