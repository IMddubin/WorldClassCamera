import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import cv2, imutils
import time
import datetime
import numpy as np


from_class = uic.loadUiType("src/Worldclass_camera.ui")[0]

class Camera(QThread):
    update = pyqtSignal()

    def __init__(self, sec=0):
        super().__init__()
        self.running = True
    
    def run(self):
        while self.running == True:
            self.update.emit()
            time.sleep(0.1)

    def stop(self):
        self.running = False

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.isAppOn = False
        self.isRecStart = False
        self.isediting = False
        self.isreset = False
        self.isthreshpush = False
        self.iscannypush = False
        self.isgraychecked = False
        self.pic_color = "origin"

        self.thresh_value = 0
        self.bright_value = 0
        self.saturate_value = 0
        self.blur_value = 0
        self.mosaic_value = 0
        self.canny_value = 0

        self.camera = Camera(self)
        self.camera.daemon = True

        self.record = Camera(self)
        self.record.daemon = True        

        # 초기 설정
        self.btn_album.hide()
        self.display.hide() # 화면
        self.btn_save.hide() # capture나 record를 가능하게 함
        self.camera_mode.hide()# 카메라 콤보박스
        self.record_status.hide() # 녹화중인지 상태 표시
        self.save_right.hide() # 저장완료
        self.edit_box.hide()
        self.btn_edit.hide()

        self.timer = QTimer(self) # 저장완료 떴다가 사라지기
        self.timer.timeout.connect(self.hideSaveLabel)

        # threshold 숨키기
        self.slide_thresh.setDisabled(True)
        self.percent_thresh.setDisabled(True)
        self.slide_canny.setDisabled(True)
        self.percent_canny.setDisabled(True)
        self.btn_edit.setDisabled(True)
        self.edit_box.setEnabled(False)
        self.btn_cancel.hide()
        self.btn_reset.hide()
        self.btn_done.hide()
        
        self.pixmap = QPixmap()

        self.btn_onoff.clicked.connect(self.app_onoff)
        self.camera.update.connect(self.updateCamera)
        self.btn_album.clicked.connect(self.go_album)

        # camera mode & save 방식
        self.record.update.connect(self.updateRecording)        
        self.btn_save.clicked.connect(self.save_file)
        self.camera_mode.currentIndexChanged.connect(self.change_btmode)

        # edit box buttons acted
        self.btn_edit.clicked.connect(self.editmode)
        self.btn_cancel.clicked.connect(self.cancel_editmode)
        self.btn_done.clicked.connect(self.done_editmode)
        self.btn_reset.clicked.connect(self.reset_editmode)

        # change R G B
        self.btn_red.clicked.connect(self.red_mode)
        self.btn_green.clicked.connect(self.green_mode)
        self.btn_blue.clicked.connect(self.blue_mode)

        # change bright, saturate
        self.slider_bright.valueChanged.connect(self.change_bright)
        self.slide_saturate.valueChanged.connect(self.change_saturate)

        self.gray_mode_box.clicked.connect(self.gray_mode_clicked)

        self.btn_thresh.clicked.connect(self.thresh_mode)
        self.btn_canny.clicked.connect(self.canny_mode)

        self.slide_thresh.valueChanged.connect(self.change_threshold)
        self.slider_blur.valueChanged.connect(self.change_blur)
        self.slide_mosaic.valueChanged.connect(self.change_mosaic)
        self.slide_canny.valueChanged.connect(self.change_canny)

    def gray_mode_clicked(self):
        if self.isgraychecked == False:
            self.isgraychecked = True
            # self.gray_mode()
        else: # graymode 헤제했을 때 event
            self.isgraychecked = False
            self.pic_color = "origin"
            self.isgraychecked = False
            self.gray_mode_box.setChecked(False)
            self.thresh_value = 0
            self.canny_value = 0
            self.slide_thresh.setValue(self.thresh_value)
            self.slide_canny.setValue(self.canny_value)          

    def canny_mode(self):
        if self.iscannypush == False:
            self.iscannypush = True
            self.slide_canny.setDisabled(False)
            self.percent_canny.setDisabled(False)             
        else:
            self.iscannypush = False
            self.slide_canny.setDisabled(True)
            self.percent_canny.setDisabled(True)
            self.canny_value = 0
            self.slide_canny.setValue(self.canny_value)   

    def thresh_mode(self):
        if self.isthreshpush == False:
            self.isthreshpush = True
            self.slide_thresh.setDisabled(False)
            self.percent_thresh.setDisabled(False)
        else:
            self.isthreshpush = False
            self.slide_thresh.setDisabled(True)
            self.percent_thresh.setDisabled(True)
            self.thresh_value = 0
            self.slide_thresh.setValue(self.thresh_value)
    

    def change_canny(self):
        self.canny_value = self.slide_canny.value()
        self.percent_canny.setText(str(self.canny_value))        

    def change_mosaic(self):
        self.mosaic_value = self.slide_mosaic.value()
        self.percent_mosaic.setText(str(self.mosaic_value))

    def change_blur(self):
        self.blur_value = self.slider_blur.value()
        self.percent_blur.setText(str(self.blur_value))

    def change_threshold(self):
        self.thresh_value = self.slide_thresh.value()
        self.percent_thresh.setText(str(self.thresh_value))
        
    def change_btmode(self):
        if self.camera_mode.currentText() == "Photo":
            self.btn_save.setText("Capture")
        else:
            self.btn_save.setText("Record")

    def save_file(self): # save버튼이 캡쳐인지 녹화인지 중앙제어
        if self.btn_save.text() == "Capture":
            self.capture()
        else:
            self.clickRecord()

    def capture(self):
        self.now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.now + ".png"
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        cv2.imwrite(filename, self.image)
        self.save_right.show()
        self.timer.start(1000)

    def updateRecording(self):
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.writer.write(self.image)        

    def clickRecord(self):
        if self.isRecStart == False:
            self.isRecStart = True
            self.recordingStart()
        else:
            self.isRecStart = False
            self.recordingStop()
            self.save_right.show()
            self.timer.start(1000)
            
    def hideSaveLabel(self):
        self.save_right.hide()
        self.timer.stop()
    
    def recordingStart(self):
        self.record_status.show()
        self.record.running = True
        self.record.start()
        
        self.now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.now + ".avi"
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")

        w = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.writer = cv2.VideoWriter(filename, self.fourcc, 20.0, (w,h))

    def recordingStop(self):
        self.record_status.hide()
        self.record.running = False
        self.writer.release()

    def change_bright(self):
        self.bright_value = self.slider_bright.value()
        self.percent_bright.setText(str(self.bright_value))

    def change_saturate(self):
        self.saturate_value = self.slide_saturate.value()
        self.percent_saturate.setText(str(self.saturate_value))

    def red_mode(self):
        if self.pic_color in ("origin", "green", "blue"):
            self.pic_color = "red"
        else: 
            self.pic_color = "origin"

    def green_mode(self):        
        if self.pic_color in ("origin", "red", "blue"):
            self.pic_color = "green"
        else:
            self.pic_color = "origin"

    def blue_mode(self):
        if self.pic_color in ("origin", "red", "green"):
            self.pic_color = "blue"
        else: 
            self.pic_color = "origin"

    def edit_group(self, status):
        if status == True:
            self.edit_box.setEnabled(True)
            self.btn_cancel.show()
            self.btn_reset.show()
            self.btn_done.show()
            self.btn_edit.hide()
        else:
            self.edit_box.setEnabled(False)
            self.btn_cancel.hide()
            self.btn_reset.hide()
            self.btn_done.hide()
            self.btn_edit.show()                

    def reset_editmode(self):
        self.pic_color = "origin"
        self.isthreshpush = False
        self.iscannypush = False
        self.isgraychecked = False
        self.gray_mode_box.setChecked(False)
        self.bright_value = 0
        self.saturate_value = 0
        self.thresh_value = 0
        self.blur_value = 0
        self.mosaic_value = 0
        self.canny_value = 0
        self.slider_bright.setValue(self.bright_value)
        self.slide_saturate.setValue(self.saturate_value)
        self.slide_thresh.setValue(self.thresh_value)
        self.slider_blur.setValue(self.blur_value)
        self.slide_mosaic.setValue(self.mosaic_value)
        self.slide_canny.setValue(self.canny_value)
        self.slide_thresh.setValue(self.thresh_value)  

    def done_editmode(self):
        self.isediting = False
        self.edit_group(self.isediting)          

    def cancel_editmode(self):
        self.isediting = False
        self.isthreshpush = False
        self.iscannypush = False
        self.pic_color = "origin"
        self.isgraychecked = False
        self.gray_mode_box.setChecked(False)
        self.bright_value = 0
        self.saturate_value = 0
        self.thresh_value = 0
        self.blur_value = 0
        self.mosaic_value = 0
        self.canny_value = 0
        self.slider_bright.setValue(self.bright_value)
        self.slide_saturate.setValue(self.saturate_value)
        self.slide_thresh.setValue(self.thresh_value)
        self.slider_blur.setValue(self.blur_value)
        self.slide_mosaic.setValue(self.mosaic_value)
        self.slide_canny.setValue(self.canny_value)
        self.slide_thresh.setDisabled(True)
        self.percent_thresh.setDisabled(True)  
        self.slide_canny.setDisabled(True)
        self.percent_canny.setDisabled(True)
        self.edit_group(self.isediting)

    def editmode(self):
        self.isediting = True
        self.edit_group(self.isediting)

    def app_onoff(self):
        if self.isAppOn == False:
            self.btn_onoff.setText("App OFF")
            self.btn_edit.show()
            self.edit_box.show()
            self.btn_edit.setEnabled(True)
            self.camera_mode.show()
            self.btn_album.show()
            self.display.show()
            self.btn_save.show()

            self.cameraStart()
            self.isAppOn = True
        else:
            self.btn_edit.setDisabled(True)
            self.camera_mode.hide()
            self.camera_mode.setCurrentIndex(0)
            self.change_btmode()
            self.cancel_editmode()
            self.btn_onoff.setText("App ON")
            self.edit_box.hide()
            self.btn_edit.hide()
            self.isAppOn = False
            self.btn_album.hide()
            self.display.hide()
            self.btn_save.hide()

            self.cameraStop()

    def cameraStart(self):
        self.camera.running = True
        self.camera.start()
        self.video = cv2.VideoCapture(0)
    
    def cameraStop(self):
        self.camera.running = False
        self.video.release()

    def updateCamera(self):
        # self.display.setText("Camera Running : " + str(self.count))
        retval, image = self.video.read()
        if retval:
            self.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, c = self.image.shape
            image_origin = self.image.copy()

            if (self.pic_color != "origin") & (self.isreset == False):
                if self.pic_color == "red":
                    image_red = self.image.copy()
                    image_red[:,:,1] = 0
                    image_red[:,:,2] = 0
                    self.image = image_red
                elif self.pic_color == "green":
                    image_green = self.image.copy()
                    image_green[:,:,0] = 0
                    image_green[:,:,2] = 0
                    self.image = image_green
                else:
                    image_blue = self.image.copy()
                    image_blue[:,:,0] = 0
                    image_blue[:,:,1] = 0
                    self.image = image_blue
            else:
                self.image = image_origin
                self.isreset = False              

            # 명암 채비 part
            self.image = np.clip(self.image + float(self.bright_value), 0, 255).astype(np.uint8)
            alpha = float(self.saturate_value/200)
            self.image = np.clip((1+alpha)*self.image - 128*alpha, 0, 255).astype(np.uint8)

            # blur, mosaic part
            self.image = cv2.blur(self.image, ksize = (self.blur_value+1, self.blur_value+1))
            small_img = cv2.resize(self.image, (w // int(self.mosaic_value+1), h // int(self.mosaic_value+1)))
            self.image = cv2.resize(small_img, (w, h), interpolation=cv2.INTER_NEAREST)

            # gray mode
            if self.isgraychecked == True:
                self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)    
                grayimage_origin = self.gray_image.copy()

                # threshold, canny edge part
                if self.isthreshpush == True:
                    retval, self.gray_image = cv2.threshold(self.gray_image, 100 + self.thresh_value, 255, cv2.THRESH_BINARY)
                else:   
                    self.gray_image = grayimage_origin

                if self.iscannypush == True:
                    self.gray_image = cv2.Canny(self.gray_image, 100+self.canny_value ,200)
                elif (self.isthreshpush == False) & (self.iscannypush == False):
                    self.gray_image = grayimage_origin
                else:
                    pass

                qimage = QImage(self.gray_image.data, w, h, w, QImage.Format_Grayscale8)
                # reset이나 cancel 같은 강제 종료가 있을경우
                if self.isreset == True:
                    qimage = QImage(self.image.data, w, h, c * w, QImage.Format_RGB888)
                    self.isreset = False
            else:
                # RGB 이미지를 QImage로 변환
                qimage = QImage(self.image.data, w, h, c * w, QImage.Format_RGB888)

            self.pixmap = self.pixmap.fromImage(qimage)
            self.pixmap = self.pixmap.scaled(self.display.width(), self.display.height())

            self.display.setPixmap(self.pixmap)

    def go_album(self):
        self.cameraStop()

        # file = QFileDialog.getOpenFileName(filter = "Pictures & Videos(*.jpg *.jpeg *.png *.bmp *.mp4 *.avi *.mov)")
        file = QFileDialog.getOpenFileName(filter = "Pictures & Videos(*.jpg *.jpeg *.png *.bmp)")
        image = cv2.imread(file[0])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        h,w,c = image.shape
        qimage = QImage(image.data, w, h, w*c, QImage.Format_RGB888)

        self.pixmap = self.pixmap.fromImage(qimage)
        self.pixmap = self.pixmap.scaled(self.display.width(), self.display.height())

        self.display.setPixmap(self.pixmap)

if __name__== "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()

    sys.exit(app.exec())
