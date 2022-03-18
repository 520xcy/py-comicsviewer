# -*- coding: utf-8 -*-
# python 3.7.0

from crypt import methods
import os
import socket
import urllib.parse
import math
import time
from waitress import serve
from flask import Flask, render_template, request, url_for, jsonify, abort, Blueprint
from datetime import timedelta
from fun.log import get_logger
from fun.mysqlite import mysql
from fun import re_sort
from fun.scan_img import scanimg
# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer
from multiprocessing import Process, Pool, RLock, freeze_support

ORDER_FIELD = "title"

BASE_PATH = os.getcwd()

DATA_PATH = os.path.join(BASE_PATH, 'data', 'xiang')
CONTENT_HTML = f"{os.sep}detail.html"

IMG_SUFFIX = [".jpg", ".png", ".jpeg", ".gif"]
DB_CONF = {
    'dbtype': 'sqllite',
    'db': DATA_PATH,
    'prefix': '',
    'charset': 'utf8'
}
SCAN = scanimg(BASE_PATH)

log = get_logger(__name__, 'CRITICAL')


def mkdir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)


def db_data():
    DB = mysql(DB_CONF)
    log.critical('读取数据库...')
    datalist = DB.table('files').order(ORDER_FIELD).getarr()
    DB.close()
    log.error(datalist)

    return datalist


def delete_file_folder(src):
    '''delete files and folders'''
    if os.path.isfile(src):
        try:
            os.remove(src)
        except:
            pass
    elif os.path.isdir(src):
        for item in os.listdir(src):
            itemsrc = os.path.join(src, item)
            delete_file_folder(itemsrc)
        try:
            os.rmdir(src)
        except:
            pass


def createImgList(content_path):
    imgs = []
    for _dir in os.listdir(content_path):
        if(os.path.splitext(_dir)[0].startswith('.')):
            continue
        if os.path.splitext(_dir)[1].lower() in IMG_SUFFIX:
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


# class FileMonitorHandler(FileSystemEventHandler):
#     def __init__(self, **kwargs):
#         super(FileMonitorHandler, self).__init__(**kwargs)
#         # 监控目录 目录下面以device_id为目录存放各自的图片
#     # 重写文件改变函数，文件改变都会触发文件夹变化
#     def on_modified(self, event):
#         if not event.is_directory:  # 文件改变都会触发文件夹变化
#             file_path = event.src_path
#             log.error("文件改变: %s " % file_path)

#     def on_created(self, event):
#         log.error('创建了', event.src_path)
#         res = ''
#         try:
#             res = SCAN.run()
#             log.error(str(res))
#         except Exception as e:
#             return log.critical(str(res))

#     def on_moved(self, event):
#         log.error("移动了文件", event.src_path)

#     def on_deleted(self, event):
#         log.error("删除了文件", event.src_path)

#     def on_any_event(self, event):
#         return


contents = Blueprint('contents', __name__,
                     static_folder=os.path.join(BASE_PATH, 'contents'))

app = Flask(__name__, template_folder=os.path.join(BASE_PATH, 'h'),
            static_folder=os.path.join(BASE_PATH, 'h'), static_url_path='')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=0)

app.register_blueprint(contents)


@app.route('/', methods=['GET'])
def home():
    return render_template("index.html")


@app.route('/pagelist', methods=['GET'])
def pagelist():
    page = int(request.values.get(
        'page')) if request.values.get('page') else 1
    limit = int(request.values.get(
        'limit')) if request.values.get('limit') else 20
    offset = (page - 1) * limit
    order = 'title'
    if 'order' in request.values:
        _order = request.values.get('order')
        if _order == 'asc':
            order = 'created_at asc'
        elif _order == 'desc':
            order = 'created_at desc'

    title = request.values.get('title') if 'title' in request.values else None
    where = {}
    if title:
        where['title'] = ['like', f'%{title}%']
    log.critical('读取数据库...'+str(request.values))

    DB = mysql(DB_CONF)

    sql = DB.table('files').field('*')
    if where:
        sql = sql.where(where)
    res = sql.limit(offset, limit).order(order).getarr()
    DB.close()
    DB = mysql(DB_CONF)
    _count = DB.table('files')
    if where:
        _count = _count.where(where)
    count = _count.count()
    DB.close()
    _res = []
    for data in res:
        data['url'] = url_for('detail', path=urllib.parse.quote(data['path']))
        data['pic'] = data['path']+"/"+data['pic']
        _res.append(data)
    last_page = math.ceil(count/limit)
    return jsonify({'data': _res, 'count': count, 'last_page': last_page, 'code': 0})


@app.route('/detail', methods=['GET'])
def detail():
    path = urllib.parse.unquote(request.values.get('path'))
    log.critical('查看详情页...'+str(request.values))
    dir_path = os.path.join(BASE_PATH, path)
    if not os.path.isdir(dir_path):
        abort(404)
    img_list = createImgList(dir_path)
    _img_list = []
    for data in img_list:
        _img_list.append(path+'/'+data)
    log.error(_img_list)
    return render_template('detail.html', img_list=_img_list, title=path.replace('contents/', ''))


@app.route('/delete', methods=['POST'])
def delete():
    db_id = request.values.get('id')
    DB = mysql(DB_CONF)
    db = DB.table('files').find(db_id)
    DB.close()
    return jsonify({"msg": f"准备删除:{str(db['path'])}"})


@app.route('/confirm_del', methods=['POST'])
def confirm_del():
    db_id = request.values.get('id')
    DB = mysql(DB_CONF)
    db = DB.table('files').find(db_id)
    delete_file_folder(db['path'])
    DB.table('files').where('id='+db_id).delete()
    DB.close()
    log.critical('删除数据库...'+str(request.values))
    return jsonify({"msg": "删除成功"})


@app.route('/scan', methods=['GET'])
def scan():
    log.critical('更新目录')
    res = ''
    try:
        res = SCAN.run()
        return jsonify({"msg": str(res)})
    except Exception as e:
        return jsonify({"msg": str(e)})


def webrun():
    log.critical('web启动成功')
    serve(app, host='0.0.0.0', port=8181)
    log.critical('web停止')

# def watchdog():
#     event_handler = FileMonitorHandler()
#     observer = Observer()
#     observer.schedule(event_handler, path=os.path.join(
#         BASE_PATH, 'contents'), recursive=True)  # recursive递归的
#     observer.start()
#     log.critical('文件夹监控启动')
#     observer.join()
#     log.critical('文件夹监控停止')


if __name__ == '__main__':
    freeze_support()
    # webbrowser.open("http://127.0.0.1:8181")
    mkdir(os.path.join(BASE_PATH, 'data'))
    mkdir(os.path.join(BASE_PATH, 'contents'))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8181))
    if result == 0:
        log.error('socket端口被占用')
    else:
        try:
            pool = Pool(processes=2)

            result = []

            result.append(pool.apply_async(webrun))
            # result.append(pool.apply_async(watchdog))

            pool.close()

            pool.join()

            for res in result:
                log.critical(res.get())
            log.critical("Sub-process(es) done.")
        except KeyboardInterrupt:
            pass
