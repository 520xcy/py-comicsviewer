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


class scanimg(object):
    def __init__(self, BASH_PATH):
        self.RUNNING = False
        self.BASE_TEMP_DEEPTH = 1
        self.BASE_PATH = BASH_PATH
        self.CONTENTS_PATH = 'contents'
        self.res = []
        self.CONTENT_HTML = f"{os.sep}detail.html"

        self.DATA_PATH = os.path.join(os.getcwd(), 'data', 'xiang')

        self.TEMPLETE_HTML = os.path.join(os.getcwd(), 'h', 'detail_templete.html')

        self.IMG_SUFFIX = [".jpg", ".png", ".jpeg", ".gif"]
        self.DBCONF = {
            'dbtype': 'sqllite',
            'db': self.DATA_PATH,
            'prefix': '',
            'charset': 'utf8'
        }
        DB = sqlite.mysql(self.DBCONF)
        DB.query(
            'CREATE TABLE IF NOT EXISTS files(id INTEGER primary key AUTOINCREMENT,title text, path text,pic text, count int, created_at text)')
        DB.query(
            'CREATE INDEX "index" on files(title ASC, created_at ASC)')
        self.contentPaths = []
        self.hasDetail = []
        self.allPaths = []

    '''把时间戳转化为时间: 1479264792 to 2016-11-16 10:53:12'''

    def TimeStampToTime(self, timestamp):
        timeStruct = time.localtime(timestamp)
        return time.strftime('%Y-%m-%d %H:%M:%S', timeStruct)

    '''文件处理'''

    def checkFileExist(self, fileURI):
        if os.path.isfile(fileURI):
            return True
        return False

    def checkFolder(self, src):
        if not '#' in src:
            return src
        dst = str.replace(src, '#', '_')
        try:
            os.rename(src, dst)
            return dst
            pass
        except:
            return src
            pass

    '''
    :文件处理部分
    '''

    def createComicItems(self, title, content_path, first_img, count, id, created_at):
        templete = r'<li><a href="{url}" target="_blank" title="{title}"><h2>{title}</h2><div class="image"><img class="lazy" src="h/img/loading.gif" data-original="{first_img}"><table class="data"><tr><th scope="row">枚数</th><td>{count}枚</td></tr><tr><td class="tag" colspan="2"><span>{title}</span></td></tr></table></div></a><p class="date">{date}&nbsp;<a class="del" href="javascript:;" data-id="{id}">删</a></p></li><!--{comic_contents}-->'
        templete = templete.replace(
            r"{url}", urllib.parse.quote(content_path) + self.CONTENT_HTML)
        templete = templete.replace(r"{title}", str(title))
        templete = templete.replace(r"{count}", str(count))
        templete = templete.replace(r"{id}", str(id))
        templete = templete.replace(
            r"{first_img}", urllib.parse.quote(content_path)+"/"+first_img)
        # date = time.localtime(os.stat(content_path).st_ctime)
        # templete = templete.replace(
        #     r"{date}", ("%d-%d-%d" % (date.tm_year, date.tm_mon, date.tm_mday)))
        templete = templete.replace(r"{date}", str(created_at))
        return templete

    def checkData(self):
        log.error('开始检查数据库中无效目录...')
        datas = self.getData()
        truedatas = copy.deepcopy(datas)
        DB = sqlite.mysql(self.DBCONF)
        for data in datas:
            if data['path'] not in self.allPaths:
                self.res.append({"移除： ": data['path']})
                print("移除： ", data['path'])
                DB.table('files').where('id='+str(data['id'])).delete()
                truedatas.remove(data)
        DB.close()
        return truedatas

    def getData(self):
        log.error('读取数据库...')
        DB = sqlite.mysql(self.DBCONF)
        datalist = DB.table('files').getarr()
        DB.close()
        return datalist
    '''
    :图片处理部分
    '''

    def get_size(self, file):
        # 获取文件大小:KB
        size = os.path.getsize(file)
        return size / 1024

    def get_outfile(self, infile, outfile=''):
        if outfile:
            return outfile
        dir, suffix = os.path.splitext(infile)
        outfile = '{}-out{}'.format(dir, suffix)
        return outfile

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
        outfile = self.get_outfile(infile, outfile)
        while o_size > mb:
            im = Image.open(infile)
            im.save(outfile, quality=quality)
            if quality - step < 0:
                break
            quality -= step
            o_size = self.get_size(outfile)
        return outfile, self.get_size(outfile)

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
        out = im.resize((x_s, y_s), Image.ANTIALIAS)
        outfile = self.get_outfile(infile, outfile)
        out.save(outfile)

    def gci(self, filepath):

        # 遍历filepath下所有文件，包括子目录
        files = os.listdir(filepath)
        for fi in files:
            fi_d = os.path.join(filepath, fi)
            if os.path.isdir(fi_d):
                fi_d = self.checkFolder(fi_d)
                self.contentPaths.append(fi_d)
                self.gci(fi_d)
            if '/'+fi == self.CONTENT_HTML:
                self.hasDetail.append(filepath)

    def pushData(self, data):
        ctime = os.path.getctime(data[1]+'/'+data[2])
        try:
            dir, suffix = os.path.splitext(data[2])
            if not dir[-4:] == '-out':
                log.error('生成封面缩略图...')
                self.compress_image(data[1]+'/'+data[2])
                self.resize_image(data[1]+'/'+data[2])
                data[2] = self.get_outfile(data[2])
                pass
        except:
            log.critical('生成封面缩略图失败')
            pass

        obj = {
            'title': data[0],
            'path': data[1],
            'pic': data[2],
            'count': data[3],
            # 'created_at':time.strftime("%Y-%m-%d", time.localtime())
            'created_at': self.TimeStampToTime(ctime)
        }
        DB = sqlite.mysql(self.DBCONF)
        count = DB.table('files').where({'path': data[1]}).count()
        if count:
            DB.table('files').where({'path': data[1]}).save(obj)
            return
        DB.table('files').add(obj)
        DB.close()

    def output2Html(self, htmlContent, file):
        output = open(file, "w", encoding="UTF-8")
        output.write(htmlContent)
        output.flush()
        output.close()

    def getTempleteHtml(self, templeteURL):
        templete = open(self.BASE_PATH + templeteURL, "r", encoding="UTF-8")
        htmlStr = templete.read()
        templete.close()
        return htmlStr

    def createOptions(self, imgData):
        options = ""
        _i = 0
        for _img in imgData:
            options += ('<option value="%d" file="%s">第%d页</option>' %
                        (_i, _img, _i+1))
            _i += 1
        return options

    def createImgList(self, content_path):
        imgs = []
        for _dir in os.listdir(content_path):
            if(os.path.splitext(_dir)[0].startswith('.')):
                continue
            if os.path.splitext(_dir)[1].lower() in self.IMG_SUFFIX:
                imgs.append(_dir)
        try:
            # {True: imgs.sort(key=lambda x: int(x[:-4])), False: imgs.sort()}[imgs[3][:-4].isdigit()]
            # imgs.sort(key=lambda x: x[:-4])
            # imgs = sort_filename.sort_insert_filename(imgs)
            imgs.sort(key=re_sort.sort_key)
            pass
        except:
            imgs.sort()
            pass
        return imgs

    def createContentHtml(self, contentPath):
        imgData = self.createImgList(contentPath)
        if len(imgData) == 0 or imgData == None:
            return
        count = len(imgData)
        options = self.createOptions(imgData)
        htmlStr = self.getTempleteHtml(self.TEMPLETE_HTML)
        title = contentPath.replace(self.CONTENTS_PATH+"/", "")
        deepth = "../"
        d_i = 0
        while d_i < self.BASE_TEMP_DEEPTH:
            deepth += "../"
            d_i += 1
        htmlStr = htmlStr.replace(r"{deepth}", deepth)
        htmlStr = htmlStr.replace(r"{imgData}", "var imgData="+str(imgData))
        htmlStr = htmlStr.replace(
            r"{title}", title).replace(r"{options}", options)
        htmlStr = htmlStr.replace(r"{count}", str(
            count)).replace(r"{first_img}", imgData[0])
        try:
            htmlStr = htmlStr.replace(r"{next_img}", imgData[1])
            pass
        except IndexError:
            htmlStr = htmlStr.replace(r"{next_img}", imgData[0])
            pass
        log.error('生成详情页...')
        self.output2Html(htmlStr, contentPath + self.CONTENT_HTML)
        return [title, contentPath, imgData[0], count]

    def run(self):
        self.contentPaths = []
        self.hasDetail = []
        self.allPaths = []
        self.res = []
        if not self.RUNNING:
            try:
                self.RUNNING = True
                time.sleep(5)
                log.error('开始遍历文件夹...')
                self.gci(self.CONTENTS_PATH)
                self.allPaths = copy.deepcopy(self.contentPaths)
                log.error('开始排除含已生成目录...')
                for path in self.hasDetail:
                    self.contentPaths.remove(path)
                log.error('开始生成目录...')
                for contentPath in self.contentPaths:
                    self.BASE_TEMP_DEEPTH = contentPath.count('/', 0)
                    data = self.createContentHtml(contentPath)
                    if data is not None:
                        self.res.append({"新增： ": data})
                        log.error("新增： " + ','.join('%s' %
                                  value for value in data))
                        self.pushData(data)
                    else:
                        self.allPaths.remove(contentPath)

                if not self.res:
                    self.res.append('无变化')
                log.critical('扫描完成')
            except:
                raise
            finally:
                self.RUNNING = False
        else:
            self.res.append('扫描正在进行时无法开始新的扫描')
        return self.res
