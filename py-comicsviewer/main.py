# -*- coding: utf-8 -*-

import os
import re
import socket
import urllib.parse
import math
import json
from flask import Flask, render_template, request, url_for, jsonify, abort, Blueprint,send_file
from datetime import timedelta
from fun.log import get_logger
# from fun.mysqlite import mysql
from scan_img import scanimg
from preview import imageResize
from multiprocessing import Process, Pool, RLock, freeze_support
from flask_autoindex import AutoIndex


ORDER_FIELD = "title"

BASE_PATH = os.getcwd()

# DATA_PATH = os.path.join(BASE_PATH, 'data', 'xiang')

IMG_SUFFIX = [".jpg", ".png", ".jpeg", ".gif"]
# DB_CONF = {
#     'dbtype': 'sqllite',
#     'db': DATA_PATH,
#     'prefix': '',
#     'charset': 'utf8'
# }
BOOKDIR = os.path.join(BASE_PATH, 'contents')

log = get_logger(__name__, 'CRITICAL')


def mkdir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)


# def db_data():
#     DB = mysql(DB_CONF)
#     log.critical('读取数据库...')
#     datalist = DB.table('files').order(ORDER_FIELD).getarr()
#     DB.close()
#     log.error(datalist)

#     return datalist


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


# def createImgList(content_path):
#     imgs = []
#     for _dir in os.listdir(content_path):
#         if(os.path.splitext(_dir)[0].startswith('.')):
#             continue
#         if os.path.splitext(_dir)[1].lower() in IMG_SUFFIX:
#             imgs.append(_dir)
#     try:
#         # {True: imgs.sort(key=lambda x: int(x[:-4])), False: imgs.sort()}[imgs[3][:-4].isdigit()]
#         # imgs.sort(key=lambda x: x[:-4])
#         # imgs = sort_filename.sort_insert_filename(imgs)
#         imgs.sort(key=re_sort.sort_key)
#         pass
#     except:
#         imgs.sort()
#         pass
#     return imgs


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


# mkdir(os.path.join(BASE_PATH, 'data'))
mkdir(BOOKDIR)
SCAN = scanimg(BASE_PATH)

contents = Blueprint('contents', __name__,
                     static_folder=BOOKDIR)

app = Flask(__name__, template_folder=os.path.join(BASE_PATH, 'h'),
            static_folder=BASE_PATH, static_url_path='')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=0)

app.register_blueprint(contents)

file = Flask(__name__)
AutoIndex(file,browse_root=BASE_PATH)

# @app.route('/', methods=['GET'])
# def home():
#     _order = request.values.get('order') if 'order' in request.values else 'asc'
#     if _order == 'asc':
#         order = 'created_at asc'
#     elif _order == 'desc':
#         order = 'created_at desc'
#     else:
#         order = 'title asc'
#     title = request.values.get('title') if 'title' in request.values else ''
#     limit = int(request.values.get(
#         'limit')) if request.values.get('limit') else 20
#     where = {}
#     if title:
#         where['title'] = ['like', f'%{title}%']
#     log.critical('读取数据库...'+str(request.values))

#     DB = mysql(DB_CONF)

#     sql = DB.table('files').field('*')
#     if where:
#         sql = sql.where(where)
#     res = sql.order(order).limit(0, limit).order(order).getarr()
#     DB.close()
#     DB = mysql(DB_CONF)
#     _count = DB.table('files')
#     if where:
#         _count = _count.where(where)
#     DB.close()
#     _res = []
#     for data in res:
#         data['url'] = url_for('detail', path=urllib.parse.quote(data['path']))
#         data['pic'] = data['path']+"/"+data['pic']
#         _res.append(data)
#     return render_template("indexAll.html", res = _res, title = title, order = _order, limit = limit)

# @app.route('/detail', methods=['GET'])
# def detail():
#     path = urllib.parse.unquote(request.values.get('path'))
#     log.critical('查看详情页...'+str(request.values))
#     dir_path = os.path.join(BASE_PATH, path)
#     if not os.path.isdir(dir_path):
#         abort(404)
#     img_list = createImgList(dir_path)
#     _img_list = []
#     for data in img_list:
#         _img_list.append(path+'/'+data)
#     log.error(_img_list)
#     return render_template('detail.html', img_list=_img_list, title=path.replace('contents/', ''))


# @app.route('/delete', methods=['POST'])
# def delete():
#     db_id = request.values.get('id')
#     DB = mysql(DB_CONF)
#     db = DB.table('files').where('id='+db_id).getarr()
#     DB.close()
#     return jsonify({"msg": f"准备删除:{str(db[0]['path'])}"})


# @app.route('/confirm_del', methods=['POST'])
# def confirm_del():
#     db_id = request.values.get('id')
#     DB = mysql(DB_CONF)
#     db = DB.table('files').where('id='+db_id).getarr()
#     delete_file_folder(db[0]['path'])
#     DB.table('files').where('id='+db_id).delete()
#     DB.close()
#     log.critical('删除数据库...'+str(request.values))
#     return jsonify({"msg": "删除成功"})


@app.route('/list_del', methods=['POST'])
def list_del():
    db_id = request.values.get('id')
    delete_file_folder(os.path.join(BOOKDIR, db_id))
    log.critical('删除...'+str(db_id))
    return jsonify({"msg": "删除成功"})


@app.route('/', methods=['get'])
@app.route('/list/', methods=['get'])
@app.route('/list/<path:path>', methods=['get'])
def dirlist(path=''):
    path = re.sub(r'\/*$', '', path)
    abspath = os.path.join(BOOKDIR, path)
    _title = request.values.get('title')
    _order = request.values.get('order',default='title')
    _limit = request.values.get('limit', type=int, default=20)
    _page = request.values.get('page', type=int, default=1)
    if os.path.isdir(abspath):
        _dir = []
        _index = []
        _img = []
        if _title:
            for folder_path, subfolders, filenames in os.walk(abspath):
                _path = folder_path.replace(BOOKDIR+os.sep,'')
                folder_path = checkFolder(folder_path)
                if _title in os.path.basename(folder_path):
                    _fi = {
                        'url':os.path.join('list',_path).replace(os.sep,'/'),
                        'path':path,
                        'preview':'h/img/404.png',
                        'title': os.path.basename(folder_path),
                        'modified': int(os.path.getmtime(folder_path)),
                        'size': 0,
                        'is_dir': True,
                        'count':0
                    }
                    for img in os.listdir(folder_path):
                        fname, fex = os.path.splitext(img)
                        if 'preview' in fname:
                            _fi['preview'] = os.path.join(_fi['url'],img)
                        if fex.lower() in IMG_SUFFIX:
                            _fi['count'] +=1
                    _dir.append(_fi)
        else:    
            for fi in os.listdir(abspath):
                fname, fex = os.path.splitext(fi)
                realpath = os.path.join(abspath,fi)
                realpath = checkFolder(realpath)
                _fi = {
                    'url':os.path.join('list',path,fi).replace(os.sep,'/'),
                    'path':os.path.join(path,fi),
                    'preview':os.path.join('list',path,fi).replace(os.sep,'/'),
                    'title': fi,
                    'modified': int(os.path.getmtime(realpath)),
                    'size': 0,
                    'is_dir': False,
                    'count':0
                }
                if fi == '_index.html':
                    _fi['preview'] = 'h/img/dat.png'
                    _index.append(_fi)
                elif os.path.isdir(realpath):
                    imageResize(realpath).run()
                    _fi['preview'] = 'h/img/404.png'
                    for img in os.listdir(realpath):
                        fname, fex = os.path.splitext(img)
                        if 'preview' in fname:
                            _fi['preview'] = os.path.join(_fi['url'],img).replace(os.sep,'/')
                        elif fex.lower() in IMG_SUFFIX:
                            _fi['count'] +=1
                    _fi['is_dir'] = True
                    _dir.append(_fi)
                elif not fex.lower() in IMG_SUFFIX:
                    continue
                elif 'preview' in fname:
                    continue
                else:
                    _fi['size'] = os.path.getsize(realpath)
                    _img.append(_fi)
            

        if _order == 'asc':
            _dir = sorted(_dir, key=lambda x: x['modified'])
            _img = sorted(_img, key=lambda x: x['modified'])
        elif _order == 'desc':
            _dir = sorted(_dir, key=lambda x: x['modified'],reverse=True)
            _img = sorted(_img, key=lambda x: x['modified'],reverse=True)
        else:
            _dir = sorted(_dir, key=lambda x: x['title'])
            _img = sorted(_img, key=lambda x: x['title'])

        res =_dir+_index+_img
        total = len(res)

        res = res[(_page-1)*_limit:_limit]
       
        _nav = [{
            'text': 'HOME',
            'href':'/'
        }]
        _t_nav = ['list']
        for nav in path.split("/"):
            _t_nav.append(nav)
            _nav.append({
                'text': f"/{nav}",
                'href':f"/{'/'.join(_t_nav)}"
            })

        return render_template("index.html",res=json.dumps(res),title=_title,nav=_nav,total=total,limit=_limit,page=_page,order=_order)

    elif os.path.isfile(abspath):
        return send_file(abspath)
    else:
        return abort(404)

@app.route('/scan', methods=['GET'])
def scan():
    log.critical('更新目录')
    res = ''
    try:
        res = SCAN.run()
        return jsonify({"msg": str(res)})
    except Exception as e:
        return jsonify({"msg": str(e)})

def checkFolder(src):
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

def startServer1(port):
    app.run(host="0.0.0.0", port=port, threaded=True )
def startServer2(port):
    file.run(host="0.0.0.0", port=port, threaded=True)
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
    port  = int(os.getenv('web_port',18181))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result1 = sock.connect_ex(('127.0.0.1', port))
    result2 = sock.connect_ex(('127.0.0.1', port+1))

    if result1 == 0:
        print('漫画端口被占用')
    elif result2 == 0:
        print('文件端口被占用')
    else:
        try:
            log.critical(f'web启动成功 http://0.0.0.0:{port}')
            server1 = Process(target=startServer1, args=(port,))
            server1.deamon = True
            server1.start()
            server2 = Process(target=startServer2, args=(port+1,))
            server2.deamon = True
            server2.start()
            server1.join()
            server2.join()
        except KeyboardInterrupt:
            log.critical('web停止')
            pass
