# -*- coding: utf-8 -*-
# python 3.7.0

import re
def sort_key(s):
    #sort_strings_with_embedded_numbers
    re_digits = re.compile(r'(\d+)')
    # 切成数字与非数字
    pieces = re_digits.split(s)  
    # 将数字部分转成整数
    pieces[1::2] = map(int, pieces[1::2])  
    return pieces

#测试数据：
# _list = [
#     'W6_010_1.jpg',
#     'WA6_000_10.jpg',
#     'W6_000_22.jpeg',
#     'W6_000_2.jpg',
#     'W6_000_03.jpg'
# ]
# _list.sort(key=sort_key)
# print(_list)
# print(sorted(_list,key=sort_key))