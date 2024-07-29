# -*- coding: utf-8 -*-
import tkinter as tk, os
import stat, os, sys, tkinter as tk
import ctypes
import time
import sys
import base64
import subprocess

from tkinter import ttk
from tkinter.ttk import *
from tkinter import *

#获取版本号信息
PyCodeVersion = '2024.7' + ' Stuido' + ' Beta'
__PyCodeVersion__ = base64.b64encode(PyCodeVersion.encode('utf-8'))
__PyCodeVersion__ = str(__PyCodeVersion__,'utf-8')

#配置窗口缩放
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 使用程序自身Dpi
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) # 获取变量 ‘ScaleFactor’

#树目录配置
icon_path = os.path.join(os.path.dirname(__file__), "Icons")  # 图标文件夹 os.path.join(os.path.dirname(__file__), "Icons")
module_path = __file__  # 默认函数浏览文件路径
bg_color = '#ffffff'  # 常规项背景颜色
st_color = '#d9d9d9'  # 选中项背景颜色


class ScrolledCanvas:
    "带有滚动条和快捷键绑定的画布小部件"

    def __init__(s, master, frame, **opts):
        if 'yscrollincrement' not in opts:
            opts['yscrollincrement'] = 17
        s.master = master
        s.frame = frame
        s.frame.rowconfigure(0, weight=1)  # 行自动适应窗口大小
        s.frame.columnconfigure(0, weight=1)  # 列自动适应窗口大小
        s.canvas = tk.Canvas(s.frame, **opts)  # Canvas绘图窗口
        s.canvas.grid(row=0, column=0, sticky="nsew")

        # 右侧滚动条
        s.vbar = tk.Scrollbar(s.frame, name="vbar")
        s.vbar.grid(row=0, column=1, sticky="nse")
        s.canvas['yscrollcommand'] = s.vbar.set
        s.vbar['command'] = s.canvas.yview

        # 下方滚动条"horizontal" 水平显示
        s.hbar = tk.Scrollbar(s.frame, name="hbar", orient="horizontal")
        s.hbar.grid(row=1, column=0, sticky="ews")
        s.canvas['xscrollcommand'] = s.hbar.set
        s.hbar['command'] = s.canvas.xview

        s.canvas.bind("<MouseWheel>", lambda event: s.unit_up(event) if event.delta > 0 else s.unit_down(event))
        s.canvas.bind("<Key-Prior>", s.page_up)  # PageUp键
        s.canvas.bind("<Key-Next>", s.page_down)  # PageDown键
        s.canvas.bind("<Key-Up>", s.unit_up)  # 上键
        s.canvas.bind("<Key-Down>", s.unit_down)  # 下键
        s.canvas.bind("<Alt-Key-2>", s.zoom_height)  # Alt+2
        s.canvas.focus_set()

    def page_up(s, event):
        # s.vbar.get()[0]为'0.0'时禁止向上
        if s.vbar.get()[0]: s.canvas.yview_scroll(-1, "page")
        return "break"

    def page_down(s, event):
        s.canvas.yview_scroll(1, "page")
        return "break"

    def unit_up(s, event):
        # s.vbar.get()[0]为'0.0'时禁止向上
        if s.vbar.get()[0]: s.canvas.yview_scroll(-1, "unit")
        return "break"

    def unit_down(s, event):
        s.canvas.yview_scroll(1, "unit")
        return "break"

    def zoom_height(s, event):  # 窗口上下满屏
        import re
        geom = s.master.wm_geometry()
        m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", geom)
        if not m:
            s.master.bell()
            return
        width, height, x, y = map(int, m.groups())
        newheight = s.master.winfo_screenheight()
        if sys.platform == 'win32':
            newy = 0
            newheight = newheight - 72
        else:
            newy = 0
            newheight = newheight - 88
        if height >= newheight:
            newgeom = ""
        else:
            newgeom = "%dx%d+%d+%d" % (width, newheight, x, newy)
        s.master.wm_geometry(newgeom)
        return "break"


class TreeNode:
    # 初始化方法,传入画布、父节点和项对象
    def __init__(s, canvas, parent, item):
        s.canvas = canvas
        s.parent = parent  # 接收父节点TreeNode对象,只在TreeNode内部传递,外部传入None
        s.item = item  # TreeItem子类对象
        s.state = 'collapsed'  # 选中标记为未选中
        s.selected = False  # 判断是否选中
        s.children = []  # 存储子节点TreeNode对象
        s.x = s.y = None
        s.iconimages = {}  # 图标的PhotoImage实例缓存

    def destroy(s):
        "退出"
        for c in s.children[:]:
            s.children.remove(c)  # 删除所有子节点
            c.destroy()
        s.parent = None  # 将父节点设置为None

    def geticonimage(s, name):
        "根据名称获取图标文件,生成tkImage对象返回"
        try:
            return s.iconimages[name]  # 如果存在同名图标,返回已经生成的tkImage对象
        except KeyError:
            pass
        file, ext = os.path.splitext(name)  # 获取文件名和后缀
        ext = ext or ".gif"  # 没有后缀的以".gif"为后缀
        fullname = os.path.join(icon_path, file + ext)  # 连接文件路径
        image = tk.PhotoImage(master=s.canvas, file=fullname)  # 生成tkImage对象
        s.iconimages[name] = image  # 将tkImage对象缓存在s.iconimages
        return image

    def select(s, event=None):
        "选中节点的方法,单击图标也可调动"
        if s.selected:
            return
        s.deselectall()  # 全不选
        s.selected = True  # 指示是否有选中项
        s.canvas.delete(s.image_id)  # 删除旧的图标对象
        s.drawicon()  # 绘制新的图标
        s.drawtext()  # 绘入文本内容

    def deselect(s, event=None):
        "取消选择节点的方法"
        if not s.selected:
            return
        s.selected = False
        s.canvas.delete(s.image_id)  # 删除图标对象
        s.drawicon()
        s.drawtext()

    def deselectall(s):
        "全不选所有节点的方法,并调用 s.parent.deselectall 方法递归操作父节点"
        if s.parent:
            s.parent.deselectall()  # 操作父节点递归操作全不选
        else:
            s.deselecttree()

    def deselecttree(s):
        "全不选所有节点的方法, 并调用 s.children-deselecttree() 方法递归操作子节点"
        if s.selected:
            s.deselect()
        for child in s.children:
            child.deselecttree()  # 操作子节点递归操作全不选

    def flip(s, event=None):
        "双击节点"
        try:
            if s.state == 'expanded':  # 选中节点为展开状态
                s.collapse()  # 收起节点
            else:
                s.expand()  # 张开节点
            s.item.OnDoubleClick()  # 执行s.item的双击函数
            return "break"
        except:
            pass

    def expand(s, event=None):
        "判断当前节点是否可展开"
        if not s.item._IsExpandable():  # 判断有无子项
            return
        if s.state != 'expanded':  # 选中节点未展开
            s.state = 'expanded'  # 选中节点设置为展开
            s.update()
            s.view()  # 更新视野

    def collapse(s, event=None):
        "收起选中的节点"
        if s.state != 'collapsed':  # 选中节点未关闭
            s.state = 'collapsed'  # 选中节点设置为关闭
            s.update()

    def view(s):
        "更新视野内容"
        top = s.y - 2
        bottom = s.lastvisiblechild().y + 17
        height = bottom - top
        visible_top = s.canvas.canvasy(0)  # 获取可见区域的顶部纵坐标
        visible_height = s.canvas.winfo_height()  # 获取画布的可见高度
        visible_bottom = s.canvas.canvasy(visible_height)  # 获取画布可见区域底部的y坐标
        if visible_top <= top and bottom <= visible_bottom:  # 如果画布的顶部在可见区域内,则直接返回
            return
        x0, y0, x1, y1 = s.canvas._getints(s.canvas['scrollregion'])  # 获取滚动区域的坐标信息
        if top >= visible_top and height <= visible_height:  # 如果当前可见区域在画布顶部和底部之间, 则计算滚动比例
            fraction = top + height - visible_height
        else:  # 否则,只滚动到可见区域的顶部
            fraction = top
        fraction = float(fraction) / y1  # 将滚动比例转换为浮点数,并除以y1得到最终的滚动比例
        s.canvas.yview_moveto(fraction)  # 将画布滚动到指定的比例位置

    def lastvisiblechild(s):
        "返回节点的最后一个可见子节点。"
        if s.children and s.state == 'expanded':  # 如果当前节点有子节点且当前节点状态为展开
            return s.children[-1].lastvisiblechild()  # 返回最后一个可见且未展开子节点的对象
        else:
            return s  # 返回当前节点对象

    def update(s):
        "刷新画布"
        if s.parent:  # 存在父节点
            s.parent.update()  # 刷新父节点
        else:
            oldcursor = s.canvas['cursor']  # 保存当前光标样式
            s.canvas['cursor'] = "watch"  # 转圈光标
            s.canvas.update()  # 更新画布
            s.canvas.delete(tk.ALL)  # 删除画布上的所有对象
            s.draw(7, 5)  # 在画布上绘制新的图形,左顶点坐标(7, 5)
            x0, y0, x1, y1 = s.canvas.bbox(tk.ALL)  # 获取包含内容的画布边界框的位置和大小
            s.canvas.configure(scrollregion=(0, 0, x1, y1))  # 设置画布的滚动区域
            s.canvas['cursor'] = oldcursor  # 恢复光标样式

    def draw(s, x, y):
        # XXX 这个硬编码的几何常数太多了！
        dy = 20  # 设置默认的间距
        s.x, s.y = x, y  # 更新对象的位置
        s.drawicon()  # 绘制图标
        s.drawtext()  # 绘制文本
        if s.state != 'expanded':  # 如果状态不是展开,则返回当前y值加上间距
            return y + dy

        # 画子节点
        if not s.children:  # 如果子节点对象列表为空
            sublist = s.item._GetSubList()  # 获取组成子元素的项目列表
            if not sublist:
                # _IsExpandable() 方法错误地允许了这种情况
                return y + 17
            for item in sublist:
                # s代表当前实例对象,通过s.XXXX()可以访问当前实例对象的方法或属性
                # s.__class__代表当前实例对象所属的类, s.__class__.XXXX()可以访问类的方法或属性。 这种方式可以用于在实例方法中调用类方法, 或者在实例方法中访问类的属性
                child = s.__class__(s.canvas, s, item)  # 为每个子元素创建一个新的对象
                s.children.append(child)

        # 计算子节点的起始位置和上一个子节点的结束位置
        cx = x + 20
        cy = y + dy
        cylast = 0

        # 遍历子节点对象,绘制连接线并递归调用draw方法
        for child in s.children:
            cylast = cy
            s.canvas.create_line(x + 9, cy + 7, cx, cy + 7,
                                 fill="gray50")  # 树状图的横线,"gray50" 灰色值50,"gray100"则为白色,值越小颜色越深
            cy = child.draw(cx, cy)
            if child.item._IsExpandable():  # 判断是否有子项
                if child.state == 'expanded':
                    iconname = "minusnode"  # 展开后显示的减号图标
                    callback = child.collapse
                else:
                    iconname = "plusnode"  # 收起后显示的加号图标
                    callback = child.expand
                image = s.geticonimage(iconname)  # 获取图标tkImage对象
                id = s.canvas.create_image(x + 9, cylast + 7, image=image)  # 绘制图标
                # 在画布上绑定单击和双击事件,直到画布被删除：
                s.canvas.tag_bind(id, "<1>", callback)
                s.canvas.tag_bind(id, "<Double-1>", lambda x: None)

        id = s.canvas.create_line(x + 9, y + 10, x + 9, cylast + 7, fill="gray50")  # 绘制竖向连接线并调整其位置
        s.canvas.tag_lower(id)  # 将连接线置于其他元素之下
        return cy  # 返回最后一个子节点的结束位置作为最终结果

    def drawicon(s):
        "绘制图标"
        if s.selected:  # 如果选中
            imagename = (s.item.GetSelectedIconName() or  # 选中时图标
                         s.item.GetIconName() or  # 设定好的图标
                         "openfolder")
        else:
            imagename = s.item.GetIconName() or "folder"  # 设定好的图标
        image = s.geticonimage(imagename)  # 获取图标的tk对象
        id = s.canvas.create_image(s.x, s.y, anchor="nw", image=image)  # 将图标绘入画布
        s.image_id = id  # 将图像ID存储在对象的属性中
        s.canvas.tag_bind(id, "<1>", s.select)  # 鼠标左键单击
        s.canvas.tag_bind(id, "<Double-1>", s.flip)  # 鼠标左键双击

    def drawtext(s):
        "绘入文字"
        # 计算文本的x和y坐标
        textx = s.x + 20 - 1
        texty = s.y - 4

        text = s.item.GetText()  # 获取显示在标签前的文字,可以用来注释
        if text:
            id = s.canvas.create_text(textx,
                                      texty,  # 如果上下有偏移这里+-调整
                                      anchor="nw",
                                      text=text)
            s.canvas.tag_bind(id, "<1>", s.select)
            s.canvas.tag_bind(id, "<Double-1>", s.flip)
            x0, y0, x1, y1 = s.canvas.bbox(id)
            textx = max(x1, 10) + 10  # 标签和文字间的间隙宽度

        labeltext = s.item.GetLabelText() or "<no text>"  # 获取标签文字

        # 如果存在entry属性,调用edit_finish方法
        try:
            s.entry
        except AttributeError:
            pass
        else:
            s.edit_finish()  # 保存编辑后的内容

        # 如果不存在label属性,则创建新的Label
        try:
            s.label
        except AttributeError:
            # label显示文字内容, label主要是为了放置编辑框Entry, 不需要编辑框的可以使用create_text替代, 减少画布上的窗口部件
            s.label = tk.Label(s.canvas, text=labeltext,
                               bg=bg_color,  # 背景颜色,这里设置为和画布一样
                               bd=0, padx=2, pady=2)
        if s.selected:
            s.label['bg'] = st_color  # 更改背景颜色为选中背景颜色
        else:
            s.label['bg'] = bg_color  # 更改背景颜色为默认背景颜色

        # 在画布上创建一个窗口来显示标签,并绑定事件
        id = s.canvas.create_window(textx, texty,
                                    anchor="nw", window=s.label)
        s.label.bind("<1>", s.select_or_edit)
        s.label.bind("<Double-1>", s.flip)
        s.label.bind("<MouseWheel>", lambda e: wheel_event(e, s.canvas))
        s.text_id = id

    def select_or_edit(s, event=None):
        "单击label"
        if s.selected and s.item.IsEditable():  # 为已选中节点且是可编辑节点
            s.edit(event)  # 生成输入框
        else:
            s.select(event)  # 选中节点

    def edit(s, event=None):
        "生成输入框"
        s.entry = tk.Entry(s.label, bd=0, highlightthickness=1, width=0)  # Entry输入框
        s.entry.insert(0, s.label['text'])  # 输入框内插入项目文本
        s.entry.selection_range(0, tk.END)  # 选中所有文本
        s.entry.pack(ipadx=5)
        s.entry.focus_set()  # 设置焦点,focus_get() 获取焦点部件名称
        s.entry.bind("<Return>", s.edit_finish)  # 回车键保存
        s.entry.bind("<Escape>", s.edit_cancel)  # Esc取消,关闭Entry

    def edit_finish(s, event=None):
        "保存编辑后的内容"
        try:
            entry = s.entry
            del s.entry
        except AttributeError:
            return
        text = entry.get()  # 获取编辑框内文本
        entry.destroy()
        if text and text != s.item.GetLabelText():
            s.item.SetLabelText(text)  # 更改节点的文本
        text = s.item.GetLabelText()  # 重新获取节点文本
        s.label['text'] = text
        s.drawtext()  # 重绘选项
        s.canvas.focus_set()  # 设置焦点

    def edit_cancel(s, event=None):
        "取消保存"
        try:
            entry = s.entry
            del s.entry
        except AttributeError:
            return
        entry.destroy()
        s.drawtext()  # 重绘选项
        s.canvas.focus_set()  # 设置焦点


class TreeItem:
    """
    表示树项的父类。
    方法通常应被重写,否则将使用默认操作。
    """

    expandable = None

    def __init__(s):
        """做任何你需要做的事。"""

    def _IsExpandable(s):
        """不要覆盖！由TreeNode调用。"""
        if s.expandable is None:
            s.expandable = s.IsExpandable()
        return s.expandable

    def IsExpandable(s):
        """返回是否有子项。"""
        return 1

    def _GetSubList(s):
        """不要覆盖！由TreeNode调用。"""
        if not s.IsExpandable():
            return []
        sublist = s.GetSubList()
        if not sublist:
            s.expandable = 0
        return sublist

    def GetText(s):
        """返回要显示在标签前的字符串（如果有）。"""

    def GetLabelText(s):
        """返回要显示的标签文本字符串。"""

    def GetSubList(s):
        """返回组成子列表的项目列表。"""

    def IsEditable(s):
        """返回是否可以编辑项目的文本。"""

    def SetLabelText(s, text):
        """更改项目的文本（如果可编辑）。"""

    def GetIconName(s):
        """返回要正常显示的图标的名称。"""

    def GetSelectedIconName(s):
        """返回选定时要显示的图标的名称。"""

    def OnDoubleClick(s):
        """在双击该项时调用。"""


class ModuleBrowserTreeItem(TreeItem):
    """
    模块中子节点的浏览器树。
    使用TreeItem作为树结构的基础。
    """

    def __init__(s, name, tree):
        # name 要显示的名称
        # tree 该函数/类的信息(位置,图标标记,子集字典)
        s.position = tree[0]
        s.isfunction = tree[1]
        s.obj = tree[2]
        s.name = name

    def GetText(s):
        "返回要显示在函数名前的文字。"
        # if s.isfunction in ['def','class']:
        #    return s.isfunction

    def GetLabelText(s):
        "返回要显示的函数/类的名称。"
        return s.name

    def GetIconName(s):
        "返回要显示的图标的名称。"
        if s.isfunction == 'def':
            return "form1"
        elif s.isfunction == 'class':
            return "form2"
        elif s.isfunction in ['.py', '.pyw']:
            return "Function2"
        else:
            return "blank"

    def IsExpandable(s):
        "判断s.obj是否有子集。"
        return len(s.obj)

    def GetSubList(s):
        "返回子级的ModuleBrowserTreeItem。"
        return [ModuleBrowserTreeItem(key, s.obj[key]) for key in s.obj.keys()]

    def OnDoubleClick(s):
        "双击返回类或函数所在的位置。"
        print(s.position)
        return s.position


class FileBrowserTreeItem(TreeItem):
    """
    模块中子节点的浏览器树。
    使用TreeItem作为树结构的基础。
    """

    def __init__(s, tree):
        # tree 文件夹信息,格式：(名称, 属性, 完整路径, [子集...., (名称,属性,完整路径,[子集...]) ])
        # s.root = treebrowser.root # 可以做弹窗提示,比如改名的时候
        s.name = tree[0]
        s.attr = tree[1]
        s.dir = tree[2]
        s.obj = tree[3]

    def GetLabelText(s):
        "返回要显示的名称。"
        return s.name

    def SetLabelText(s, text):
        "更改项目的文本（如果可编辑）。"
        dir = s.dir[:s.dir.rfind(s.name)]  # 上级文件夹
        if os.path.exists(dir):
            try:
                os.renames(dir + s.name, dir + text)
                s.name = text
                s.dir = dir + text
            except:
                pass

    def GetIconName(s):
        "返回要显示的图标的名称。"
        if s.attr == 'dir':
            return 'dir'
        elif s.attr == 'root':
            return 'pc'  # 根"计算机"
        elif s.attr == 'piece':
            return 'piece'  # 盘符
        elif s.attr == 'collect':
            return 'collect'  # 收藏文件夹图标
        elif s.attr in ['.txt']:
            return 'txt'
        elif s.attr in ['.dll', '.bin', '.cab']:
            return "dll"
        elif s.attr in ['.apk']:
            return "apk"
        elif s.attr in ['.reg']:
            return "tree"
        elif s.attr in ['.lnk']:
            return "lnk"
        elif s.attr in ['.chm']:
            return "help"
        elif s.attr in ['.gba', '.nes', '.chd', '.swf']:
            return "game"
        elif s.attr in ['.py', '.pyw']:
            return "py"
        elif s.attr in ['.ini', '.db', '.bat', '.dat', '.sav', '.tag']:
            return "db"
        elif s.attr in ['.zip', '.rar', '.7z', '.gz']:
            return "zip"
        elif s.attr in ['.exe', '.iso', '.msi']:
            return "exe"
        elif s.attr in ['.mp3', '.flac', '.ape', '.wav']:
            return "mp3"
        elif s.attr in ['.ttf', '.ttc', '.fon']:
            return "font"
        elif s.attr in ['.pdf']:
            return "pdf"
        elif s.attr in ['.xml', '.html', '.htm']:
            return "html"
        elif s.attr in ['.doc', '.docx', '.rtf']:
            return "docx"
        elif s.attr in ['.xls', '.xlsx', '.cav']:
            return "xlsx"
        elif s.attr in ['.jpg', '.png', '.gif', '.bmp', '.ico', '.raw']:
            return "jpg"
        elif s.attr in ['.scr', '.avi', '.rmvb', '.mp4', '.flv']:
            return "video"
        else:
            return "blank"

    def IsEditable(s):
        "判断是否可以编辑节点"
        Protect = ['C:\\Windows\\', 'C:\\ProgramData\\', 'C:\\Program Files\\', 'C:\\Documents and Settings\\']
        for dir in Protect:
            if s.dir.count(dir): return False  # 上面列出的文件夹及其子文件禁止编辑
        if s.attr == 'dir':
            if len(s.dir) == 3:
                return False  # 禁止编辑盘符
            else:
                return True
        elif s.attr not in ['root', 'piece', 'collect']:  # 判断文件是否可编辑
            return True
        else:
            return False

    def IsExpandable(s, skip_dir=True):
        "判断是否有子集。"
        if len(s.obj):
            return True
        elif s.attr == 'root':
            return True
        elif s.attr in ['dir', 'piece', 'collect']:
            if skip_dir:  # skip_dir是否跳过文件夹的判断
                return True  # 直接返回True可以大幅提升子文件夹多的文件夹打开速度,空文件夹点击后会再识别为空
            else:
                try:
                    len(os.listdir(s.dir))  # 可能无权限查看
                except:
                    return False
        else:
            return False

    def GetSubList(s):
        "返回子级的FileBrowserTreeItem对象列表,文件和文件夹区分开,直接排序是按拼音排序会比较混乱"
        dirlist = []  # 文件夹列表
        filelist = []  # 文件列表
        collect = []  # 收藏文件夹,直接显示在一级目录

        if not s.obj:
            # 尝试获取文件夹子集,无权限则跳过,放在这里获取而不是后面添加到文件夹子集里是为了减少不必要的运算,增加上级文件夹的打开效率
            try:
                s.obj = os.listdir(s.dir)
            except:
                pass

        for child in s.obj:
            if isinstance(child, tuple):  # 判断child是不是元组,是的话为磁盘或收藏文件夹
                collect.append(FileBrowserTreeItem(child))
                continue
            path = s.dir + child
            if not os.path.exists(path): continue  # 文件不存在则跳过,主要是规避收藏夹子集传入不存在文件（夹）
            if (len(path) > 3) and s.FileStat(path):  # 判断文件属性,不判断盘符,跳过隐藏文件和受保护文件
                continue
            if os.path.isdir(path):  # 先处理文件夹
                path += '\\'  # 文件夹尾加上'\\'
                dirlist.append(FileBrowserTreeItem((child, 'dir', path, [])))
            else:  # 处理文件
                filelist.append(
                    FileBrowserTreeItem((child, os.path.splitext(child)[1].lower(), path, [])))  # 先把文件信息存储到列表中,放文件夹列表后
        return dirlist + filelist + collect  # 文件夹排在文件前面,最后是收藏夹

    def OnDoubleClick(s):
        "双击返回完整路径。"
        if s.attr in ['.py', '.pyw']:  # 如果文件是py文件就打开模块浏览器
            treebrowser.new_Module_node(s.dir)
        print(s.dir)
        return s.dir

    def FileStat(s, file_path):
        "判断文件是否是隐藏文件及受保护文件"
        file_stat = os.stat(file_path)  # 函数获取文件的状态信息
        # st_file_attributes获取属性值
        if file_stat.st_file_attributes & 2:  # 隐藏文件的属性值为2,因此我们可以通过与运算（'&'）来判断文件的属性值中是否包含2来判断文件是否是隐藏文件
            return True
        if stat.S_ISREG(file_stat.st_mode):  # S_ISREG判断文件是否是普通文件,判断文件是否是受保护文件
            mode = stat.S_IMODE(file_stat.st_mode)  # 获取文件的权限模式
            if (mode & stat.S_IRUSR) and (mode & stat.S_IWUSR) and (mode & stat.S_IXUSR):  # 判断文件的用户权限
                return True
            elif (mode & stat.S_IRGRP) and (mode & stat.S_IWGRP) and (mode & stat.S_IXGRP):  # 判断文件的组权限
                return True
            elif (mode & stat.S_IROTH) and (mode & stat.S_IWOTH) and (mode & stat.S_IXOTH):  # 判断文件的其他用户权限
                return True
        return False


class Tree:
    '''创建一个树状结构的窗口。'''

    def __init__(s,root):
        s.node_list = []  # 存储node窗口
        s.root = root
    def main(s):
        "创建浏览器tkinter部件,包括树。"
        s.root = tk.Frame(s.root)
        s.root.place(x=0,y=70,width=355,height=800)
        s.root.focus_set()

        s.tab = ttk.Notebook(s.root)  # 创建Notebook选项卡控件
        s.tab.pack(expand=1, fill="both")  # 让Notebook控件显示出来
        s.tab.enable_traversal()  # 为s.tab启用键盘快捷方式,Control-Tab向后切换,Shift-Control-Tab向前切换

        # collect收藏文件夹,格式[(标题,图标标记,完整路径,子集列表),....],子集列表为空的话浏览下面所有文件（夹）,也可指定显示的子集文件夹
        collect = [('收藏1', 'collect', 'C:\\', ['Program Files', 'Users']), ('收藏2', 'collect', 'C:\\', [])]
        s.new_Module_node(path=module_path)  # 函数浏览器-浏览文件
        s.new_file_node(collect)  # 文件浏览器

        lah = '''
def 函数():
    def a1():
       def a11():''
       def a12():''
       def a13():''
    def a2():''
class 类:
    def b1(s):''
    def b2(s):''
        '''
        s.new_Module_node(text=lah)  # 函数浏览器-浏览字符串

    def new_node(s, text, item):
        "新建tab,并绘入node界面"
        new_tab = tk.Frame(s.tab)  # 添加tab选项卡
        s.tab.add(new_tab, text=text)
        new_Frame = tk.Frame(new_tab)
        new_Frame.pack(expand=1, fill="both")
        # 创建带滚动画布,canvas画布尽量和mainloop在同一函数下否则可能快捷键会失效
        new_Canvas = ScrolledCanvas(s.root, new_Frame, bg=bg_color, highlightthickness=0, takefocus=1).canvas
        new_node = TreeNode(new_Canvas, None, item)  # 将画布及内容传入TreeNode,绘制树状图
        new_node.update()  # 刷新node
        new_node.expand()  # 显示内容
        s.node_list.append(new_node)

    def new_Module_node(s, path=None, text=''):
        "新建模块浏览器窗口"
        # tree获取需要显示的类和函数
        tree = cscope(file=path, retarn_args=False, line_num=True, skip_comment=True,
                      text=text)  # 函数名不包含args,返回行数,跳过三引号注释
        key = next(iter(tree.keys()))  # 返回第一个key文件名,作为树状图的根
        item = ModuleBrowserTreeItem(key, tree[key])
        s.new_node('函数浏览器', item)

    def new_file_node(s, collect=[]):
        "新建文件浏览器窗口"
        # tree 需要显示树根"计算机"以及一级结构"硬盘分区"和"收藏文件夹"；chr()将整数转为字符串,再通过os.path.isdir判断A-Z是否有硬盘分区
        tree = ("计算机", "root", "",
                [(chr(i) + ':', 'piece', chr(i) + ':\\', []) for i in range(65, 91) if
                 os.path.isdir(chr(i) + ':\\')] + collect)
        item = FileBrowserTreeItem(tree)
        s.new_node('文件浏览器', item)


def cscope(file=None, retarn_args=False, line_num=True, skip_comment=True, text=''):
    '''
    file         类和函数结构的文件路径
    retarn_args  函数名是否包含args
    line_num     True返回行数,False返回位置
    skip_comment 是否跳过三引号注释,要考虑多种情况,会增加运算；最好的办法是关闭,然后规范代码,将注释内缩进设为一致
    text         需要获取类和函数的字符串
    '''
    if file:
        dir, base = os.path.split(file)
        name, ext = os.path.splitext(base)
        if os.path.normcase(ext) not in [".py", ".pyw"]:
            return {base: (0, ext, {})}

        text = open(file, 'r', encoding='utf-8').read()
    else:
        base = '类和函数'
        ext = '.py'

    flines = []
    idx = lpos = 0
    lst = text.splitlines()  # 获取文件行列表
    if not (lst): lst.append(u'')
    for index, line in enumerate(lst):
        lnum = index + 1  # 行数
        ln = line.strip()  # 去除空格后的字符串
        if not (ln):  # 跳过空行
            lpos += len(line) + 1
            continue
        ind = line.find(ln[0])  # 缩进
        flines.append((idx, lnum, ind, lpos, ln))  # (序号,行数,字符串缩进,行首的位置,去除空格后的字符串)
        idx += 1  # 序号
        lpos += len(line) + 1  # 下一行行首的位置

    last = root = {}
    end = {u'class': u'', u'def': u'()'}
    lev = [(0, root)]  # 用来临时存储同一缩进的函数
    comment = [False, (), [("'''", '"'), ('"""', "'")]]  # 用来存储注释信息
    for idx, lnum, ind, lpos, ln in flines:  # 序号,行数,字符串缩进,行的位置,去除空格后的字符串
        if skip_comment:  # 判断是否处理三引号注释
            if comment[0]:  # 本行在注释范围内
                flines[idx] = (idx, lnum, flines[(idx - 1)][1], lpos, ln)  # 将本行缩进改为上一行的缩进
                if ln.count(comment[1][0]): comment[0] = False  # 本行为注释行最后一行,结束跳过注释
                continue
            else:
                for mark in comment[2]:
                    if ln.count(mark[0]):  # 存在三引号
                        Lnum = ln.find(mark[0])  # 最左侧三引号位置
                        Rnum = ln.rfind(mark[0])  # 最右侧三引号位置
                        Mnum = divmod(ln[:Lnum].count(mark[1]), 2)[1]  # 判断三引号前有几个不同引号,如果为奇数则三引号在字符串内
                        Jnum = ln[:Rnum].rfind('#')  # 三引号前'#'的位置
                        if Jnum < 0 or (Jnum >= 0 and (ln[Jnum:Rnum].count('"') or ln[Jnum:Rnum].count("'"))):
                            # 不存在'#' 或 三引号和'#'之间存在引号。只是三引号出现的其中一种情况,都处理会增加计算
                            if Lnum == Rnum and not Mnum:  # 只存在一个三引号,且不是存在字符串内
                                comment[:2] = [True, mark]
                            elif Lnum < Rnum and Mnum and divmod(ln[Lnum:Rnum].count(mark[1]), 2)[
                                1]:  # 存在多个三引号,且最左侧的在字符串里面
                                comment[:2] = [True, mark]

        # 根据缩进级别更新lev列表，用于存储同一缩进级别的函数
        if ind < lev[-1][0]:  # 缩进 < lev最后标记的缩进
            if idx > 0:  # 序号 > 0
                rastrow = flines[(idx - 1)]  # 上一行列表
                if rastrow[-1][-1] in (u',', u'\\'):  # 上一行是以','或'\'结尾,跳过元组、列表、字典的换行缩进,以及长字符串中间的'\'换行
                    flines[idx] = (idx, lnum, rastrow[2], lpos, ln)  # 将本行缩进改为上一行的缩进,方便下一行比对
                    continue
                if ln[0] == '#':  # '#'注释
                    flines[idx] = (idx, lnum, rastrow[2], lpos, ln)  # 将本行缩进改为上一行的缩进,方便下一行比对
                    continue
            try:
                while ind < lev[-1][0]:  # 缩进 < 上一个缩进记录
                    lev.pop()  # 弹出lev最后一项,直至当前缩进和存储的最后一个缩进同级
            except IndexError:
                return None
        elif ind > lev[-1][0]:  # 缩进 > lev最后标记的缩进
            lev.append((ind, last))  # lev添加(缩进,字典)

        t = ln.split()  # 以空格分割成列表
        if t[0] in end.keys():  # 字符串列表第一位是'class'或'def'
            try:
                if retarn_args:  # 保留args
                    t = ln.split(' ', 1)
                    tok = t[1].split(u':')[0]  # 剪切'('及':'之前的部分
                    name = tok
                else:
                    tok = t[1].split(u'(')[0].split(u':')[0]  # 剪切'('及':'之前的部分
                    name = tok + end[t[0]]  # 加上end设置好的结尾
                if line_num:
                    num = lnum  # line_num 返回行数
                else:
                    num = lpos + ind  # 返回位置
                if name in lev[-1][1]:  # name和lev最后一项的字典里的函数重名
                    name = (u'%s%s*%d' % (tok, end[t[0]], num))  # name = tok:+字符串位置+end设置好的结尾
                last = {}  # 重置last
                lev[-1][1][name] = (num, t[0], last)  # lev最后一个元组标记的字典加入{name:(字符串位置,{})}
            except:
                pass
    root = {base: (0, ext, root)}  # 以文件名做树状图的根
    return root


def wheel_event(event, widget=None):
    """处理滚轮事件。
    在Windows上,滚轮向上滚动时,event.delta = 120*n。
    参数widget是必需的,以便浏览器标签绑定可以将底层画布传递过去。
    此函数依赖于widget.yview不会被子类覆盖。
    """
    # 判断滚轮是否向上滚动
    up = {tk.EventType.MouseWheel: event.delta > 0,
          tk.EventType.ButtonPress: event.num == 4}
    # 如果没有传入widget参数,则使用event中的widget属性
    widget = event.widget if widget is None else widget

    lines = 5
    if up[event.type]:  # 如果滚轮向上滚动
        lines = -5 if widget.canvasy(0) else 0  # lines = -5，如果可见区域的顶部纵坐标为0则lines = 0 防止过度向下

    widget.yview(tk.SCROLL, lines, 'units')  # 调用widget的yview方法进行滚动
    # 返回'break'以阻止事件继续传播
    return 'break'


class CustomNotebook(ttk.Notebook):  # 带关闭按钮的Notebook
    """定义一个名为CustomNotebook的类,继承自ttk.Notebook"""

    __initialized = False  # 初始化一个私有变量,用于标记是否已经初始化

    def __init__(s, *args, **kwargs):
        # 如果尚未初始化,则调用自定义初始化方法,并设置已初始化标志
        if not s.__initialized:
            s.__initialize_custom_style()
            CustomNotebook.__initialized = True
            # s.__inititialized = True # 这样会导致第二次调用出错,请用上面的方法标记

        # 设置notebook的样式为"CustomNotebook"
        kwargs["style"] = "CustomNotebook"
        # 调用父类的初始化方法
        ttk.Notebook.__init__(s, *args, **kwargs)

        s._active = None  # 初始化一个私有变量,用于存储当前活动的tab

        # 绑定鼠标左键按下事件到on_close_press方法
        s.bind("<ButtonPress-1>", s.on_close_press, True)
        # 绑定鼠标左键释放事件到on_close_release方法
        s.bind("<ButtonRelease-1>", s.on_close_release)

    def __initialize_custom_style(s):
        # 创建一个ttk样式对象
        style = ttk.Style()
        # 定义四个图片对象,分别表示关闭按钮的不同状态
        s.images = (
            # 元素普通状态时图标
            tk.PhotoImage("img_closenormal", data='''
                R0lGODdhCwALAIMAAJKSkpeXl5ubm5+fn6CgoKampqqqqq2trbGxsba2tr29vcHBwdnZ2QAAAAAAAAAA
                ACwAAAAACwALAAAIXQAXJEBwwEDBAgUGHEigYOCBhwYMEBCAIAEDBgYQXhwg4ACCiwwKgOQIEeRGjgUK
                GgBJYABKgyYZuBRAQORFmwwEBBhgE6FNAQAEDCBAtCVHoAcC6AzANAAAAAYCAgA7
                '''),
            # 选中的选项卡的关闭图标
            tk.PhotoImage("img_closeselected", data='''
                R0lGODdhCwALAIVUAJ9dcptfe6NfcpthfZ5hfJ9ifp5nfaNjda9lc6Rmea1nfqRpe6Fqfq9ofK1ofqxr
                frFndbJqeLJufZ9rgKpngaBqgKtpg6tphK5uhKxvia5xhq91iq1xjK1zj692jLFyg7N1hrJ3i7B2jbF4
                ja51ka94kq97l698mq9+m7B8mbB/nLCDn6aEoayMprCForGMq7KNq7KPrrOXt7WfwP///wAAAAAAAAAA
                AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAACwALAAAIcgBnwFiBwoQJEh0yUGARQ8YLFwRPHLwQ
                wEUMGjQOcsB4YYAKFxhpbMRooYCJFSlCYlTgoAAJFSlMhHTgQEGBDilSqoyggACGEiFFhGxwAINQGiNC
                gMAIQcADDR48bAjxQUIEBABaGJgwoQKDBQkOCGAREAA7
                '''),
            # 鼠标经过时选项卡的关闭图标
            tk.PhotoImage("img_closeactive", data='''
                R0lGODdhCwALAIVSAN5IN+lRNeBQP+5bPvtSP+FSQuJXR+VbRu5dQetfRuVbSf9dS/xeTO5iR+hhTOxl
                TP1wTP1iUP1kUv9lVPxnVv9rVP1pWP9rWv9vXv5/WP54Xf9yYv11YP90ZP99YP94af97bP99bv6BW/6C
                Yv6FYP+BZf6JZv+Eb/6Jav+Oa+eJe/+Bcf+Edf+Hef+KfP+Rd/+WfP+bev+Pgu+Rhv+RhP+ViP+Zjf+h
                lv+lmv+1rP+/twAAAAAAAAAAAAAAACwAAAAACwALAAAIcwB13KDhgkWIEB8wRJiBIwcOGzRktFjx
                wUKBGjh27GABYoNGCQZc2NC4owNJkCsIktRYoYKCDywmkizhQYODDSFWrNyRYsSDCSY1wiBJosGCCxpP
                vIihMcMAAgwoXOBQAoUJERACzAAAoICAAwkaIAigIiAAOw==
                '''),
            # 按下关闭按钮时选项卡的关闭图标
            tk.PhotoImage("img_closepressed", data='''
                R0lGODdhCwALAIUAAGsiD20jEHIkEHYlEXsnEX4oEogrE4orFIwsFJEtFJUvFZoxFpwwFp4yF6EzF6Yz
                F642GbU3GbY4Grk5Grk6G7s7G7w6G7w8G8A+HcJAHcVDH8ZEH8dEIMhGIMtJIsxKIs1KIpdxZ8eAbtqI
                cuKdiQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
                AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAACwALAAAIcABDABBA4AACBQscNBARIAGDBxAkVKhw
                oeIABiRIRJhQIeMFDAUeZCTRMWOGCwYgRBhpMgMGBBEqWBipYcOGDAoolBz5wcOGBRdGchjps0FQEhk6
                eMgIgoODihgycOgAAoQHDiIsYMBwoeYGDhtGBAQAOw==
                '''),
        )

        # 使用element_create方法创建一个名为"close"的元素,类型为"image",图像文件名为"img_closenormal"
        style.element_create("close", "image", "img_closenormal",
                             # 当元素处于激活、按下、未禁用状态时,显示"img_closepressed"图片
                             ("active", "pressed", "!disabled", "img_closepressed"),
                             # 当元素处于激活且未禁用状态时,显示"img_closeactive"图片
                             ("active", "!disabled", "img_closeactive"),
                             # 当选项卡处于选中状态时,显示"img_closeselected"图片
                             ("selected", "img_closeselected"),
                             # 设置元素的边框宽度为8像素,无边框；设置元素的粘性属性为空字符串,表示不粘附在其他元素上。
                             border=9, sticky='')
        '''
        notebook有如下状态
            disabled    禁用状态,该状态下的控件无法接收用户输入。
            normal      正常状态,该状态下的控件可以接收用户输入。
            active      激活状态(鼠标经过),该状态下的控件可以接收用户输入,并且会显示特殊效果(如闪烁)。
            selected    选中状态,该状态下的控件会显示特殊效果(如高亮)。
            insensitive 不敏感状态,该状态下的控件不会响应用户的键盘操作。
            focus       聚焦状态,该状态下的控件会显示特殊效果(如边框)。
        '''
        # 设置Notebook的样式为"CustomNotebook",并为"CustomNotebook.client"添加一个样式选项,设置其"sticky"属性为"nswe"
        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        # 设置CustomNotebook.Tab的布局样式
        style.layout("CustomNotebook.Tab", [
            ("CustomNotebook.tab", {  # 设置 CustomNotebook.tab 的样式
                "sticky": "nswe",  # 设置 tab 的粘性属性为 NSWE,表示在水平方向上可拉伸,垂直方向上可滚动
                "children": [  # 设置 tab 的子元素
                    ("CustomNotebook.padding", {  # 设置 CustomNotebook.padding 的样式
                        "side": "top",  # 设置 padding 的侧边距在顶部
                        "sticky": "nswe",  # 设置 padding 的粘性属性为 NSWE
                        "children": [  # 设置 padding 的子元素
                            ("CustomNotebook.focus", {  # 设置 CustomNotebook.focus 的样式
                                "side": "top",  # 设置 focus 的侧边距在顶部
                                "sticky": "nswe",  # 设置 focus 的粘性属性为 NSWE
                                "children": [  # 设置 focus 的子元素
                                    # 设置 CustomNotebook.label 的样式
                                    ("CustomNotebook.label", {"side": "left", "sticky": ''}),  # 设置 label 的侧边距在左侧,无粘性
                                    # 设置 CustomNotebook.close 的样式
                                    ("CustomNotebook.close", {"side": "left", "sticky": ''}),  # 设置 close 的侧边距在左侧,无粘性
                                ]
                            })
                        ]
                    })
                ]
            })
        ])

    def on_close_press(s, event):
        """当按钮被按下时触发,位于关闭按钮上方"""

        # 获取鼠标点击位置的元素
        element = s.identify(event.x, event.y)

        # 如果元素包含"close",则执行以下操作
        if "close" in element:
            # 获取鼠标点击位置的索引值
            index = s.index("@%d,%d" % (event.x, event.y))
            # 将按钮状态设置为按下
            s.state(['pressed'])
            # 将_active属性设置为点击的索引值
            s._active = index

    def on_close_release(s, event):
        """
        当鼠标在关闭按钮上释放时调用此方法。
        event:  包含鼠标事件信息的对象。
        """
        if not s.instate(['pressed']):  # 如果按钮没有按下状态,直接返回
            return
        try:
            element = s.identify(event.x, event.y)  # 获取鼠标释放位置的元素
            index = s.index("@%d,%d" % (event.x, event.y))  # 获取元素在列表中的索引
            if "close" in element and s._active == index:  # 元素是关闭按钮,且当前激活的标签页与释放位置的标签页相同
                s.event_generate("<<NotebookTabClosed>>")  # 生成一个表示标签页关闭的事件
                # s.forget(index)  # 删除该标签页,但并未销毁,要销毁需要用destroy(),也可以将删除写入NotebookTabClosed事件里面
        except:
            pass
        s.state(["!pressed"])  # 将按钮状态设置为非按下状态
        s._active = None  # 将当前激活的标签页设置为None # # #


class ScrolledText(tk.Text):  # 带右侧滚动条的文本框
    def __init__(s, master=None, **kw):
        s.frame = tk.Frame(master)
        s.vbar = tk.Scrollbar(s.frame)
        s.vbar.pack(side='right', fill='y')

        kw.update({'yscrollcommand': s.vbar.set})
        tk.Text.__init__(s, s.frame, **kw)
        s.pack(side='left', fill='both', expand=True)
        s.vbar['command'] = s.yview

        # Copy geometry methods of s.frame without overriding Text
        # methods -- hack!
        text_meths = vars(tk.Text).keys()
        methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        methods = methods.difference(text_meths)
        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(s, m, getattr(s.frame, m))

        # 为底层控件创建一个代理
        # 为变量s添加一个属性_orig,其值为s的_w属性值加上"_orig"字符串
        s._orig = s._w + "_orig"
        # 使用tkinter库的call方法,将s的_w属性对应的窗口重命名为_orig
        s.tk.call("rename", s._w, s._orig)
        # 使用tkinter库的createcommand方法, 为s的_w属性对应的窗口创建一个命令, 该命令执行s的_proxy属性对应的函数
        s.tk.createcommand(s._w, s._proxy)

    def __str__(s):
        return str(s.frame)

    def _proxy(s, command, *args):
        # 避免复制时出错
        if command == 'get' and (args[0] == 'sel.first' and args[1] == 'sel.last') and not s.tag_ranges('sel'): return
        # 避免删除时出错
        if command == 'delete' and (args[0] == 'sel.first' and args[1] == 'sel.last') and not s.tag_ranges(
            'sel'): return
        # if command not in ['index','yview','count']:
        # print (command, args)

        cmd = (s._orig, command) + args  # 将原始对象、命令和参数组合成一个新的命令
        try:
            result = s.tk.call(cmd)  # 调用新命令并获取结果
        except:
            pass
        if command in ("insert", "delete", "replace"):  # 如果命令是插入、删除或替换操作
            s.event_generate("<<TextModified>>")  # 生成一个<<TextModified>>事件,表示文本已被修改
        try:
            return result
        except:
            pass


class RowScrolledText:  # 左侧带行数显示的文本框
    def __init__(s, frame, master, spacing=5, font=("Microsoft YaHei light", 13)):
        s.root = master
        s.frame = frame
        # 创建一个文本框,用于输入和显示文本
        s.line_text = tk.Text(s.frame, width=10, height=13, spacing3=spacing, bg="#DCDCDC", bd=0,
                              font=font, takefocus=0, state="disabled", cursor="arrow")
        s.line_text.pack(side="left", expand="no")
        frame.update()  # 更新画布和文本框的显示

        # 创建一个带滚动条的文本框,用于显示大文本,设置边框样式为"ridge"、"solid"、"double"、"groove"、"ridgeless"或"none"
        s.ScrolledText = ScrolledText(s.frame, height=1,width=100,wrap="none", spacing3=spacing, bg="white", bd=0,
                                      font=font, undo=True, insertwidth=1, relief="solid")
        s.ScrolledText.vbar.configure(command=s.scroll)
        s.ScrolledText.pack(side="right", fill="both", expand=True)
        # events = s.ScrolledText.event_info()
        # print(events)

        # 每行插入数字,用来对比行数显示的效果

        s.line_text.bind("<MouseWheel>", s.wheel)  # line_text鼠标滚轮事件
        s.ScrolledText.bind("<MouseWheel>", s.wheel)  # ScrolledText鼠标滚轮事件
        s.ScrolledText.bind("<KeyPress-Up>", s.KeyPress_scroll)
        s.ScrolledText.bind("<KeyPress-Down>", s.KeyPress_scroll)
        s.ScrolledText.bind("<KeyPress-Left>", s.KeyPress_scroll)
        s.ScrolledText.bind("<KeyPress-Right>", s.KeyPress_scroll)
        s.ScrolledText.bind("<<Selection>>", s.on_selection)  # 文本选中事件
        s.ScrolledText.bind("<<TextModified>>", s.get_txt)  # 绑定文本修改事件
        s.show_line()  # 显示行数

    def on_selection(s, event):  # 处理选中文本事件
        # text = event.widget.get("sel.first", "sel.last") # 获取选中文本的内容
        s.line_text.yview('moveto', s.ScrolledText.vbar.get()[0])  # 确保选中拖动导致滚动条滚动时行数显示能同步

    def wheel(s, event):  # 处理鼠标滚轮事件
        # 根据鼠标滚轮滚动的距离,更新line_text和ScrolledText的垂直滚动位置
        s.line_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        s.ScrolledText.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def see_line(s, line):
        s.ScrolledText.see(f"{line}.0")
        s.line_text.see(f"{line}.0")

    def KeyPress_scroll(s, event=None, moving=0, row=0):
        # 光标所在行的行数和位置
        line, column = map(int, s.ScrolledText.index("insert").split('.'))
        # 屏幕显示范围最上面的行
        first_line = int(s.ScrolledText.index("@0,0").split('.')[0])
        # 屏幕显示范围最下面的行
        last_line = int(s.ScrolledText.index("@0," + str(s.ScrolledText.winfo_height())).split('.')[0])

        # 光标超显示范围事件,先滚动屏幕到光标能显示区域
        if line <= first_line + row or line >= last_line - row:
            s.see_line(line)

        if row: return  # show_line 转过来的到这里结束

        if event.keysym == 'Up':  # 按上键,在光标小于顶部能显示的下一行时激活滚动
            if line <= first_line + 1: moving = -1  # 这里用first_line+1,是为了防止最上面一行只露出一点的情况,下面同理
        elif event.keysym == 'Down':  # 按下键,在光标大于底部能显示的上一行时激活滚动
            if line >= last_line - 1: moving = 1
        elif event.keysym == 'Left':  # 按左键,在光标小于顶部能显示的下一行且光标在开头时激活滚动
            if line <= first_line + 1 and not column: moving = -1
        elif event.keysym == 'Right':  # 按右键,在光标大于底部能显示的上一行且光标在结尾时激活滚动
            text = s.ScrolledText.get("1.0", "end")  # 获取文本内容
            cursor_line = text.split("\n")[line - 1]  # 获取光标所在行内容
            line_length = len(cursor_line)  # 光标在当前行的位置
            if line >= last_line - 1 and column == line_length: moving = 1

        s.line_text.yview_scroll(moving, "units")
        s.ScrolledText.yview_scroll(moving, "units")

    def scroll(s, *xy):  # 处理滚动条滚动事件
        # 根据滚动条,更新line_text和ScrolledText的垂直滚动位置
        s.line_text.yview(*xy)
        s.ScrolledText.yview(*xy)

    def get_txt(s, event=None):  # 用于获取文本内容并显示
        '修改内容后需要的操作都可以写在这里'
        # txt = s.ScrolledText.get("1.0", "end")[:-1] # 文本框内容
        s.show_line()

    def show_line(s):
        # 获取文本行数
        text_lines = int(s.ScrolledText.index('end-1c').split('.')[0])
        # 计算行数最多右几位数,调整
        len_lines = len(str(text_lines))
        s.line_text['width'] = len_lines + 2

        # 将显示行数文本的状态设置为正常
        s.line_text.configure(state="normal")
        # 删除行文本中的所有内容
        s.line_text.delete("1.0", "end")

        # 遍历文本数组,逐行插入到行文本中
        for i in range(1, text_lines + 1):
            if i == 1:
                s.line_text.insert("end", " " * (len_lines - len(str(i)) + 1) + str(i))
            else:
                s.line_text.insert("end", "\n" + " " * (len_lines - len(str(i)) + 1) + str(i))

        s.scroll('moveto', s.ScrolledText.vbar.get()[0])  # 模拟滚动条滚动事件

        s.line_text.configure(state="disabled")  # 将行文本的状态设置为禁用

        s.KeyPress_scroll(row=1)  # 处理光标超过显示范围事件,否则行数会不同步


#主程序
class TEditor:  # 主窗口
    def __init__(s):
        super().__init__()
        s.scrolledtext_list = {}  # 存储scrolledtext窗口
        s.root = tk.Tk()
        s.save_images = (
            # 原色
            tk.PhotoImage('save_original', data='''
                R0lGODdhDgAOAIU9ADFjpTFjrTFjtTFrtTljrTlrrcDAwEJzvUpzvUp7vVJ7rVJ7vVqEvWOEvWOMzmuU
                zmuU1nOUxnOc1nOc3nuUxnucxnul53ut54Slzoylxoyl1oyt1ozGY5StxpS13py13qWtxqW9563G57XO
                773O78bW78bW987e9zlrvQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
                AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAADgAOAAAIjAAzUFhwIIXBgykYgDAQ4cQJFBAjQiTh
                oEOCExdQOJA4kcSBAycsaOSIwkKJASlCkoQ4IYSAFCYsOHDwoOZMBxI+vIxpoWfPCRKC6kxRwqdPoEE9
                BEhBwqiFoFA3LG26EgUEDUtHiOTAtSuHBxiybvXK1UEFAAhEiKhagUIBCg0ODBBAN4DdAAAIKAgIADs=
                '''),
            # 黑白
            tk.PhotoImage('save_gray', data='''
                R0lGODdhDgAOAIU9AFxcXF1dXV9fX2JiYmRkZGVlZW1tbW9vb3R0dHZ2dn5+foGBgYeHh46Ojo+Pj5CQ
                kJKSkpaWlpeXl6CgoKGhoaOjo6WlpaioqKmpqa2trbCwsLKysru7u8DAwMLCwsrKys3NzdTU1NXV1dzc
                3P///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
                AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAADgAOAAAIiwApQEhgoIDBgwUUZOjwYMQIEhAjQgTB
                4AKCERZIMJA4EYQBAyMmaORIYkKIAQVCkoQogUOAAiImMGDQoOZMBhE2vIw5oWdPCRGC6iwQwqdPoEE1
                ACgAwuiEoFAvLG26koSDCks/iMTAtSuGBhOybvXKlYEEAAc8eKgqAQIBCAsMDAhAF4BduwIQBAQAOw==
                '''),
            # 红色
            tk.PhotoImage('save_red', data='''
                R0lGODdhDgAOAIU9AP/h4f++vv+3t/+2tv+vr/+srP+kpP+iov+dnf+UlP+Skv+Pj/+Li/+Kiv+Hh/+F
                hf+Dg/+Cgv95ef94eP90dP9ycv9xcf9wcP9paf9jY/9gYP9YWP9WVv9RUf9PT/tHR/pGRvhERPVBQfM/
                P/I+PgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
                AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAADgAOAAAIiwAhUNjg4YPBgx80LDhQIUAAABAjQiSA
                oQGHAA4AYJA4kYAHDwEiaOQIIMKAEB9CkoQoAcGIDwIiYMBwoeZMDBMSvIwZoWdPCROC6vwwwKdPoEEV
                kPhAwGiEoFAbLG26EoCFB0sLiGTAtSuDCxGybvXKFYMEEh0MGKgqgQIIChk8hBhBl4RduyI4BAQAOw==
                '''),
            # 淡红色

        )

    def close(s, event=None):
        "关闭窗口。"
        s.root.destroy()
        os._exit(0)

    def win_menu(s):
        def child_command(parent, item):
            for m in item.keys():
                if type(item[m]) == dict:
                    menu = tk.Menu(parent, tearoff=0)
                    parent.add_cascade(label=m, menu=menu)
                    child_command(menu, item[m])
                elif "separator" in m:
                    parent.add_separator()
                elif m == "历史记录":
                    for L in item[m]:
                        parent.add_command(label=L, command=None)
                else:
                    parent.add_command(label=m, command=item[m])

        menu_dict = {
            "文件(F)": {
                "新建": None,
                "打开": None,
                "打开所在文件夹": None,
                "使用默认查看器打开": None,
                "打开文件夹作为工作区": None,
                "重新读取文件": None,
                "保存": None,
                "另存为": None,
                "全部保存": None,
                "重命名": None,
                "关闭": None,
                "全部关闭": None,
                "更多关闭方式": {
                    "关闭当前以外所有文件": None,
                    "关闭左侧所有文件": None,
                    "关闭右侧所有文件": None,
                    "关闭所有未修改文件": None},
                "从磁盘删除": None,
                "separator1": None,
                "读取会话": None,
                "保存会话": None,
                "separator2": None,
                "历史记录": ['1.aaaa.py', '2.bbbb.py', '3.cccc.py', '4.dddd.py', '5.eeee.py'],
                "separator3": None,
                "恢复最近关闭文件": None,
                "打开文件列表": None,
                "清除文件列表": None,
                "separator": None,
                "退出": None, },
            "编辑(E)": {
                "撤销": None,
                "恢复": None,
                "separator1": None,
                "剪切": None,
                "复制": None,
                "粘贴": None,
                "删除": None,
                "全选": None,
                "开始/结束 选择": None,
                "separator2": None,
                "复制到剪切板": {
                    "复制当前文件路径": None,
                    "复制当前文件名": None,
                    "复制当前目录路径": None, },
                "缩进": {
                    "插入制表符(缩进)": None,
                    "删除制表符(退格)": None},
                "转换大小写": {
                    "转成大写": None,
                    "转成小写": None,
                    "每词转成仅首字母大写": None,
                    "每词的首字母转成大写": None,
                    "每句转成仅首字母大写": None,
                    "每句的首字母转成大写": None,
                    "大小写互换": None,
                    "随机大小写": None, },
                "行操作": {
                    "复制当前行": None,
                    "删除连续重复行": None,
                    "分割行": None,
                    "合并行": None,
                    "上移当前行": None,
                    "下移当前行": None,
                    "移除空行": None,
                    "移除空行(包括空白字符)": None,
                    "在当前行上方插入空行": None,
                    "在当前行下方插入空行": None,
                    "separator1": None,
                    "升序排列文本行": None,
                    "升序排列整数": None,
                    "升序排列小数(逗号作为小数点)": None,
                    "升序排列小数(句号作为小数点)": None,
                    "separator2": None,
                    "降序排列文本行": None,
                    "降序排列整数": None,
                    "降序排列小数(逗号作为小数点)": None,
                    "降序排列小数(句号作为小数点)": None, },
                "注释/取消注释": {
                    "添加/删除单行注释": None,
                    "设置行注释": None,
                    "取消行注释": None,
                    "区块注释": None,
                    "取消区块注释": None, },
                "空白字符操作": {
                    "移除行尾空格": None,
                    "移除行首空格": None,
                    "移除行首和行尾空格": None,
                    "EOL转空格": None,
                    "移除非必须的空白和EOL": None,
                    "separator1": None,
                    "TAB转空格": None,
                    "空格转TAB(全部)": None,
                    "空格转TAB(行首)": None, },
                "separator3": None,
                "历史剪切板": None,
                "设为只读": None,
                "清除只读标记": None, },
            "搜索(S)": {
                "查找": None,
                "在文件中查找": None,
                "查找下一个": None,
                "查找上一个": None,
                "选定并查找下一个": None,
                "选定并查找上一个": None,
                "快速查找下一个": None,
                "快速查找上一个": None,
                "替换": None,
                "增量查找": None,
                "寻找结果": None,
                "下一个寻找结果": None,
                "上一个寻找结果": None,
                "行定位": None,
                "转到匹配的括号": None,
                "选中所有匹配括号间字符": None,
                "标记": None,
                "separator1": None,
                "标记所有": {
                    "使用格式1": None,
                    "使用格式2": None,
                    "使用格式3": None,
                    "使用格式4": None,
                    "使用格式5": None, },
                "清除颜色标记": {
                    "清除格式1": None,
                    "清除格式2": None,
                    "清除格式3": None,
                    "清除格式4": None,
                    "清除格式5": None,
                    "清除所有格式": None, },
                "到上一个颜色标记": {
                    "格式1": None,
                    "格式2": None,
                    "格式3": None,
                    "格式4": None,
                    "格式5": None,
                    "寻找格式": None, },
                "到下一个颜色标记": {
                    "格式1": None,
                    "格式2": None,
                    "格式3": None,
                    "格式4": None,
                    "格式5": None,
                    "寻找格式": None, },
                "separator2": None,
                "书签": {
                    "设置/取消书签": None,
                    "上一书签": None,
                    "下一书签": None,
                    "清除所有书签": None,
                    "剪切书签行": None,
                    "复制书签行": None,
                    "粘贴(替换)书签行": None,
                    "删除书签行": None,
                    "删除未标记行": None,
                    "反向标记书签": None, },
                "separator3": None,
                "查找范围内字符": None,
            },
            "视图(V)": {
                "总在最前": None,
                "切换全屏模式": None,
                "便签模式": None,
                "separator1": None,
                "将当前文件显示到": None,
                "separator2": None,
                "显示符号": None,
                "缩放": None,
                "移动/复制当前文档": None,
                "标签页(Tab)": None,
                "自动换行": None,
                "激活从视图": None,
                "隐藏行": None,
                "separator3": None,
                "折叠所有层次": None,
                "展开所有层次": None,
                "折叠当前层次": None,
                "展开当前层次": None,
                "折叠层次": None,
                "展开层次": None,
                "separator4": None,
                "摘要...": None,
                "separator5": None,
                "工程": None,
                "文件夹工作区": None,
                "文档结构图": None,
                "函数列表": None,
                "separator6": None,
                "垂直同步滚动": None,
                "水平同步滚动": None,
                "separator7": None,
                "文字方向从右到左": None,
                "文字方向从左到右": None,
                "separator8": None,
                "监视日志 (tail -f)": None, },
            "编码(N)": {
                "使用 ANSI 编码": None,
                "使用 UTF-8 编码": None,
                "使用 UTF-8-BOM 编码": None,
                "使用 UCS-2 Big Endian 编码": None,
                "使用 UCS-2 Little Endian 编码": None,
                "编码字符集": None,
                "separator1": None,
                "转为 ANSI 编码": None,
                "转为 UTF-8 编码": None,
                "转为 UTF-8-BOM 编码": None,
                "转为 UCS-2 Big Endian 编码": None,
                "转为 UCS-2 Little Endian 编码": None, },
            "设置(T)": {
                "首选项...": None,
                "语言格式设置...": None,
                "管理快捷键...": None,
                "separator1": None,
                "导入": {
                    "导入插件": None,
                    "导入主题": None, },
                "separator2": None,
                "编辑弹出菜单": None, },
            "工具(O)": {
                "MD5": {
                    "生成...": None,
                    "从文件生成...": None,
                    "从选区生成并复制到剪切板": None, },
                "SHA-256": {
                    "生成...": None,
                    "从文件生成...": None,
                    "从选区生成并复制到剪切板": None, }, },
            "运行(R)": {
                "运行": None,
                "管理快捷键": None, },
            "插件(P)": {
                "PyNpp": None,
                "MIME": None,
                "separator1": None,
                "插件管理": None,
                "separator2": None,
                "打开插件文件夹": None, },
        }

        menubar = tk.Menu(s.root)
        s.root.config(menu=menubar)
        child_command(menubar, menu_dict)

    def input_message(s,message):
        print(message)

    def input_terim_text(s,text):
        output = os.popen('ver').read()
        output = output.strip()
        text.insert(1.0,f'{output}\n(c) Microsoft Corporation。保留所有权利。\n')
    def geticonimage(s, name):
        "根据名称获取图标文件,生成tkImage对象返回"
        try:
            return s.iconimages[name]  # 如果存在同名图标,返回已经生成的tkImage对象
        except KeyError:
            pass
        file, ext = os.path.splitext(name)  # 获取文件名和后缀
        ext = ext or ".gif"  # 没有后缀的以".gif"为后缀
        fullname = os.path.join(icon_path, file + ext)  # 连接文件路径
        image = tk.PhotoImage(master=s.canvas, file=fullname)  # 生成tkImage对象
        s.iconimages[name] = image  # 将tkImage对象缓存在s.iconimages
        return image

    def button_menu(s, button_frame):
        canvas = tk.Canvas(button_frame, height=24, highlightthickness=0)
        canvas.pack(anchor='w', fill='x')

        # 绘制图片,贴图(这里的贴图必须是 全局 或者和 mainloop在同一个函数下，否则会被清除导致不显示)

    def mainExec(s):
        # 设置窗口大小和可调整性
        s.input_message('========================START========================')
        s.root.resizable(True, True)
        s.root.geometry("1920x1080")
        s.root.title("PyCode Studio 2024")
        s.root.protocol("WM_DELETE_WINDOW", s.close)
        s.root.focus_set()
        s.root.tk.call('tk', 'scaling', ScaleFactor / 75)
        s.input_message(f'complete to set dpi,ScaleFactor / 75 = {ScaleFactor / 75}')
        s.input_message(f'Version Code: {__PyCodeVersion__}')
        s.input_message(f'Version : {PyCodeVersion}')
        s.win_menu()  # 顶部菜单

        s.input_message('complete to laod Tree Path to the Workspace [1/1]')

        Label(s.root, bd=1, relief=SUNKEN, anchor=W, width=155,
              text='PyCode已就绪。        默认编码：utf-8       缩进:4个空格              配置方案:默认              文件:{NewFileName}             位置:{postion}           空闲内存:{FreeMemory}KB').place(
            x=0, y=900)
        s.input_message('complete to laod Message Basket to the Workspace [1/1]')

        button_frame = tk.Frame(s.root)
        button_frame.pack(anchor='w', side='top', fill='x')
        s.input_message('complete to laod Button Frame to the Workspace [1/1]')

        s.button_menu(button_frame)

        editor_frame = tk.Frame(s.root,width=6000000000)
        editor_frame.place(x=390,y=65)
        terim_frame = tk.Frame(s.root)
        terim_frame.place(x=200,y=700)
        s.input_message('complete to laod Editor Frame and Terim Frame to the Workspace [1/1]')

        s.editor_tab = CustomNotebook(editor_frame) # 创建Notebook选项卡控件
        s.editor_tab.pack(side='left')  # 让Notebook控件显示出来
        s.editor_tab.enable_traversal()  # 为s.editor_tab启用键盘快捷方式,Control-Tab向后切换,Shift-Control-Tab向前切换
        s.editor_tab.bind("<<NotebookTabClosed>>", s.EditorTabClosed)
        s.new_scrolledtext(title='Untitiled.py', image='save_gray')
        s.input_message('complete to laod Notebook to the Workspace [1/1]')

        s.tree = Tree(s.root)
        s.tree.main()
        s.input_message('complete to laod Tree to the Workspace [1/1]')

        s.run_button = ttk.Button(s.root, text='  ▶\n运行')

        s.stop_button = ttk.Button(s.root,text='  ■\n终止')

        s.share_button = ttk.Button(s.root,text='代码\n协同')

        s.terim_text = tk.Text(s.root,height=11,width=145,font=("Courier New", 8))

        s.cut_line = ttk.Label(s.root,text='|\n|')

        s.terim_line = ttk.Label(s.root,text='————终端——————————————————————————————————————————————————————————————————————')

        s.cut_line_2 = ttk.Label(s.root,text='———————————————————————————————————————————————————————————————————')

        s.undo_button = ttk.Button(s.root,text='↶撤销')

        s.redo_button = ttk.Button(s.root,text='↷重做')

        s.run_button.place(x=0, y=0)

        s.stop_button.place(x=135,y=0)

        s.share_button.place(x=270,y=0)

        s.cut_line.place(x=405,y=0)

        s.undo_button.place(x=440,y=0)

        s.redo_button.place(x=440,y=30)

        s.cut_line_2.place(x=600,y=20)

        s.terim_text.place(x=390,y=665)

        s.terim_line.place(x=390,y=625)

        s.input_terim_text(s.terim_text)

        s.input_message('complete to laod the Button to the Workspace [1/1]')

        s.input_message('Run the application successfully [1/1]')
        s.input_message('=========================END=========================')
        s.root.mainloop()
        return  'Exit application'
    def EditorTabClosed(s, event=None):
        children = s.editor_tab.children  # 所有标签信息,只要没有destroy,从创建开始的都可以查询到
        childstr = s.editor_tab.tabs()  # 所有的显示标签名称
        select = s.editor_tab.select()  # 选中要关闭的标签名称
        index = s.editor_tab.index('current')  # 选中要关闭的标签序号
        tab_dict = s.editor_tab.tab(index)  # 选中要关闭的标签信息
        select_frame = s.editor_tab.children[select.split('.')[-1]]  # 选中标签页的frame对象
        data = {'所有标签信息': children,
                '所有标签名称': childstr,
                '选中标签信息': tab_dict,
                '选中标签名称': select,
                '选中标签序号': index,
                '选中标签对象': select_frame,
                }
        # print (data)

        s.editor_tab.forget(index)  # 删除选中标签页,但并未销毁,再一次add输入选项卡名称可以继续调用,要销毁需要用destroy(),
        # select_frame.destroy() # 销毁选中标签页的frame对象
        if len(childstr) == 1: s.new_scrolledtext(title='new 1.py')  # 删除的是最后一个标签,则创建一个

    def new_scrolledtext(s, path=None, title='', image='save_original'):
        new_tab = tk.Frame(s.editor_tab,width=60000000)  # 添加tab选项卡
        s.editor_tab.add(new_tab, text=title, image=image, compound='left')

        new_Frame = tk.Frame(new_tab,width=600000)
        new_Frame.pack(side='left')  # 这里需要 fill="both", expand=True 否则窗口可能无法填充满

        rowscrolledtext = RowScrolledText(new_Frame, s.root)
        rowscrolledtext.see_line(0)

        ScrolledText = rowscrolledtext.ScrolledText
        text = ScrolledText.get(0.0, 'end')

if __name__ == "__main__":
    Application = TEditor()
    sys.exit(Application.mainExec())
