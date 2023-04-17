# encoding: utf-8
#! /usr/bin/python
import os
import sys

imag_folder_path = sys.argv[1]  # 指定文件夹路径
md_out_file = sys.argv[2]  # 指定文件夹路径

# 遍历文件夹内所有文件
for file_name in os.listdir(imag_folder_path):
    if file_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".JPG")):
        # 包装成Markdown语法的图片引用格式
        markdown_str = "![{}]({})".format(file_name, file_name)
        print(markdown_str)  # 输出Markdown字符串
        # 或者保存到文件中
        with open(md_out_file, "a") as f:
            f.write(markdown_str + "\n")

# eg: python imag-to-md.py source/_posts/2023/04/北京 source/_posts/2023/04/北京.md