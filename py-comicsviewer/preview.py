# -*- coding: utf-8 -*-
# python 3.7.0

import os
import shelve
import urllib.parse
import os
import copy
import time
from PIL import Image

from fun import mysqlite as sqlite
from fun import re_sort
from fun.log import get_logger

log = get_logger(__name__, 'ERROR')

class imageResize(object):
    def __init__(self,filepath):
        self.origin = filepath
        self.IMG_SUFFIX = [".jpg", ".png", ".jpeg", ".gif"]
        self.img =[]
        self.no_index = True
        self.no_preview = True

    def get_outfile(self, infile):
        dir, suffix = os.path.splitext(infile)
        dir,basename = os.path.split(infile)
        outfile = os.path.join(dir,f"preview{suffix}")
        return outfile
    
    def get_size(self, file):
        # 获取文件大小:KB
        size = os.path.getsize(file)
        return size / 1024
    
    def compress_image(self, infile, outfile='', mb=150, step=10, quality=80):
        """不改变图片尺寸压缩到指定大小
        :param infile: 压缩源文件
        :param outfile: 压缩文件保存地址
        :param mb: 压缩目标，KB
        :param step: 每次调整的压缩比率
        :param quality: 初始压缩比率
        :return: 压缩文件地址，压缩文件大小
        """
        o_size = self.get_size(infile)
        if o_size <= mb:
            return infile
        outfile = self.get_outfile(infile)
        while o_size > mb:
            im = Image.open(infile)
            im.save(outfile, quality=quality)
            if quality - step < 0:
                break
            quality -= step
            o_size = self.get_size(outfile)
        return outfile

    def resize_image(self, infile, outfile='', x_s=800):
        """修改图片尺寸
        :param infile: 图片源文件
        :param outfile: 重设尺寸文件保存地址
        :param x_s: 设置的宽度
        :return:
        """
        im = Image.open(infile)
        x, y = im.size
        y_s = int(y * x_s / x)
        out = im.resize((x_s, y_s), Image.LANCZOS)
        outfile = self.get_outfile(infile)
        out.save(outfile)

    def createImgList(self):
        imgs = []
        for _dir in os.listdir(self.origin):
            if(os.path.splitext(_dir)[0].startswith('.')):
                continue
            if 'preview' in _dir and not os.path.isdir(_dir):
                self.no_preview = False
                continue
            if '_index.html' == _dir:
                self.no_index = False
                continue
            if os.path.splitext(_dir)[1].lower() in self.IMG_SUFFIX:
                imgs.append(_dir)
        try:
            imgs.sort(key=re_sort.sort_key)
            pass
        except:
            imgs.sort()
            pass
        self.img = imgs
    
    def createContentHtml(self):
        try:
            if len(self.img) == 0 or self.img == None:
                return
            html='<!DOCTYPE html><html><head> <meta charset="UTF-8"> <!--==============手机端适应============--> <meta name="viewport" content="width=device-width,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no"> <!--===================================--> <meta name="description" content=""> <meta name="author" content=""> <!--==============强制双核浏览器使用谷歌内核============--> <meta name="renderer" content="webkit" /> <meta name="force-rendering" content="webkit" /> <meta http-equiv="Content-Type" content="text/html; charset=utf-8" /> <meta name="format-detection" content="telephone=no"> <meta name="referrer" content="never"> <title>Comicsviewer</title> <link rel="stylesheet" href="/h/css/swiper-bundle.min.css" /> <!-- Demo styles --> <style> html, body { position: relative; height: 100%; } body { background: #eee; font-family: Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 14px; color: #000; margin: 0; padding: 0; } .swiper { width: 100%; height: 100%; } .swiper-slide { text-align: center; font-size: 18px; background: #000; overflow: hidden; /* Center slide text vertically */ display: -webkit-box; display: -ms-flexbox; display: -webkit-flex; display: flex; -webkit-box-pack: center; -ms-flex-pack: center; -webkit-justify-content: center; justify-content: center; -webkit-box-align: center; -ms-flex-align: center; -webkit-align-items: center; align-items: center; } /* .swiper-slide img { width: auto; height: auto; max-width: 100%; max-height: 100%; -ms-transform: translate(-50%, -50%); -webkit-transform: translate(-50%, -50%); -moz-transform: translate(-50%, -50%); transform: translate(-50%, -50%); position: absolute; left: 50%; top: 50%; } */ .swiper .swiper-button-hidden { opacity: 0; } .swiper .swiper-button-next, .swiper .swiper-button-prev { right:0; left: 0; margin: 0 auto; outline: none; transform: rotate(90deg); -ms-transform: rotate(90deg); -moz-transform: rotate(90deg); -webkit-transform: rotate(90deg); -o-transform: rotate(90deg); } .swiper .swiper-button-next { top:auto; bottom: 22px; } .swiper .swiper-button-prev{ top:22px; bottom: auto; } </style></head><body> <!-- Swiper --> <div style="--swiper-navigation-color: #fff; --swiper-pagination-color: #fff" class="swiper mySwiper"> <div class="swiper-wrapper"> {% img_list %} </div> <div class="swiper-button-next"></div> <div class="swiper-button-prev"></div> <div class="swiper-pagination"></div> </div> <!-- Swiper JS --> <script type="text/javascript" src="/h/js/swiper-bundle.min.js"></script> <!-- Initialize Swiper --> <script> var swiper = new Swiper(".mySwiper", { zoom: true, direction: "vertical", keyboard: { enabled: true, }, lazy: { loadPrevNext: true, }, hashNavigation: { watchState: true, }, pagination: { el: ".swiper-pagination", type: "progressbar", clickable: true, }, navigation: { nextEl: ".swiper-button-next", prevEl: ".swiper-button-prev", hideOnClick: true, }, }); </script></body></html>'
            imgList = ''
            for i in range(len(self.img)):
                imgList+='<div data-hash="slide'+str(i)+'" class="swiper-slide"><div class="swiper-zoom-container"><img loading="lazy" src="'+self.img[i]+'" class="swiper-lazy" /></div><div class="swiper-lazy-preloader swiper-lazy-preloader-white"></div></div>'
            html = html.replace('{% img_list %}',imgList)
            with open(os.path.join(self.origin,'_index.html'),'w',encoding="utf-8") as w:
                w.write(html)
            return True
        except:
            log.error('生成html失败')
            pass
    
    def createPreviewImg(self):
        try:
            if len(self.img) == 0 or self.img == None:
                return
            basename = os.path.basename(self.img[0])
            if not 'preview' in basename:
                log.critical('生成封面缩略图...')
                outfile = self.compress_image(os.path.join(self.origin,self.img[0]))
                self.resize_image(outfile)
                pass
        except:
            log.error('生成封面缩略图失败')
            pass

    def run(self):
        self.createImgList()
        if self.no_index:
            self.createContentHtml()
        if self.no_preview:
            self.createPreviewImg()