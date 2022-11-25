import glob
import ffmpeg
import requests
import sys
import urllib.error
from bs4 import BeautifulSoup
from os import startfile, remove, replace, listdir, makedirs, getcwd
from PySide6.QtCore import QUrl, Qt, QThread, Signal, Slot, QMutex
from PySide6.QtGui import QIcon, QCloseEvent, QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QTabWidget, QVBoxLayout, QToolBar, \
    QLineEdit, QSizePolicy, QGroupBox, QComboBox, QLabel, QTextEdit, QStatusBar, QPushButton, QProgressBar, QMessageBox
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget
from pytube import YouTube
from time import strftime, gmtime
from variables import *


class Downloader(QThread):
    download_started_signal = Signal(bool)
    download_progress_signal = Signal(str, str)
    download_finished_signal = Signal(bool, str)

    def __init__(self, mw, url, filename, index):
        super(Downloader, self).__init__(mw)
        self.url = url
        self.filename = filename
        self.index = index
        self._mutex = QMutex()

    def run(self):
        self._mutex.lock()
        if not path.exists('./downloads/Music'):
            makedirs('./downloads/Music')
        if not path.exists('./downloads/Videos'):
            makedirs('./downloads/Videos')
        while True:
            try:
                self.current_page = YouTube(self.url, on_progress_callback=self.on_progress)
                if self.index == 1:
                    self.file_extension = ".mp4"
                    self.current_page.streams.filter(mime_type="video/mp4").order_by("resolution").order_by("fps").desc().first().download(filename="video", output_path=".\\downloads\\download_cache\\")
                    self.current_page.streams.filter(mime_type="audio/mp4", abr="128kbps").first().download(filename="audio", output_path=".\\downloads\\download_cache\\")
                    video = ffmpeg.input('.\\downloads\\download_cache\\video')
                    audio = ffmpeg.input('.\\downloads\\download_cache\\audio')
                    out = ffmpeg.output(video, audio, ".\\downloads\\download_cache\\" + self.filename + ".mp4",
                                        vcodec='copy', acodec='aac', strict='experimental')
                    ffmpeg.run(stream_spec=out, cmd='ffmpeg', quiet=True)
                    remove('.\\downloads\\download_cache\\video')
                    remove('.\\downloads\\download_cache\\audio')
                    replace('.\\downloads\\download_cache\\' + self.filename + '.mp4', '.\\downloads\\Videos\\' + self.filename + '.mp4')
                else:
                    self.file_extension = ".mp3"
                    self.current_page.streams.filter(mime_type="audio/mp4", abr="128kbps").first().download(filename="audio", output_path=".\\downloads\\download_cache\\")
                    audio = ffmpeg.input('.\\downloads\\download_cache\\audio')
                    out = ffmpeg.output(audio, ".\\downloads\\download_cache\\" + self.filename + ".mp3", )
                    ffmpeg.run(stream_spec=out, cmd='ffmpeg', quiet=True)
                    remove('.\\downloads\\download_cache\\audio')
                    replace('.\\downloads\\download_cache\\' + self.filename + '.mp3', '.\\downloads\\Music\\' + self.filename + '.mp3')
                self.download_finished_signal.emit(True, self.filename + self.file_extension)
                break
            except urllib.error.HTTPError:
                pass
        self._mutex.unlock()
        self.quit()

    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        self.download_progress_signal.emit(str(int(percentage_of_completion)), self.filename + self.file_extension)


class Info_Collector(QThread):
    title_signal = Signal(str)
    author_signal = Signal(str)
    view_signal = Signal(str)
    date_signal = Signal(str)
    length_signal = Signal(str)
    description_signal = Signal(str)
    video_quality_signal = Signal(str)
    video_frame_signal = Signal(str)
    sound_quality_signal = Signal(str)

    def __init__(self, mw, url):
        super(Info_Collector, self).__init__(mw)
        self.url = url
        self._mutex = QMutex()

    def run(self):
        self._mutex.lock()
        while True:
            try:
                self.current_page = YouTube(self.url)
                title = self.current_page.title
                author = self.current_page.author
                length = self.current_page.length
                while True:
                    try:
                        date = self.current_page.publish_date.strftime('X%d X%m X%Y').replace('X0', 'X').replace('X', '')
                        month = ""
                        if date[-6] == "1":
                            month = "Ocak"
                        if date[-6] == "2":
                            month = "Şubat"
                        if date[-6] == "3":
                            month = "Mart"
                        if date[-6] == "4":
                            month = "Nisan"
                        if date[-6] == "5":
                            month = "Mayıs"
                        if date[-6] == "6":
                            month = "Haziran"
                        if date[-6] == "7":
                            month = "Temmuz"
                        if date[-6] == "8":
                            month = "Ağustos"
                        if date[-6] == "9":
                            month = "Eylül"
                        if date[-7] == "1" and date[-6] == "0":
                            month = "Ekim"
                        if date[-7] == "1" and date[-6] == "1":
                            month = "Kasım"
                        if date[-7] == "1" and date[-6] == "2":
                            month = "Aralık"
                        date = self.current_page.publish_date.strftime('X%d ' + month + ' X%Y').replace('X0', 'X').replace('X', '')
                        break
                    except AttributeError:
                        pass
                description = self.current_page.description
                view = f'{self.current_page.views:,}'
                view = view.replace(',', '.')
                video_quality = self.current_page.streams.filter(mime_type="video/mp4").order_by("resolution").order_by("fps").desc().first().resolution
                video_frame = self.current_page.streams.filter(mime_type="video/mp4").order_by("resolution").order_by("fps").desc().first().fps
                sound_quality = self.current_page.streams.filter(mime_type="audio/mp4", abr="128kbps").first().abr
                self.title_signal.emit(str(title))
                self.author_signal.emit(str(author))
                self.view_signal.emit(str(view))
                self.date_signal.emit(str(date))
                self.description_signal.emit(description)
                self.video_quality_signal.emit(video_quality)
                self.video_frame_signal.emit(str(video_frame))
                self.sound_quality_signal.emit(sound_quality)
                self.length_signal.emit(str(length))
                break
            except urllib.error.HTTPError:
                pass
        self._mutex.unlock()
        self.quit()

class Update_Checker(QThread):
    library_update_signal = Signal(int)
    application_update_signal = Signal(int)

    def __init__(self, mw):
        super(Update_Checker, self).__init__(mw)
        self._mutex = QMutex()

    def run(self):
        self._mutex.lock()
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.58'}
        library_version_selector = "#content > div.banner > div > div.package-header__left > h1"
        library_version_url = "https://pypi.org/project/pytube/"
        while True:
            try:
                library_version_html = requests.get(library_version_url, headers=headers).text.encode("utf-8")
                library_version_parser = BeautifulSoup(library_version_html, "html.parser")
                library_version_data = library_version_parser.select_one(library_version_selector).contents[0][9:22]
                if library_version_data == PYTUBE_VERSION:
                    self.library_update_signal.emit(0)
                else:
                    self.library_update_signal.emit(1)
                break
            except (requests.ConnectionError, requests.Timeout) as exception:
                pass
        self._mutex.unlock()
        self.quit()

class YIP(QMainWindow):
    def __init__(self):
        super(YIP, self).__init__()

        self.setMinimumSize(1024, 768)
        self.setWindowIcon(QIcon(youtube_icon_x16))
        self.setWindowTitle(APPLICATION_NAME + " - " + APPLICATION_VERSION)

        self.youtube_Url = QUrl(youtube_url)

        self.main_Widget = QWidget()
        self.main_Layout = QVBoxLayout()
        self.main_Layout.setAlignment(Qt.AlignCenter)
        self.center_Layout = QHBoxLayout()

        self.status_Icon = QLabel()
        self.status_Pixmap = QPixmap(search_icon_x16)
        self.status_Icon.setPixmap(self.status_Pixmap)
        self.status_Message = QLabel("Video bekleniyor...")

        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet('QStatusBar::item {border: None;}')
        self.statusBar.setSizeGripEnabled(False)
        self.author_Label = QLabel(APPLICATION_AUTHOR)
        self.author_Label.setDisabled(True)

        self.statusBar.addWidget(self.status_Icon)
        self.statusBar.addWidget(self.status_Message)
        self.statusBar.addPermanentWidget(self.author_Label)

        self.browser_Tab = QTabWidget()
        self.browser_SizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.browser_SizePolicy.setHorizontalStretch(4)
        self.browser_Tab.setSizePolicy(self.browser_SizePolicy)
        self.browser_ToolBar = QToolBar()
        self.browser_Widget = QWidget()
        self.browser_Layout = QVBoxLayout()
        self.browser_WebView = QWebEngineView()
        self.browser_WebView.setUrl(self.youtube_Url)
        self.browser_WebView.page().profile().setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        self.browser_WebView.page().profile().setHttpCacheType(QWebEngineProfile.NoCache)
        self.browser_WebView.page().setZoomFactor(1.0)
        self.browser_WebView.settings().setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        self.browser_WebView.setContextMenuPolicy(Qt.NoContextMenu)
        self.browser_WebView.titleChanged.connect(self.title_changed)
        self.browser_WebView.iconChanged.connect(self.icon_changed)
        self.browser_WebView.urlChanged.connect(self.url_changed)
        self.browser_Layout.addWidget(self.browser_WebView)
        self.browser_Widget.setLayout(self.browser_Layout)
        self.browser_Tab.addTab(self.browser_Widget, QIcon(find_icon_x16), "YouTube")

        self.browser_homepage_Action = QAction(QIcon(homepage_icon_x16), "Ana Sayfa", self)
        self.browser_homepage_Action.triggered.connect(self.home_page)
        self.browser_back_Action = QAction(QIcon(back_icon_x16), "Önceki Sayfa", self)
        self.browser_back_Action.setDisabled(True)
        self.browser_back_Action.triggered.connect(self.back_page)
        self.browser_forward_Action = QAction(QIcon(forward_icon_x16), "Sonraki Sayfa", self)
        self.browser_forward_Action.setDisabled(True)
        self.browser_forward_Action.triggered.connect(self.forward_page)
        self.browser_refresh_Action = QAction(QIcon(refresh_icon_x16), "Sayfayı Yenile", self)
        self.browser_refresh_Action.triggered.connect(self.refresh_page)
        self.browser_show_video_Action = QAction(QIcon(show_video_icon_x16), "İndirilen Videoları Görüntüle", self)
        self.browser_show_video_Action.triggered.connect(self.show_video)
        self.browser_show_music_Action = QAction(QIcon(show_music_icon_x16), "İndirilen Sesleri Görüntüle", self)
        self.browser_show_music_Action.triggered.connect(self.show_music)
        self.browser_zoom_out_Action = QAction(QIcon(zoom_out_icon_x16), "Uzaklaştır", self)
        self.browser_zoom_out_Action.triggered.connect(self.zoom_out)
        self.browser_zoom_in_Action = QAction(QIcon(zoom_in_icon_x16), "Yakınlaştır", self)
        self.browser_zoom_in_Action.triggered.connect(self.zoom_in)
        self.browser_mute_Action = QAction(QIcon(unmute_icon_x16), "Sesi Kapat", self)
        self.browser_mute_Action.triggered.connect(self.mute)
        self.browser_unmute_Action = QAction(QIcon(mute_icon_x16), "Sesi Aç", self)
        self.browser_unmute_Action.triggered.connect(self.unmute)
        self.browser_ToolBar.addAction(self.browser_homepage_Action)
        self.browser_ToolBar.addAction(self.browser_refresh_Action)
        self.browser_ToolBar.addAction(self.browser_mute_Action)
        self.browser_ToolBar.addAction(self.browser_zoom_out_Action)
        self.browser_ToolBar.addAction(self.browser_zoom_in_Action)
        self.browser_ToolBar.addAction(self.browser_show_music_Action)
        self.browser_ToolBar.addAction(self.browser_show_video_Action)
        self.browser_ToolBar.addAction(self.browser_back_Action)
        self.browser_ToolBar.addAction(self.browser_forward_Action)
        self.browser_Tab.setCornerWidget(self.browser_ToolBar)

        self.right_Tab = QTabWidget()
        self.right_SizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.right_SizePolicy.setHorizontalStretch(1)
        self.right_Tab.setSizePolicy(self.right_SizePolicy)
        self.right_Tab.setDisabled(True)
        self.right_Tab.currentChanged.connect(self.tab_changed)

        self.info_Widget = QWidget()
        self.info_Layout = QVBoxLayout()
        self.info_Layout.setAlignment(Qt.AlignTop)

        self.info_title_GroupBox = QGroupBox(" Başlık : ")
        self.info_title_Label = QLineEdit("")
        self.info_title_Label.setAlignment(Qt.AlignCenter)
        self.info_title_Label.setReadOnly(True)
        self.info_title_Layout = QVBoxLayout()
        self.info_title_Layout.addWidget(self.info_title_Label)
        self.info_title_GroupBox.setLayout(self.info_title_Layout)

        self.info_author_GroupBox = QGroupBox(" Yayıncı : ")
        self.info_author_Label = QLineEdit("")
        self.info_author_Label.setAlignment(Qt.AlignCenter)
        self.info_author_Label.setReadOnly(True)
        self.info_author_Layout = QVBoxLayout()
        self.info_author_Layout.addWidget(self.info_author_Label)
        self.info_author_GroupBox.setLayout(self.info_author_Layout)

        self.info_length_GroupBox = QGroupBox(" Uzunluk : ")
        self.info_length_Label = QLineEdit("")
        self.info_length_Label.setAlignment(Qt.AlignCenter)
        self.info_length_Label.setReadOnly(True)
        self.info_length_Layout = QVBoxLayout()
        self.info_length_Layout.addWidget(self.info_length_Label)
        self.info_length_GroupBox.setLayout(self.info_length_Layout)

        self.info_view_GroupBox = QGroupBox(" Görüntüleme : ")
        self.info_view_Label = QLineEdit("")
        self.info_view_Label.setAlignment(Qt.AlignCenter)
        self.info_view_Label.setReadOnly(True)
        self.info_view_Layout = QVBoxLayout()
        self.info_view_Layout.addWidget(self.info_view_Label)
        self.info_view_GroupBox.setLayout(self.info_view_Layout)

        self.info_rating_GroupBox = QGroupBox(" Oylama : ")
        self.info_rating_Label = QLineEdit("")
        self.info_rating_Label.setAlignment(Qt.AlignCenter)
        self.info_rating_Label.setReadOnly(True)
        self.info_rating_Layout = QVBoxLayout()
        self.info_rating_Layout.addWidget(self.info_rating_Label)
        self.info_rating_GroupBox.setLayout(self.info_rating_Layout)

        self.info_date_GroupBox = QGroupBox(" Paylaşım Tarihi : ")
        self.info_date_Label = QLineEdit("")
        self.info_date_Label.setAlignment(Qt.AlignCenter)
        self.info_date_Label.setReadOnly(True)
        self.info_date_Layout = QVBoxLayout()
        self.info_date_Layout.addWidget(self.info_date_Label)
        self.info_date_GroupBox.setLayout(self.info_date_Layout)

        self.info_description_GroupBox = QGroupBox(" Açıklama : ")
        self.info_description_Label = QTextEdit("")
        self.info_description_Label.setAlignment(Qt.AlignCenter)
        self.info_description_Label.setReadOnly(True)
        self.info_description_Layout = QVBoxLayout()
        self.info_description_Layout.addWidget(self.info_description_Label)
        self.info_description_GroupBox.setLayout(self.info_description_Layout)

        self.info_Layout.addWidget(self.info_title_GroupBox)
        self.info_Layout.addWidget(self.info_length_GroupBox)
        self.info_Layout.addWidget(self.info_view_GroupBox)
        self.info_Layout.addWidget(self.info_date_GroupBox)
        self.info_Layout.addWidget(self.info_author_GroupBox)
        self.info_Layout.addWidget(self.info_description_GroupBox)
        self.info_Widget.setLayout(self.info_Layout)

        self.right_Tab.addTab(self.info_Widget, QIcon(browser_icon_x16), "Bilgiler")

        self.download_Widget = QWidget()
        self.download_Layout = QVBoxLayout()
        self.download_Layout.setAlignment(Qt.AlignTop)

        self.download_title_GroupBox = QGroupBox(" Dosya Adı : ")
        self.download_title_LineEdit = QLineEdit()
        self.download_title_LineEdit.setAlignment(Qt.AlignCenter)
        self.download_title_LineEdit.setMaxLength(255)
        self.download_title_Layout = QVBoxLayout()
        self.download_title_Layout.addWidget(self.download_title_LineEdit)
        self.download_title_GroupBox.setLayout(self.download_title_Layout)

        self.download_video_quality_GroupBox = QGroupBox(" Video Kalitesi : ")
        self.download_video_quality_Label = QLineEdit("")
        self.download_video_quality_Label.setAlignment(Qt.AlignCenter)
        self.download_video_quality_Label.setReadOnly(True)
        self.download_video_quality_Layout = QVBoxLayout()
        self.download_video_quality_Layout.addWidget(self.download_video_quality_Label)
        self.download_video_quality_GroupBox.setLayout(self.download_video_quality_Layout)

        self.download_video_frame_GroupBox = QGroupBox(" Video Kare Hızı : ")
        self.download_video_frame_Label = QLineEdit("")
        self.download_video_frame_Label.setAlignment(Qt.AlignCenter)
        self.download_video_frame_Label.setReadOnly(True)
        self.download_video_frame_Layout = QVBoxLayout()
        self.download_video_frame_Layout.addWidget(self.download_video_frame_Label)
        self.download_video_frame_GroupBox.setLayout(self.download_video_frame_Layout)

        self.download_sound_quality_GroupBox = QGroupBox(" Ses Kalitesi : ")
        self.download_sound_quality_Label = QLineEdit("")
        self.download_sound_quality_Label.setAlignment(Qt.AlignCenter)
        self.download_sound_quality_Label.setReadOnly(True)
        self.download_sound_quality_Layout = QVBoxLayout()
        self.download_sound_quality_Layout.addWidget(self.download_sound_quality_Label)
        self.download_sound_quality_GroupBox.setLayout(self.download_sound_quality_Layout)

        self.download_type_GroupBox = QGroupBox(" İndirme Türü : ")
        self.download_type_ComboBox = QComboBox()
        self.download_type_ComboBox.setEditable(True)
        self.download_type_ComboBox.lineEdit().setAlignment(Qt.AlignCenter)
        self.download_type_ComboBox.lineEdit().setReadOnly(True)
        self.download_type_ComboBox.addItem("Ses")
        self.download_type_ComboBox.addItem("Video")
        self.download_type_Layout = QVBoxLayout()
        self.download_type_Layout.addWidget(self.download_type_ComboBox)
        self.download_type_GroupBox.setLayout(self.download_type_Layout)

        self.download_history_GroupBox = QGroupBox(" İndirme Geçmişi : ")
        self.download_history_Label = QTextEdit()
        self.download_history_Label.setReadOnly(True)
        self.download_history_Layout = QVBoxLayout()
        self.download_history_Layout.addWidget(self.download_history_Label)
        self.download_history_GroupBox.setLayout(self.download_history_Layout)

        self.download_Button = QPushButton(QIcon(download_icon_x16), " İndir")
        self.download_Button.clicked.connect(self.download_button)

        self.download_ProgressBar = QProgressBar()
        self.download_ProgressBar.setAlignment(Qt.AlignCenter)
        self.download_ProgressBar.setTextVisible(True)
        self.statusBar.addWidget(self.download_ProgressBar, 1)
        self.download_ProgressBar.hide()

        self.download_Layout.addWidget(self.download_title_GroupBox)
        self.download_Layout.addWidget(self.download_video_quality_GroupBox)
        self.download_Layout.addWidget(self.download_video_frame_GroupBox)
        self.download_Layout.addWidget(self.download_sound_quality_GroupBox)
        self.download_Layout.addWidget(self.download_type_GroupBox)
        self.download_Layout.addWidget(self.download_history_GroupBox)
        self.download_Layout.addWidget(self.download_Button)
        self.download_Widget.setLayout(self.download_Layout)

        self.right_Tab.addTab(self.download_Widget, QIcon(download_icon_x16), "İndir")

        self.center_Layout.addWidget(self.browser_Tab)
        self.center_Layout.addWidget(self.right_Tab)
        self.main_Layout.addLayout(self.center_Layout)
        self.main_Layout.addWidget(self.statusBar)
        self.main_Widget.setLayout(self.main_Layout)

        self.setCentralWidget(self.main_Widget)
        self.showMaximized()

        self.update_checker_thread = Update_Checker(self)
        self.update_checker_thread.library_update_signal.connect(self.get_library_update_status)
        # self.update_checker_thread.application_update_signal.connect()
        self.update_checker_thread.start()

    def get_library_update_status(self, status):
        if status == 0:
            print("no library update required")
        elif status == 1:
            print("library update required")
        else:
            print("library update check error")

    def title_changed(self, title):
        self.browser_Tab.setTabText(0, title)

    def icon_changed(self, icon):
        pass

    def url_changed(self, url):
        if self.browser_WebView.history().canGoBack():
            self.browser_back_Action.setEnabled(True)
        else:
            self.browser_back_Action.setDisabled(True)

        if self.browser_WebView.history().canGoForward():
            self.browser_forward_Action.setEnabled(True)
        else:
            self.browser_forward_Action.setDisabled(True)

        try:
            self.info_Thread.terminate()
        except AttributeError:
            pass

        self.disable_right_tab()

        if url.toString().startswith(key):
            try:
                if self.download_Thread.isRunning() is True:
                    self.status_Pixmap.load(download_icon_x16)
                    self.status_Icon.setPixmap(self.status_Pixmap)
                    self.status_Message.setText("İndiriliyor...")
                else:
                    self.status_Pixmap.load(browser_icon_x16)
                    self.status_Icon.setPixmap(self.status_Pixmap)
                    self.status_Message.setText("Bilgiler yükleniyor...")
            except AttributeError:
                self.status_Pixmap.load(browser_icon_x16)
                self.status_Icon.setPixmap(self.status_Pixmap)
                self.status_Message.setText("Bilgiler yükleniyor...")
            self.info_Thread = Info_Collector(self, url.toString())
            self.info_Thread.title_signal.connect(self.get_title)
            self.info_Thread.author_signal.connect(self.get_author)
            self.info_Thread.length_signal.connect(self.get_length)
            self.info_Thread.view_signal.connect(self.get_view)
            self.info_Thread.date_signal.connect(self.get_date)
            self.info_Thread.description_signal.connect(self.get_description)
            self.info_Thread.video_quality_signal.connect(self.get_video_quality)
            self.info_Thread.video_frame_signal.connect(self.get_video_frame)
            self.info_Thread.sound_quality_signal.connect(self.get_sound_quality)
            self.info_Thread.start()
        else:
            self.disable_right_tab()

    def home_page(self):
        self.browser_WebView.setUrl(self.youtube_Url)

    def back_page(self):
        self.browser_WebView.page().triggerAction(QWebEnginePage.Back)

    def forward_page(self):
        self.browser_WebView.page().triggerAction(QWebEnginePage.Forward)

    def refresh_page(self):
        self.browser_WebView.page().triggerAction(QWebEnginePage.Reload)

    def tab_changed(self):
        if self.right_Tab.currentIndex() == 1:
            self.download_title_LineEdit.setFocus()
            self.download_title_LineEdit.setText(self.title)
        else:
            pass

    def disable_right_tab(self):
        self.right_Tab.setCurrentIndex(0)
        self.right_Tab.setDisabled(True)
        self.info_title_Label.setText("")
        self.info_author_Label.setText("")
        self.info_length_Label.setText("")
        self.info_view_Label.setText("")
        self.info_date_Label.setText("")
        self.info_description_Label.setText("")
        self.download_title_LineEdit.setText("")
        self.download_video_quality_Label.setText("")
        self.download_video_frame_Label.setText("")
        self.download_sound_quality_Label.setText("")
        self.download_type_ComboBox.setCurrentIndex(0)
        try:
            if self.download_Thread.isRunning() is True:
                self.status_Pixmap.load(download_icon_x16)
                self.status_Icon.setPixmap(self.status_Pixmap)
                self.status_Message.setText("İndiriliyor...")
            else:
                self.status_Pixmap.load(search_icon_x16)
                self.status_Icon.setPixmap(self.status_Pixmap)
                self.status_Message.setText("Video bekleniyor...")
        except AttributeError:
            self.status_Pixmap.load(search_icon_x16)
            self.status_Icon.setPixmap(self.status_Pixmap)
            self.status_Message.setText("Video bekleniyor...")

    def show_video(self):
        if not path.exists('./downloads/Videos'):
            makedirs('./downloads/Videos')
        startfile(getcwd() + './downloads/Videos/')

    def show_music(self):
        if not path.exists('./downloads/Music'):
            makedirs('./downloads/Music')
        startfile(getcwd() + '/downloads/Music/')

    def zoom_out(self):
        self.browser_zoom_in_Action.setEnabled(True)
        if self.browser_WebView.page().zoomFactor() <= 0.75:
            pass
        else:
            self.browser_WebView.page().setZoomFactor(self.browser_WebView.page().zoomFactor() - 0.25)
            if self.browser_WebView.page().zoomFactor() <= 0.75:
                self.browser_zoom_out_Action.setDisabled(True)

    def zoom_in(self):
        self.browser_zoom_out_Action.setEnabled(True)
        if self.browser_WebView.page().zoomFactor() >= 1.25:
            pass
        else:
            self.browser_WebView.page().setZoomFactor(self.browser_WebView.page().zoomFactor() + 0.25)
            if self.browser_WebView.page().zoomFactor() >= 1.25:
                self.browser_zoom_in_Action.setDisabled(True)

    def mute(self):
        self.browser_ToolBar.removeAction(self.browser_mute_Action)
        self.browser_ToolBar.insertAction(self.browser_zoom_out_Action, self.browser_unmute_Action)
        self.browser_WebView.page().setAudioMuted(True)

    def unmute(self):
        self.browser_ToolBar.removeAction(self.browser_unmute_Action)
        self.browser_ToolBar.insertAction(self.browser_zoom_out_Action, self.browser_mute_Action)
        self.browser_WebView.page().setAudioMuted(False)

    def download_button(self):
        self.download_Button.setDisabled(True)
        self.download_title_LineEdit.setReadOnly(True)
        self.download_type_ComboBox.setDisabled(True)
        self.status_Message.setText("İndiriliyor...")
        self.download_ProgressBar.show()
        self.download_ProgressBar.setTextVisible(True)
        self.download_ProgressBar.setValue(0)
        url = self.browser_WebView.url().toString()
        filename = self.download_title_LineEdit.text().replace('/', '-').replace('\\', '-').replace('|', '-').replace(':', '-').replace('*', '-').replace('?', '').replace('"', '').replace('<', "").replace('>', "")
        index = self.download_type_ComboBox.currentIndex()
        if self.download_type_ComboBox.currentIndex() == 1:
            self.download_ProgressBar.setFormat(filename + ".mp4 " + "[0%]")
        else:
            self.download_ProgressBar.setFormat(filename + ".mp3 " + "[0%]")
        self.download_Thread = Downloader(self, url, filename, index)
        self.download_Thread.download_progress_signal.connect(self.download_progress)
        self.download_Thread.download_finished_signal.connect(self.download_finished)
        self.download_Thread.start()

    @Slot(str, str)
    def download_progress(self, progress, title):
        self.download_ProgressBar.setValue(int(progress))
        self.download_ProgressBar.setFormat(title + " [" + progress + "%]")

    @Slot(bool, str)
    def download_finished(self, finished, filename):
        if finished is True:
            self.browser_WebView.setDisabled(False)
            self.download_Button.setDisabled(False)
            self.browser_homepage_Action.setDisabled(False)
            self.browser_refresh_Action.setDisabled(False)
            self.browser_back_Action.setDisabled(False)
            self.browser_forward_Action.setDisabled(False)
            self.download_title_LineEdit.setReadOnly(False)
            self.download_title_LineEdit.setFocus()
            self.download_type_ComboBox.setDisabled(False)
            self.download_ProgressBar.hide()
            self.download_history()
            self.status_Message.setText("İndirme tamamlandı.")

    @Slot(str)
    def get_title(self, title):
        self.title = title
        self.disable_right_tab()
        self.info_title_Label.setText(title)
        self.download_title_LineEdit.setText(title)

    @Slot(str)
    def get_author(self, author):
        self.info_author_Label.setText(author)

    @Slot(str)
    def get_view(self, view):
        self.info_view_Label.setText(view)

    @Slot(str)
    def get_rating(self, rating):
        self.info_rating_Label.setText(rating)

    @Slot(str)
    def get_date(self, date):
        self.info_date_Label.setText(date)

    @Slot(str)
    def get_description(self, description):
        self.info_description_Label.setText(description)

    @Slot(str)
    def get_video_quality(self, video_quality):
        self.download_video_quality_Label.setText(video_quality)

    @Slot(str)
    def get_video_frame(self, video_frame):
        self.download_video_frame_Label.setText(video_frame+"fps")

    @Slot(str)
    def get_sound_quality(self, sound_quality):
        self.download_sound_quality_Label.setText(sound_quality)

    @Slot(str)
    def get_length(self, length):
        if length == "0":
            self.disable_right_tab()
            try:
                if self.download_Thread.isRunning() is True:
                    self.status_Pixmap.load(download_icon_x16)
                    self.status_Icon.setPixmap(self.status_Pixmap)
                    self.status_Message.setText("İndiriliyor...")
                else:
                    self.status_Pixmap.load(search_icon_x16)
                    self.status_Icon.setPixmap(self.status_Pixmap)
                    self.status_Message.setText("Video bekleniyor...")
            except AttributeError:
                self.status_Pixmap.load(search_icon_x16)
                self.status_Icon.setPixmap(self.status_Pixmap)
                self.status_Message.setText("Video bekleniyor...")
        else:
            if int(length) > 3599:
                if int(strftime('%M', gmtime(int(length)))) == 0 and int(strftime('%S', gmtime(int(length)))) == 0:
                    self.info_length_Label.setText(strftime('X%H Saat', gmtime(int(length))).replace('X0', 'X').replace('X', ''))
                elif int(strftime('%M', gmtime(int(length)))) == 0:
                    self.info_length_Label.setText(strftime('X%H Saat X%S Saniye', gmtime(int(length))).replace('X0', 'X').replace('X', ''))
                elif int(strftime('%S', gmtime(int(length)))) == 0:
                    self.info_length_Label.setText(strftime('X%H Saat X%M Dakika', gmtime(int(length))).replace('X0', 'X').replace('X', ''))
                else:
                    self.info_length_Label.setText(strftime('X%H Saat X%M Dakika X%S Saniye', gmtime(int(length))).replace('X0', 'X').replace('X', ''))
            elif int(length) > 59:
                if int(strftime('%S', gmtime(int(length)))) == 0:
                    self.info_length_Label.setText(
                        strftime('X%M Dakika', gmtime(int(length))).replace('X0', 'X').replace('X', ''))
                else:
                    self.info_length_Label.setText(strftime('X%M Dakika X%S Saniye', gmtime(int(length))).replace('X0', 'X').replace('X', ''))
            else:
                self.info_length_Label.setText(strftime('X%S Saniye', gmtime(int(length))).replace('X0', 'X').replace('X', ''))
            self.download_history()
            self.right_Tab.setEnabled(True)
            try:
                if self.download_Thread.isRunning() is True:
                    self.status_Pixmap.load(download_icon_x16)
                    self.status_Icon.setPixmap(self.status_Pixmap)
                    self.status_Message.setText("İndiriliyor...")
                else:
                    self.status_Pixmap.load(download_icon_x16)
                    self.status_Icon.setPixmap(self.status_Pixmap)
                    self.status_Message.setText("İndirme bekleniyor...")
            except AttributeError:
                self.status_Pixmap.load(download_icon_x16)
                self.status_Icon.setPixmap(self.status_Pixmap)
                self.status_Message.setText("İndirme bekleniyor...")

    def download_history(self):
        self.download_history_Label.clear()
        dir_name = '.\\downloads\\'
        list_of_files = filter(path.isfile,
                               glob.glob(dir_name + '/**/*'))
        list_of_files = sorted(list_of_files,
                               key=path.getmtime)
        for file_name in list_of_files:
            file_name = path.basename(file_name)
            self.download_history_Label.insertPlainText("• " + file_name + "\n")

    def closeEvent(self, event: QCloseEvent):
        self.close_MessageBox = QMessageBox()
        self.close_MessageBox.setWindowTitle("Kapat")
        self.close_MessageBox.setWindowIcon(QIcon(close_icon_x16))
        self.close_MessageBox.setIcon(QMessageBox.Question)
        self.close_MessageBox.setText("Programı kapatmak istediğine emin misin?")
        self.close_MessageBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.close_MessageBox_Yes = self.close_MessageBox.button(QMessageBox.Yes)
        self.close_MessageBox_Yes.setText("Evet")
        self.close_MessageBox_No = self.close_MessageBox.button(QMessageBox.No)
        self.close_MessageBox_No.setText("Hayır")
        self.close_MessageBox.setDefaultButton(QMessageBox.No)

        self.close_deny_MessageBox = QMessageBox()
        self.close_deny_MessageBox.setWindowTitle("Kapat")
        self.close_deny_MessageBox.setWindowIcon(QIcon(close_icon_x16))
        self.close_deny_MessageBox.setIcon(QMessageBox.Information)
        self.close_deny_MessageBox.setText("İndirme işlemi devam ederken program kapatılamaz.")
        self.close_deny_MessageBox.setStandardButtons(QMessageBox.Ok)
        self.close_deny_Ok = self.close_deny_MessageBox.button(QMessageBox.Ok)
        self.close_deny_Ok.setText("Tamam")
        self.close_deny_MessageBox.setDefaultButton(QMessageBox.Ok)

        try:
            if self.download_Thread.isRunning() is True:
                self.close_deny_MessageBox.exec()
                event.ignore()
            else:
                reply = self.close_MessageBox.exec()
                if reply == QMessageBox.Yes:
                    self.browser_WebView.history().clear()
                    for f in listdir('.\\downloads\\download_cache'):
                        remove(path.join('.\\downloads\\download_cache', f))
                else:
                    event.ignore()
        except AttributeError:
            reply = self.close_MessageBox.exec()
            if reply == QMessageBox.Yes:
                self.browser_WebView.history().clear()
                if path.isdir('new_folder'):
                    for f in listdir('.\\downloads\\download_cache'):
                        remove(path.join('.\\downloads\\download_cache', f))
                else:
                    pass
            else:
                event.ignore()


if __name__ == '__main__':
    application = QApplication(sys.argv)
    yip = YIP()
    sys.exit(application.exec())