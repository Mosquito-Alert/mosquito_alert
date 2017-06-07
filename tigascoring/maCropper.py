import urllib2
import StringIO
import Tkinter
import Image
from PIL import ImageTk
# import imghdr

import ma

_HOST_Pictures = 'http://humboldt.ceab.csic.es/get_photo/q0n50KN2Tg1O0Zh/'
_IMG_def = '/home/jgarriga/mosquitoAlert/ma.png'
_IMG_def = '/home/jgarriga/Pictures/ceab/olighopodus_it3.jpg'


def image_list():
    (conn, cur) = ma.connect()
    t = ma.Table('tREPIMG', cur)
    t.rows = t.selectAll(cur)
    ma.disconnect(conn, cur)
    return [row[-1] for row in t.rows]


def image_get(img_idd='d1bbf374-4be1-4af0-ad6d-91644e163cc3', img_sze='medium'):
    img_url = _HOST_Pictures + img_idd + '/' + img_sze
    try:
        img_str = urllib2.urlopen(img_url).read()
        img_rgb = Image.open(StringIO.StringIO(img_str))
    except Exception, e:
        print e
        img_rgb = Image.open(_IMG_def)
    # imghdr.what('ignore', img)
    return img_rgb


def image_show(img_rgb=None):
    if img_rgb == None: img_rgb = Image.open(_IMG_def)
    img_rgb.show()


# +++ image-cropping functions +++

class Cropper:
    def __init__(self, img_list, crop_size, save_path, tk_size=(1000, 800), tk_mrgn=50):

        self.tk = Tkinter.Tk()
        self.tk.geometry('%dx%d' % tk_size)
        self.mrgn = tk_mrgn
        self.wdth = float(tk_size[0] - 2 * tk_mrgn)
        self.hght = float(tk_size[1] - 2 * tk_mrgn)

        self.tk.bind('<Button-1>', self.left_click)
        self.tk.bind('<Button-3>', self.right_click)

        self.button_next = Tkinter.Button(self.tk, text='next', command=self.image_next)
        self.button_prev = Tkinter.Button(self.tk, text='prev', command=self.image_prev)
        self.button_save = Tkinter.Button(self.tk, text='save', command=self.image_save)
        self.button_large = Tkinter.Button(self.tk, text='large', command=self.image_large)
        self.button_rotate = Tkinter.Button(self.tk, text='rotate', command=self.image_rotate)

        self.button_next.pack(side='right', anchor='s')
        self.button_prev.pack(side='right', anchor='s')
        self.button_save.pack(side='right', anchor='s')
        self.button_large.pack(side='right', anchor='s')
        self.button_rotate.pack(side='right', anchor='s')

        self.crop_size = crop_size
        self.save_path = save_path

        self.img_list = img_list
        self.img_list.reverse()
        self.curr_img = -1

    # self.image_next()

    def right_click(self, event):
        if hasattr(event.widget, 'photo'):
            self.image = self.iBase
            self.frame_reset()

    def left_click(self, event):
        if hasattr(event.widget, 'photo'):
            if (self.image.size[0] > self.crop_size and self.image.size[1] > self.crop_size):
                lft, rgh = max(0, event.x - self.crop_size / 2), min(self.image.size[0], event.x + self.crop_size / 2)
                top, btm = max(0, event.y - self.crop_size / 2), min(self.image.size[1], event.y + self.crop_size / 2)
                if lft == 0: rgh = self.crop_size
                if top == 0: btm = self.crop_size
                if rgh == self.image.size[0]: lft = rgh - self.crop_size
                if btm == self.image.size[1]: top = btm - self.crop_size
                self.image = self.image.crop(box=(lft, top, rgh, btm))
                self.frame_reset(lft, top)

    def frame_reset(self, lft=0, top=0):
        if hasattr(self, 'frame'): self.frame.destroy()
        self.tk.geometry('%dx%d' % (min(self.image.size[0] + 200, 800), min(self.image.size[1] + 200, 600)))
        self.tk.title(self.img_list[self.curr_img])
        photo = ImageTk.PhotoImage(self.image)
        self.frame = Tkinter.Label(self.tk, image=photo)
        self.frame.photo = photo
        self.frame.place(x=lft + self.mrgn, y=top + self.mrgn, width=self.image.size[0], height=self.image.size[1])

    # print self.image

    def image_rotate(self):
        self.image = self.image.rotate(90)
        self.frame_reset()

    def image_large(self):
        self.iBase = image_get(img_idd=self.img_list[self.curr_img][-1], img_sze='large')
        if self.iBase.size[0] > self.wdth or self.iBase.size[1] > self.hght:
            resize_factor = min(self.wdth / self.iBase.size[0], self.hght / self.iBase.size[1])
            self.iBase = self.iBase.resize([int(x * resize_factor) for x in self.iBase.size])
        self.image = self.iBase
        self.frame_reset()

    def image_prev(self):
        self.curr_img -= 1
        self.iBase = image_get(img_idd=self.img_list[self.curr_img][-1])
        self.image = self.iBase
        self.frame_reset()

    def image_next(self):
        self.curr_img += 1
        if self.curr_img < len(self.img_list):
            self.iBase = image_get(img_idd=self.img_list[self.curr_img])
            self.image = self.iBase
        # self.frame_reset()
        else:
            print '... finished processing all images !!'
            self.tk.destroy()

    def image_save(self):
        fName = _LOCAL_data + self.save_path + 'ci_' + str(self.img_list[self.curr_img][0]).zfill(6)
        self.image.save(fName + '.png')
        self.image_next()


def mycrop(img_list=[], crop_size=200, save_path='cropped_images/'):
    _cropper = Cropper(img_list, crop_size, save_path)
    _cropper.tk.mainloop()
