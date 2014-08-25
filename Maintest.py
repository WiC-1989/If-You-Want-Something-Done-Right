
import threading
from threading import Thread
import time
import queue

import tkinter
from tkinter import *
from tkinter import tix
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk

import mutagenx.id3 
from mutagenx.mp3 import MP3
from mutagenx.easyid3 import EasyID3
from mutagenx.id3 import ID3, APIC, error

import os

##################
#Global Variables#
##################

mw_w = 1006     #The Main window's defined width (width size)
mw_h = 462      #The Main window's defined height (height size)
sw_w = 450      #Suggestion window's defined width (width size)
sw_h = 332      #Suggestion window's defined height (height size)
ww_w = 325      #Warning window's defined width (width size) - Illegal character(s)
ww_h = 125       #Warning window's defined height (height size) - Illegal character(s)
in_w = 325      #Invalid name's defined width (width size) - Empty file name
in_h = 125       #Invalid name's defined height (height size) - Empty file name

phaa = "100placeholder.jpg"#Placeholder album art image
imaaa = "addalbumart.jpg"#Add album art button image
imsd = "seldir.jpg"#Select diretory button image
imdb = "dirback.jpg"#Select previous directory button image
ims = "suggest.jpg"#Enable suggestion functionality button image
ima = "apply.jpg"#Apply suggestions to selected button image
imal = "applyall.jpg"#Apply suggestions to all button image
xico = "X.jpg"#Blue X symbol used or cw_ww, and cw_in warning pop-ups

ILLEGAL_CHARACTERS = """
#\/:*?"<>|. are potentially illegal
characters and will not be included
in Filename Generator!
"""
EMPTY_FILE_NAME = """
Cannot select an empty filename!

"""

def main():
    root = tix.Tk()
    root['bg']="pink"
    root.minsize(mw_w, mw_h)
    root.maxsize(mw_w, mw_h)
    app = App(root)
    root.update()
    root.mainloop()
    

class App(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master, background= 'azure')
        self.master = master
        self.bind("<Configure>", self.on_resize)
        ####################
        #App-wide variables#
        ####################
    
        #App operation variables
        self.mp3fileinfocus=""#File in focus (path included!)
        self.workingsongid=""#Filename in focus (path not included!)
        self.nextID=""#ID of next element in dirdisplay
        self.dirliststart="C:\\"#Where to store selected directory chosen by seldir button, to be used by dirlist and others
        self.prevdir=""#Stores the immediately previous directory used by dirlist, for dirback button
        self.refreshpos=0#Stores the position of the present song incase it refreshes
        #Thread variables
        self.lock=threading.Lock()
        self.queue=queue.Queue()#Used to determine if scanner threads complete
        self.suggestions=queue.Queue()#Stores suggestions found by all scanner threads
        self.makesuggestions=BooleanVar()#Determines if user wants suggestion functionality operating
        self.working_directory=""#Current directory for scan threads to work
        #Statusbar variables
        self.s_timetotal=0#Total length of MP3 files shown in dirdisplay
        self.s_sizetotal=0#Total size of MP3 files shown in dirdisplay
        self.s_timecurrent=0#Length of currently selected MP3 file
        self.s_sizecurrent=0#Size of currently selected MP3 file
        
        #############################################################################
        #Widget initial creation and options (init_UI covers grid and other options)#
        #############################################################################
        
        #######
        #Menus#
        #######
        
        #File Menu
        self.filebutton = Menubutton(self, text="File", background="steel blue", foreground='azure', relief=RAISED)
        self.filemenu = Menu(self.filebutton, tearoff=0)
        
        #######################################
        #Directory List - Left pane, 'dirlist'#
        #######################################
        
        self.dirlist = tix.DirList(self, value=self.dirliststart, command=self.populate_table, scrollbar=BOTH)
        
        ##############################################
        #Directory Display - Right pane, 'dirdisplay'#
        ##############################################
        
        self.dirdisplay = ttk.Treeview(self, selectmode= 'browse', columns= ('File Name', 'Artist', 'Song Title', 'Album', 'path'), displaycolumns=('File Name', 'Artist', 'Song Title', 'Album'))
        self.dirdisplay.bind("<<TreeviewSelect>>", self.display_chosen)
        
        #xsb and ysb scrollbars for 'dirdisplay'
        self.xsb = ttk.Scrollbar(self, orient='horizontal', command= self.dirdisplay.xview)
        self.ysb = ttk.Scrollbar(self, orient='vertical', command= self.dirdisplay.yview)
        
        ####################
        #Filename Generator#
        ####################
        
        #Foundation
        self.nameframe=Label(self, background='light sky blue', relief=RAISED)
        #Section title
        self.ngs_tit = Label(self.nameframe, text='Filename Generator', background='steel blue', foreground='azure', relief=RAISED)
        #Row identifiers (labels)
        self.fr_lab = Label(self.nameframe, text='1st', background='steel blue', relief=RAISED)
        self.sr_lab = Label(self.nameframe, text='2nd', background='azure', relief=RAISED)
        self.tr_lab = Label(self.nameframe, text='3rd', background='steel blue', relief=RAISED)
        #Radio buttons
        self.fn_one=StringVar()#1st part of filename
        self.fn_one.trace("w", self.display_selection)
        self.fn_two=StringVar()#2nd part of filename
        self.fn_two.trace("w", self.display_selection)
        self.fn_thr=StringVar()#3rd part of filename
        self.fn_thr.trace("w", self.display_selection)
        self.fr_none=Radiobutton(self.nameframe, text="x", variable=self.fn_one, value="None")
        self.fr_title=Radiobutton(self.nameframe, text="Title", variable=self.fn_one, value="Title")
        self.fr_artist=Radiobutton(self.nameframe, text="Artist", variable=self.fn_one, value="Artist")
        self.fr_album=Radiobutton(self.nameframe, text="Album", variable=self.fn_one, value="Album")
        self.sr_none=Radiobutton(self.nameframe, text="x", variable=self.fn_two, value="None")
        self.sr_title=Radiobutton(self.nameframe, text="Title", variable=self.fn_two, value="Title")
        self.sr_artist=Radiobutton(self.nameframe, text="Artist", variable=self.fn_two, value="Artist")
        self.sr_album=Radiobutton(self.nameframe, text="Album", variable=self.fn_two, value="Album")
        self.tr_none=Radiobutton(self.nameframe, text="x", variable=self.fn_thr, value="None")
        self.tr_title=Radiobutton(self.nameframe, text="Title", variable=self.fn_thr, value="Title")
        self.tr_artist=Radiobutton(self.nameframe, text="Artist", variable=self.fn_thr, value="Artist")
        self.tr_album=Radiobutton(self.nameframe, text="Album", variable=self.fn_thr, value="Album")
        #Apply selection button (selection of file name makeup)
        self.asel = Button(self.nameframe, text='Apply', command=self.apply_selection)
        #Entry to show results of selections
        self.s_sel=""
        self.e_sel = Entry(self.nameframe, textvariable=self.s_sel)
        
        ##########################
        #Tag Editor w/ Suggestion#
        ##########################
        
        #Foundation
        self.tagframe=Label(self, background='light sky blue', relief=RAISED)
        #Section Title
        self.te_tit = Label(self.tagframe, text='Tag Editor', background='steel blue', foreground='azure', relief=RAISED)
        #Labels beside entries
        self.l_title=Label(self.tagframe, text='Title', background='steel blue', foreground='white', relief=RAISED)
        self.l_artist=Label(self.tagframe, text='Artist', background='azure', foreground='black', relief=RAISED)
        self.l_album=Label(self.tagframe, text='Album', background='steel blue', foreground='white', relief=RAISED)
        #Entries for users to edit tag data (fields)/Bind them to <return> and strings
        self.s_title=""
        self.s_artist=""
        self.s_album=""
        self.t_title=Entry(self.tagframe, textvariable=self.s_title)
        self.t_artist=Entry(self.tagframe, textvariable=self.s_artist)
        self.t_album=Entry(self.tagframe, textvariable=self.s_album)
        #Binds of '<Return>' to jump to next field. Must also link to threads. mode=(0=title, 1=artist, 2=album)
        self.t_title.bind("<Return>", lambda event: self.scannerthreadgen(event, 0))
        self.t_artist.bind("<Return>", lambda event: self.scannerthreadgen(event, 1))
        self.t_album.bind("<Return>", lambda event: self.scannerthreadgen(event, 2))
        #Suggest On button 
        self.sugb=Checkbutton(self.tagframe, text='Suggest On', variable=self.makesuggestions)
        #Suggestions (#) button 
        self.ss_image = Image.open(ims)
        self.ss_bimage = ImageTk.PhotoImage(self.ss_image)
        self.showsuggest=Button(self.tagframe, text='Suggestions (0)', command=self.showsuggested, image=self.ss_bimage, compound='left')
        
        ##########################
        #Images for cw_sg buttons#
        ##########################
        
        #Image for Apply Selected Suggestions Button
        self.ima_image = Image.open(ima)
        self.ima_bimage = ImageTk.PhotoImage(self.ima_image)
        #Image for Apply all Suggestions Button
        self.imal_image = Image.open(imal)
        self.imal_bimage = ImageTk.PhotoImage(self.imal_image)
        
        ###############################################
        #Button Toolbar - above dirlist and dirdisplay#
        ###############################################
        
        #Button panel foundation above dirlist and dirdisplay
        self.bpframe = Label(self, background='white', relief=RAISED)
        #Previous directory button (back)
        self.db_image = Image.open(imdb)
        self.db_bimage = ImageTk.PhotoImage(self.db_image)
        self.dirback = Button(self.bpframe, command= self.prevdirset, image=self.db_bimage)
        #Select directory button
        self.sdb_image = Image.open(imsd)
        self.sdb_bimage = ImageTk.PhotoImage(self.sdb_image)
        self.seldir = Button(self.bpframe, command= self.seldirdia, image=self.sdb_bimage)
        
        ###################
        #Album Art Section#
        ###################
        
        #Foundation
        self.aa_found = Label(self, background='steel blue')
        
        #Album Art slot
        self.ph_image = Image.open(phaa)
        self.albumartpic = ImageTk.PhotoImage(self.ph_image)
        self.albumartslot = ttk.Label(self.aa_found, image=self.albumartpic, background="blue", relief=RAISED)
        #Add Album Art Button
        self.aaab_image = Image.open(imaaa)
        self.aaab_bimage = ImageTk.PhotoImage(self.aaab_image)
        self.addalbumart = Button(self.aa_found, command=self.add_albumart, background="light blue", image=self.aaab_bimage, compound='left')
        
        ##################################################
        #Buffers and Spacers for GUI Placement of Widgets#
        ##################################################
        
        #Spacer/placeholder between 'dirlist' and 'dirdisplay'
        self.tagdataarea = Frame(self, background="light sky blue")
        self.filenamelab = Label(self, text="File Name", background="steel blue", foreground="steel blue", relief=RAISED)
        #Spacer/placeholder above status bar
        self.blab = Label(self, text="", background="light sky blue", relief=RAISED)
        #Blue X image used for empty filename and illegal character popups
        self.ic_img = Image.open(xico)
        self.ic_image = ImageTk.PhotoImage(self.ic_img)
        
        ############
        #Status Bar#
        ############
        
        #Foundation
        self.statusbar = Frame(self, background="snow2")
        #Status bar item buffer (to line up with 'dirdisplay'
        self.timecurrent = Label(self.statusbar, text='000:00:00', background='azure', relief=RAISED)
        #Status bar items
        self.timetotal = Label(self.statusbar, text='000:00:00', background='steel blue', relief=RAISED)
        self.sizecurrent = Label(self.statusbar, text='000 GB ', background='azure', relief=RAISED)
        self.sizetotal = Label(self.statusbar, text='000 GB ', background='steel blue', relief=RAISED)
        self.statusbuffer = Label(self.statusbar, text='############################', background='snow2', foreground='snow2')
        
        #####################
        #Run setup functions#
        #####################
        
        self.center()
        self.init_UI()
        self.init_filemenu()
        self.init_dirlist()
        self.init_dirdisplay(self.dirdisplay)
        self.disablealbumartbutton()
        self.disableentries()
        self.disable_button(self.showsuggest)
        self.disable_FG()
        
#######################        
#Application Functions#      
#######################        
        
    def init_UI(self):#Initializes things like grid and title, ensures cells for grid expand correctly
        ##############
        #Program-wide#
        ##############
        self.master.title("If You Want Something Done Right...")
        self.grid(sticky=N+S+E+W)
        
        #######
        #Menus#
        #######
        #File Menu
        self.filebutton.grid(row=0, column=0, sticky=NW)
        self.filebutton.config(activebackground='azure', activeforeground='black')
        #######################################
        #Directory List - Left pane, 'dirlist'#
        #######################################
        self.dirlist.grid(row=7, column=0, rowspan=24, columnspan=3, sticky=NSEW)
        
        ##############################################
        #Directory Display - Right pane, 'dirdisplay'#
        ##############################################
        self.dirdisplay.grid(row=7, column=6, rowspan=23, columnspan=9, pady=0.1, sticky=NSEW)
        
        #xsb and ysb scrollbars for 'dirdisplay'
        self.xsb.grid(row=30, column=6, columnspan=9, sticky=EW)
        self.ysb.grid(row=7, column=15, rowspan=23, padx=1, pady=2, sticky=NS)
        
        ####################
        #Filename Generator#
        ####################
        #Foundation
        self.nameframe.grid(row=1, column=0, rowspan=5, columnspan=6, sticky=N+E+W+S)
        #Section title
        self.ngs_tit.grid(row=0, column=0, columnspan=6, sticky=N+E+W+S)
        #Row Identifiers (labels)
        self.fr_lab.grid(row=2, column=0, sticky=N+E+W+S)
        self.sr_lab.grid(row=3, column=0, sticky=N+E+W+S)
        self.tr_lab.grid(row=4, column=0, sticky=N+E+W+S)
        #Radio buttons
        self.fr_none.grid(row=2, column=1)
        self.fr_none.config(background='steel blue', foreground='azure', selectcolor='light sky blue', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        self.fr_none.select()#None is default selected
        self.fr_title.grid(row=2, column=2)
        self.fr_title.config(background='steel blue', foreground='azure', selectcolor='light sky blue', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        self.fr_artist.grid(row=2, column=3)
        self.fr_artist.config(background='steel blue', foreground='azure', selectcolor='light sky blue', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        self.fr_album.grid(row=2, column=4)
        self.fr_album.config(background='steel blue', foreground='azure', selectcolor='light sky blue', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        self.sr_none.grid(row=3, column=1)
        self.sr_none.config(background='azure', foreground='black', selectcolor='white', relief=RAISED, activebackground='steel blue', activeforeground='azure')
        self.sr_none.select()#None is default selected
        self.sr_title.grid(row=3, column=2)
        self.sr_title.config(background='azure', foreground='black', selectcolor='white', relief=RAISED, activebackground='steel blue', activeforeground='azure')
        self.sr_artist.grid(row=3, column=3)
        self.sr_artist.config(background='azure', foreground='black', selectcolor='white', relief=RAISED, activebackground='steel blue', activeforeground='azure')
        self.sr_album.grid(row=3, column=4)
        self.sr_album.config(background='azure', foreground='black', selectcolor='white', relief=RAISED, activebackground='steel blue', activeforeground='azure')
        self.tr_none.grid(row=4, column=1)
        self.tr_none.config(background='steel blue', foreground='azure', selectcolor='light sky blue', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        self.tr_none.select()#None is default selected
        self.tr_title.grid(row=4, column=2)
        self.tr_title.config(background='steel blue', foreground='azure', selectcolor='light sky blue', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        self.tr_artist.grid(row=4, column=3)
        self.tr_artist.config(background='steel blue', foreground='azure', selectcolor='light sky blue', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        self.tr_album.grid(row=4, column=4)
        self.tr_album.config(background='steel blue', foreground='azure', selectcolor='light sky blue', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        #Apply selection button
        self.asel.grid(row=5, column=4, sticky=N+E+W)
        self.asel.config(anchor='ne', background='steel blue', foreground='azure', relief=RAISED, activebackground='azure', activeforeground='steel blue')
        #Entry to show results of selections
        self.e_sel.grid(row=5, column=0, columnspan=5, sticky=N+W+S)
        self.e_sel.config(width=30, disabledbackground='light sky blue')

        ##########################
        #Tag Editor w/ Suggestion#
        ##########################
        #Foundation
        self.tagframe.grid(row=1, column=7, rowspan=5, sticky=NW)
        #Section title
        self.te_tit.grid(row=0, column=0, columnspan=9, sticky=N+E+W+S)
        #Labels beside entries
        self.l_title.grid(row=1, column=0, columnspan=3, sticky=N+E+W+S)
        self.l_artist.grid(row=2, column=0, columnspan=3, sticky=N+E+W+S)
        self.l_album.grid(row=3, column=0, columnspan=3, sticky=N+E+W+S)
        #Entries for users to edit tag data (fields)
        self.t_title.grid(row=1, column=3, columnspan=6, sticky=N+E+W+S)
        self.t_title.config(width=40, disabledbackground='steel blue', selectbackground='steel blue', selectforeground='azure')
        self.t_artist.grid(row=2, column=3, columnspan=6, sticky=N+E+W+S)
        self.t_artist.config(width=40, disabledbackground='azure', selectbackground='steel blue', selectforeground='azure')
        self.t_album.grid(row=3, column=3, columnspan=6, sticky=N+E+W+S)
        self.t_album.config(width=40, disabledbackground='steel blue', selectbackground='steel blue', selectforeground='azure')
        #Suggest On button
        self.sugb.grid(row=4, column=0, sticky=SW)
        self.sugb.config(background = 'light sky blue', foreground='azure', selectcolor='steel blue', activebackground='steel blue', activeforeground='light sky blue', relief=RAISED)
        #Suggestions (#) button
        self.showsuggest.grid(row=4, column=8, sticky=SE)
        self.showsuggest.config(background = 'azure', foreground='steel blue', activebackground='steel blue', activeforeground='azure', relief=RAISED)
        
        ###############################################
        #Button Toolbar - above dirlist and dirdisplay#
        ###############################################
        #Button panel foundation above dirlist and dirdisplay
        self.bpframe.grid(row=6, column=0, columnspan=16, rowspan=1, sticky=EW)
        #Previous directory button (back)
        self.dirback.grid(row=6, column=0, sticky=N+W)
        #Select directory button
        self.seldir.grid(row=6, column=1, sticky=N)
            
        ###################
        #Album Art Section#
        ###################
        #Foundation
        self.aa_found.grid(row=1, column=13, rowspan=5, sticky=NW)
        #Album art slot
        #self.albumartslot.grid(row=1, column=13, rowspan=5, sticky=NW)
        self.albumartslot.grid(row=0, column=0, sticky=N+E+W+S)
        #Add album art button
        #self.addalbumart.grid(row=5, column=13, sticky=NW)
        self.addalbumart.grid(row=0, column=0, sticky=SW)
        
        ##################################################
        #Buffers and Spacers for GUI Placement of Widgets#
        ##################################################
        #Spacer/placeholder between 'dirlist' and 'dirdisplay'
        self.tagdataarea.grid(row=7, column=3, rowspan=24, columnspan=3, sticky=N+E+W+S)
        self.filenamelab.grid(row=7, column=3, rowspan=24, columnspan=3, sticky=N+E+W+S)
        #Spacer/placeholder above status bar
        self.blab.grid(row=31, column=0, columnspan=16, sticky=EW)
        
        ############
        #Status Bar#
        ############
        #Foundation   
        self.statusbar.grid(row=32, column=0, columnspan=16, rowspan=1, sticky=EW)
        #Status bar item buffer (to line up with 'dirdisplay'
        self.statusbuffer.grid(row=32, column=0, sticky=EW)
        #Status bar items
        self.timecurrent.grid(row=32, column=5, sticky=EW)
        self.timetotal.grid(row=32, column=6, sticky=EW)
        self.sizecurrent.grid(row=32, column=7, sticky=EW)
        self.sizetotal.grid(row=32, column=8, sticky=EW)
        
        
    def center(self):#Finds out dimensions of user screen and places application in center
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        mwl_x = (screen_width - mw_w)/2
        mwl_y = (screen_height - mw_h)/2
        self.master.geometry("%dx%d+%d+%d" % (mw_w,mw_h,mwl_x,mwl_y))
        
    def center_cw(self, child_window, width, height):#Used to center any child window of main
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        cwl_x = (screen_width - width)/2
        cwl_y = (screen_height - height)/2
        child_window.geometry("%dx%d+%d+%d" % (width,height,cwl_x,cwl_y))        
        
    def on_resize(self, event):#Called when application window is resized
        userheight=self.winfo_height()
        userwidth=self.winfo_width()
        print(userheight)
        print(userwidth)
        
            
    def disable_button(self, buttontodisable):#Disable the given button
        try:
            buttontodisable.config(state=DISABLED)
        except AttributeError:
            pass
        
    def enable_button(self, buttontoenable):#Enable the given button
        try:
            buttontoenable.config(state=NORMAL)
        except AttributeError:
            pass

    def detect_illegal(self, value, deletechars):#Removes characters specified in second string from first string, returns 1 if none found, new string if some found
        originalvalue=value
        for c in deletechars:#For each banned character, replace any found characters with blank
            value = value.replace(c,'')
        if(originalvalue == value):
            return 1#The original value was perfectly fine
        else:
            return value#The original value contained illegal characters, created a replacement

    def ph(self,event):#Placeholder function that does nothing
        pass
    
    def refresh_file(self):#Used when tag data was changed or album art added/replaced
        
        directorynfile = self.mp3fileinfocus
        file= os.path.basename(directorynfile)
        directory=os.path.dirname(directorynfile)
        #print('refresh')
        #print(self.refreshpos)
        #Take the MP3 and turn it into an easyMP3 object to work with
        fileasmp3= self.mp3easygen(directorynfile)
        #Values populates 'dirdisplay' using functions and variables for filename, title, artist, album plus a (hidden) path to file
        try:
            self.dirdisplay.delete(file)#Delete the old entry(what you just edited)
        except TclError:#If refreshed due to filerename, you have nothing to delete 
            pass
        self.dirdisplay.insert('', self.refreshpos, file, text=file, values=(file, self.get_artist(fileasmp3), self.get_songtitle(fileasmp3), self.get_album(fileasmp3), directory))
        #Album art
        self.clr_albumartslot()#Clear any album art data displayed
        #Take the MP3 and turn it into an MP3id3 object to work with
        mp3ID3rep = self.mp3id3gen(directorynfile)
        tempart= self.get_coverart(mp3ID3rep)
        try:
            pil_image=Image.open(tempart)
            pil_imagesized=pil_image.resize((100,100), Image.ANTIALIAS)
            self.albumartpic = ImageTk.PhotoImage(pil_imagesized)
            self.albumartslot['image']=self.albumartpic
        except FileNotFoundError:
            #print("No album art found")
            self.clr_albumartslot()
    
    def refresh_directory(self):
        self.disablealbumartbutton()#Ensure add album art is disabled
        self.clearentries()#Clear any tag data inside entries
        self.disableentries()#Disable user using entries
        self.clr_albumartslot()#Clear any album art data displayed
        self.clearsuggestions()#Clear suggestion queue so they don't carry over from old directory
        self.clearstatusbar()
        self.disable_FG()
        self.directory_search(self.working_directory)
        #After refresh of directory, set focus back to the song you were working on
        self.dirdisplay.focus_set()#Set input focus (up/down keys) to dirdisplay
        self.dirdisplay.selection_set((self.workingsongid, self.workingsongid))
        self.dirdisplay.focus(self.workingsongid)
    
#######################################################
#Suggestion Functionality and Thread Related Functions#   
#######################################################

    def showsuggested(self):#Creates a child window to display suggestions
        cw_sg = Toplevel(self, background= 'white')#Generate window
        cw_sg.minsize(sw_w,sw_h)
        cw_sg.maxsize(sw_w,sw_h)
        cw_sg.protocol("WM_DELETE_WINDOW", lambda: self.cw_sgdestroy(cw_sg, listbox))#Redefines closing cw_sg
        cw_sg.title('Suggestions')#Add title
        self.center_cw(cw_sg, sw_w, sw_h)#Center the window
        #Enable proper resizing with grid options
        cw_sg.rowconfigure(0, weight=1)
        cw_sg.rowconfigure(1, weight=1)
        cw_sg.columnconfigure(0, weight=1)
        cw_sg.columnconfigure(1, weight=1)
        cw_sg.columnconfigure(2, weight=1)
        
        self.disable_button(self.showsuggest)#Eliminate chance of multiple cw_sgs
        
        #Create buttons beneath listbox
        applyb=Button(cw_sg, text='Apply', command= lambda: self.applytosel(listbox, cw_sg), image=self.ima_bimage, compound='left', relief=RAISED)
        applyb.config(background='azure', foreground='steel blue')
        applyb.grid(row=2, column=0, sticky=NSEW)
        
        applyallb=Button(cw_sg, text=' Apply all', command= lambda: self.applytoall(listbox, cw_sg), image=self.imal_bimage, compound='left', relief=RAISED)
        applyallb.config(background='azure', foreground='steel blue')
        applyallb.grid(row=2, column=1, sticky=NSEW)
        
        #Create listbox and x, y-scrollbars
        cw_sg_xsb = ttk.Scrollbar(cw_sg, orient='horizontal')
        cw_sg_ysb = ttk.Scrollbar(cw_sg, orient='vertical')
        listbox=Listbox(cw_sg, width=71, height=18, background='white', selectmode='extended', yscrollcommand=cw_sg_ysb.set)
        listbox.bind("<<ListboxSelect>>", lambda event: self.marksuggestion(event, listbox))
        cw_sg_xsb.configure(command= listbox.xview)
        cw_sg_ysb.configure(command= listbox.yview)
        listbox.configure(xscroll=cw_sg_xsb.set)
        listbox.grid(row=0, column=0, rowspan=1, columnspan=2, sticky=NSEW)
        cw_sg_xsb.grid(row=1, column=0, rowspan=1, columnspan=2, sticky=EW)
        cw_sg_ysb.grid(row=0, column=2, rowspan=1, sticky=NS)
        
        #Populate listbox
        while(self.suggestions.empty()== False):
            #Don't print since that counts as removing!!
            listbox.insert(END, self.suggestions.get())
            
        if(self.suggestions.empty() == True):
            #print('No more suggestions!')
            self.disable_button(self.showsuggest)
            
    def cw_sgdestroy(self, cw, listbox):#Defines destroying cw_sg to include re-enabling showsuggest button
        if(listbox.size() > 0):#If there are still suggestions, replace in self.suggestions
            for x in range(0, listbox.size()):
                self.suggestions.put(listbox.get(x))
        if(self.suggestions.empty() == False):#If suggestions holds any when you close the window
            self.enable_button(self.showsuggest)
            no_ofsuggestions = str(self.suggestions.qsize())
            newtitle = "Suggestions ("+no_ofsuggestions+")"
            self.showsuggest.config(text=newtitle)
        elif(self.suggestions.empty() == True):#If empty, reset button
            self.showsuggest.config(text='Suggestions (0)')
        cw.destroy()
        
    def marksuggestion(self, event, listbox):#Called when user makes selections
        pass
        
    def scannerthreadgen(self, event, mode):#Creates a Scannerthreadobj and puts in queue
        #mode=(0=title, 1=artist, 2=album)
        if(mode == 0):
            scanwith = self.t_title.get()
            self.tit_to_art(event)
        if(mode == 1):
            scanwith = self.t_artist.get()
            self.art_to_alb(event)
        if(mode == 2):
            scanwith = self.t_album.get()
            self.alb_to_nex(event)
        
        if(self.makesuggestions.get() == True):
            Scannerthreadobj(self.queue, self.suggestions, scanwith, mode, self.working_directory).start()
            self.master.after(100, self.process_queue)
        elif(self.makesuggestions.get() == False):
            pass
            #print("Cannot use", scanwith, 'did not select checkbox!')
            
    def process_queue(self):#Used to process all Scannerthreadobj's scanning what the user has entered in title or album
        try:#This will only work when all threads finish
            msg = self.queue.get(0)
            print(msg)
            self.enable_button(self.showsuggest)#Only allows button to work when all scanners done
            no_ofsuggestions = str(self.suggestions.qsize())
            newtitle = "Suggestions ("+no_ofsuggestions+")"
            self.showsuggest.config(text = newtitle)
            #Show result of the task if needed
        except queue.Empty:#If the queue is empty (IE all threads done), continue
            #print('Job not finished')
            self.master.after(100, self.process_queue)    
    
    def phe(self):
        print('Placeholder pressed')
        
    def applytosel(self, listbox, cw):
        #print('Pressed apply')
        if(listbox.curselection()):#If user selected something
            p=0
            for x in listbox.curselection():#Goes through each item
                self.applychange(listbox.get(x-p))#Sending it to self.applychange
                listbox.delete(listbox.curselection()[x-p])
                p=p+1
        else:#Nothing selected, don't destroy cw_sg
            pass#Do nothing
        self.refresh_directory()
    
    def applytoall(self, listbox, cw):
        #print('Pressed apply to all')
        for x in range(0, listbox.size()):
            self.applychange(listbox.get(x))#Sending it to self.applychange
        listbox.delete(0, END)    
        self.cw_sgdestroy(cw, listbox)
        self.refresh_directory()
        
    def applychange(self, suggestion):#Used by scanner threads, accepts Suggestion
        directorylimit = suggestion.rfind('/')#The index of the last '/' in path
        filenamelimit = suggestion.find('>')#The index of the first '>' after filename
        directory=suggestion[0:directorylimit+1]#Just the directory of Suggestion
        filename=suggestion[directorylimit+1:filenamelimit]#Just the filename of Suggestion
        modelimit = suggestion.rfind('> ')#The index of '> ' for mode start
        changetoapplylimit = suggestion.rfind(': ')#The index where changetoapply starts
        mode=suggestion[modelimit+2:changetoapplylimit-1]
        changetoapply=suggestion[changetoapplylimit+2:len(suggestion)]
        #print('Using', directory+filename, 'for tmp')
        tmp=self.mp3easygen(directory+filename)
        if(mode == 'Title'):#Mode 0, change title
            #print('Mode 0, change title')
            tmp['title'] = changetoapply
        elif(mode == 'Artist'):#Mode 1, change artist
            #print('Mode 1, change artist')
            tmp['artist'] = changetoapply
        elif(mode == 'Album'):#Mode 2, change album
            #print('Mode 2, change album')
            tmp['album'] = changetoapply

        tmp.save(v2_version=3)
        
        
    def clearsuggestions(self):#Used when user exits the working directory
        try:
            with self.suggestions.mutex:
                self.suggestions.queue.clear()#Clear suggestion queue
                self.showsuggest.config(text='Suggestions (0)')#Reset button
        except AttributeError:
            pass
        
        
#####################
#File Menu Functions#    
#####################

    def init_filemenu(self):#Sets up File Menu, Commands for buttons in own section
        self.filemenu.add_command(label="Choose Directory", command=self.seldirdia, underline=0, background='azure', foreground='black')
        self.filemenu.add_command(label="Placeholder1", command=self.ph, underline=0, background='azure', foreground='black')
        self.filemenu.add_command(label="Placeholder2", command=self.ph, underline=0, background='azure', foreground='black')
        self.filemenu.add_command(label="Exit", command=self.quit, underline=1, background='azure', foreground='black')
        self.filebutton.config(menu=self.filemenu)

##########################
#Name Generator Functions#
##########################
    
    def apply_selection(self):#Apply's new filename in format specified by e_sel's data to file self.mp3fileinfocus
        oldfilename=self.mp3fileinfocus
        first=str(self.fn_one.get())#1st segment of new filename
        second=str(self.fn_two.get())#2nd segment of new filename
        third=str(self.fn_thr.get())#3rd segment of new filename
        #print(first+' - '+second+' - '+third+'.mp3')
        mptree = self.mp3easygen(self.mp3fileinfocus)
        #First segment
        p1=""
        p2=""
        p3=""
        if(first == "Title"):#If first component should be Title
            p1=self.get_songtitle(mptree)
            print("p1=", p1)
        elif(first == "Artist"):#If first component should be Artist
            p1=self.get_artist(mptree)
            print("p1=", p1)
        elif(first == "Album"):#If first component should be Album
            p1=self.get_album(mptree)
            print("p1=", p1)
        elif(first == "None"):#User doesnt need a first component
            pass
        if(second == "Title"):#If second component should be Title
            p2=self.get_songtitle(mptree)
            print("p2=", p2)
        elif(second == "Artist"):#If second component should be Artist
            p2=self.get_artist(mptree)
            print("p2=", p2)
        elif(second == "Album"):#If second component should be Album
            p2=self.get_album(mptree)
            print("p2=", p2)
        elif(second == "None"):#User doesnt need a second component
            pass
        if(third == "Title"):#If third component should be Title
            p3=self.get_songtitle(mptree)
            print("p3=", p3)
        elif(third == "Artist"):#If third component should be Artist
            p3=self.get_artist(mptree)
            print("p3=", p3)
        elif(third == "Album"):#If third component should be Album
            p3=self.get_album(mptree)
            print("p3=", p3)
        elif(third == "None"):#User doesnt need a third component
            pass
        #Generate filename
        #First '-'
        if((p1 != "" and p2 != "") or (p1 != "" and p3 != "")):
            p1 = p1+' - '
        #Second '-'
        if(p2 != "" and p3 != ""):
            p2 = p2+' - '
        if(p1 != "" or p2 !="" or p3 !=""):
            newname=p1+p2+p3+'.mp3'
        else:
            newname=".mp3"
        #print('Unvalidated')
        #print(newname)
        #Screen for illegal characters
        cleanname=self.detect_illegal(newname, '#\/:*?"<>|')
        if(cleanname==1):#There is no difference between newname and cleanname.
            pass#Continue
        else:#The new filename contained potentially illegal characters
            #Use the cleaned name to continue
            newname=cleanname
        #Ensure the filename isn't just dashes and filetype
        testname=newname.replace(" - ","")
        testname=testname.replace(".mp3","")
        if(testname != ""):#If the clean testname isn't just dashes and .mp3 write
            #print('I will write this=', newname)
            #print(self.mp3fileinfocus)
            reWrite=self.working_directory+"/"+newname
            #print(reWrite)
            os.rename(self.mp3fileinfocus, reWrite)
            self.mp3fileinfocus=reWrite
            self.dirdisplay.delete(os.path.basename(oldfilename))#Delete the old entry in dirdisplay
            self.refresh_file()
        else:#Fail, create warning window cw_in(child window invalid name)
            #print('I cannot write=', newname)
            self.genww_efn()
    
    def genww_efn(self):#Generate a pop-up that notifies user about empty filename
        cw_in = Toplevel(self, background='white')
        cw_in.focus_set()
        cw_in.bind("<Return>", lambda event: self.cw_inclose(cw_in))
        cw_in.minsize(in_w,in_h)
        cw_in.maxsize(in_w,in_h)
        cw_in.protocol("WM_DELETE_WINDOW", lambda: self.cw_inclose(cw_in))
        cw_in.title('Alert')
        self.center_cw(cw_in, in_w, in_h)#Center the window
        cw_in.grab_set()#When popup appears, disable interaction with root window
        cw_in.rowconfigure(0, weight=1)
        cw_in.rowconfigure(1, weight=1)
        cw_in.rowconfigure(2, weight=1)
        cw_in.columnconfigure(0, weight=1)
        #Elements of cw_in window, made them self. so they persist
        img_slot = ttk.Label(cw_in, image=self.ic_image, background="white")
        img_slot.grid(row=0, column=0, sticky=W)
        cw_in_mess = Label(cw_in, text=EMPTY_FILE_NAME, background="white", foreground="light sky blue", anchor=W, justify=LEFT, font=14)
        cw_in_mess.grid(row=0, column=1)
        cw_in_buf= Label(cw_in, background="white")
        cw_in_buf.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        cw_in_okay = Button(cw_in, text='OK', command= lambda: self.cw_inclose(cw_in))
        cw_in_okay.config(background='light sky blue', foreground='white')
        cw_in_okay.grid(row=2, column=0, columnspan=2, sticky=NS)    
            
    def display_selection(self, *args):#Each time a user changes the selection, this changes contents of self.e_sel
        first=str(self.fn_one.get())
        second=str(self.fn_two.get())
        third=str(self.fn_thr.get())
        #Clear old data in Filename entry
        self.e_sel.delete(0, END)
        #Generate filename and determine '-'s to use
        #First '-'
        if(first == "None"):
            first=""
        if(second == "None"):
            second=""
        if(third == "None"):
            third=""
        if((first != "" and second != "") or (first != "" and third != "")):
            first = first+' - '
        #Second '-'
        if(second != "" and third != ""):
            second = second+' - '
        if(first != "" or second !="" or third !=""):
            nametoplace=first+second+third+'.mp3'
        else:
            nametoplace=".mp3"
        #Place generated filename in Filename entry
        self.e_sel.insert(0, nametoplace)
        
    def disable_FG(self):
        try:
            #Disable radio buttons
            self.fr_none.config(state=DISABLED)
            self.fr_none.deselect()
            self.fr_title.config(state=DISABLED)
            self.fr_title.deselect()
            self.fr_artist.config(state=DISABLED)
            self.fr_artist.deselect()
            self.fr_album.config(state=DISABLED)
            self.fr_album.deselect()
            self.sr_none.config(state=DISABLED)
            self.sr_none.deselect()
            self.sr_title.config(state=DISABLED)
            self.sr_title.deselect()
            self.sr_artist.config(state=DISABLED)
            self.sr_artist.deselect()
            self.sr_album.config(state=DISABLED)
            self.sr_album.deselect()
            self.tr_none.config(state=DISABLED)
            self.tr_none.deselect()
            self.tr_title.config(state=DISABLED)
            self.tr_title.deselect()
            self.tr_artist.config(state=DISABLED)
            self.tr_artist.deselect()
            self.tr_album.config(state=DISABLED)
            self.tr_album.deselect()
            #Disable 'Apply' button
            self.asel.config(state=DISABLED)
            #Disable then clear Filename entry
            self.e_sel.delete(0, END)
            self.e_sel.config(state=DISABLED)
            
        except AttributeError:
            pass
        
    def enable_FG(self):
        try:
            #Enable radio buttons
            self.fr_none.config(state=NORMAL)
            self.fr_none.select()
            self.fr_title.config(state=NORMAL)
            self.fr_artist.config(state=NORMAL)
            self.fr_album.config(state=NORMAL)
            self.sr_none.config(state=NORMAL)
            self.sr_none.select()
            self.sr_title.config(state=NORMAL)
            self.sr_artist.config(state=NORMAL)
            self.sr_album.config(state=NORMAL)
            self.tr_none.config(state=NORMAL)
            self.tr_none.select()
            self.tr_title.config(state=NORMAL)
            self.tr_artist.config(state=NORMAL)
            self.tr_album.config(state=NORMAL)
            #Enable 'Apply' button
            self.asel.config(state=NORMAL)
            #Enable Filename entry
            self.e_sel.config(state=NORMAL)
            #Clear any previous data in Filename entry
            self.e_sel.delete(0, END)
            #Run display_selection once on empty entry field
            self.display_selection()
        except AttributeError:
            pass
        
    def cw_inclose(self, win2close):#Close window, return ability to interact with root window
        win2close.grab_release()
        win2close.destroy()

######################################
#Directory Selection Button Functions#
######################################

    def seldirdia(self):#Generates askdirectory() dialogue, stores directory in dirname
        self.prevdir = str(self.dirlist.cget('value'))#Current directory into prevdir
        dirname = filedialog.askdirectory()#Ask user for directory, if cancelled, dirname = ""
        if(dirname != ""):#If user chose a directory, change it
            self.dirliststart = dirname
            self.dirlist.configure(value=self.dirliststart)
        else:#If the user somehow chose nothing
            pass
        
#####################################
#Previous Directory Button Functions#
#####################################
    
    def prevdirset(self):#Tries to go back to previous directory if possible
        if(self.prevdir != ""):
            godir = self.prevdir#The directory to set dirlist to is self.prevdir
            self.prevdir = str(self.dirlist.cget('value'))#Set current directory to self.prevdir incase you wanna go back to that
            self.dirliststart = godir
            self.dirlist.configure(value=self.dirliststart)
        else:
            pass

##########################
#Album Art Slot Functions#
##########################

    def init_albumartslot(self):#Sets up Album art slot
        pass
    
    def disablealbumartbutton(self):
        try:
            self.addalbumart.config(state=DISABLED)
        except AttributeError:
            pass
        
    def enablealbumartbutton(self):
        try:
            self.addalbumart.config(state=NORMAL)
        except AttributeError:
            pass
    
    def clr_albumartslot(self):#Clears Album art slot to default
        try:
            self.albumartpic = ImageTk.PhotoImage(self.ph_image)
            self.albumartslot['image']=self.albumartpic
        except AttributeError:#Sometimes it says that ph_image doesnt exist inside App
            pass
        
    def add_albumart(self):#Used to add album art to selected file, mp3fileinfocus when button pressed
        #Get image from dialog to add to mp3
        pictoadd = filedialog.askopenfilename(filetypes=(("JPEG files", "*.jpg"),
                                                          ("JPEG files","*.jpeg"),
                                                          ("JPEG files", "*.jpe"),
                                                          ("GIF files", "*.gif"),
                                                          ("PNG files", "*.png"),
                                                          ("BMP files", "*.bmp") 
                                                          ))
        #Determine which of the allowed image types the image is
        img=self.imgtypedeterminator(pictoadd)
        
        if(img == -1):#Error with the file chosen somehow
            print('How did you manage this?')
        else:#add the album art
            self.addreplacealbumart(self.mp3fileinfocus, pictoadd, img)
        
        #Refresh mp3 in dirlist and album art
        self.refresh_file()
        
    def imgtypedeterminator(self, img):#Accepts an image filename (path included) and outputs appropriate mime label based on image type, -1 if uncovered type was found
        #Acceptable types are .jpg, .jpeg, .jpe, .gif, .png, .bmp
        if(img.endswith('.jpg') or img.endswith('.jpe') or img.endswith('.jpeg')):#jpg, jpe or jpeg
            return 'jpg'
        elif(img.endswith('.gif')):#gif
            return 'gif'
        elif(img.endswith('.png')):#png
            return 'png'
        elif(img.endswith('.bmp')):#bmp
            return 'bmp'
        else:
            return -1
        
    def addreplacealbumart(self, musicfile, albumartfile, imgtype):#Adds given albumartfile(path included) of imgtype to given musicfile
        #Generate ID3 representation of music file
        audio = MP3(musicfile, ID3=ID3)
        # add ID3 tags if none exist
        try:
            audio.add_tags()
        except error:
            pass

        #Pop any image that might be stored (the desc field is a title associated with an attached picture,
        #if two pictures are attached with different desc fields, both will be added)

        audio.tags.delall('APIC')

        #Add an image
        mimeentry='image/'+imgtype
        audio.tags.add(
                   APIC(
                        encoding=3, # 3 is for utf-8
                        mime=mimeentry, # image/jpeg or image/png
                        type=3, # 3 is for the cover image
                        desc=u'Cover',
                        data=open(albumartfile, 'rb').read()
                        )
                   )
        audio.save(v2_version=3)
        
#############################################
#Textbox (fields above dirdisplay) Functions#        
#############################################

    def tit_to_art(self, event):#Gives focus to textbox immediately below title, artist, saves data
        # \ / ? : * " > < | are banned
        tmp = self.mp3easygen(self.mp3fileinfocus)
        
        #print('Entered song title was')
        #print(self.t_title.get())
        #print(self.refreshpos)
        #Check and remove illegal characters
        tmp_t = self.detect_illegal(self.t_title.get(), '#\/:*?"<>|')
        if(tmp_t == 1):#All characters entered in title entry are legal. Proceed as normal
            #pass
            tmp['title'] = self.t_title.get()
            tmp.save(v2_version=3)
            #Refresh mp3 in dirlist and album art
            self.refresh_file()
        else:#Illegal characters were entered. Will not be translated to filename. Pop-up warning.
            self.genww_ic()
            tmp['title'] = self.t_title.get()
            tmp.save(v2_version=3)
            #Refresh mp3 in dirlist and album art
            self.refresh_file()
            #self.t_title.delete(0, 'end')#Remove illegal entry and place legal one
            #self.t_title.insert(0, tmp_t)
        
        
        #Set focus to artist entry    
        self.t_artist.focus_set()
        self.t_artist.selection_range(0, 'end')
        self.t_artist.icursor(0)#Sets cursor to first position in entry widget
    
    def art_to_alb(self, event):#Gives focus to textbox immediately below artist, album, saves data
        # \ / ? : * " > < | are banned
        tmp = self.mp3easygen(self.mp3fileinfocus)
        
        #print('Entered artist was')
        #print(self.t_artist.get())
        #print(self.refreshpos)
        #Check and remove illegal characters
        tmp_t = self.detect_illegal(self.t_artist.get(), '#\/:*?"<>|')
        if(tmp_t == 1):#All characters entered in title entry are legal. Proceed as normal
            #pass
            tmp['artist'] = self.t_artist.get()
            tmp.save(v2_version=3)
            #Refresh mp3 in dirlist and album art
            self.refresh_file()
        else:#Illegal characters were entered. Will not be translated to filename. Pop-up warning.
            self.genww_ic()
            tmp['artist'] = self.t_artist.get()
            tmp.save(v2_version=3)
            #Refresh mp3 in dirlist and album art
            self.refresh_file()
            #self.t_artist.delete(0, 'end')#Remove illegal entry and place legal one
            #self.t_artist.insert(0, tmp_t)
        
        
        #Set focus to album entry    
        self.t_album.focus_set()
        self.t_album.selection_range(0, 'end')
        self.t_album.icursor(0)#Sets cursor to first position in entry widget
        
    def alb_to_nex(self, event):#Go to next mp3 in dirdisplay, saves data
        # \ / ? : * " > < | . are banned
        tmp = self.mp3easygen(self.mp3fileinfocus)
        
        #print('Entered album was')
        #print(self.t_album.get())
        #print(self.refreshpos)
        #Check and remove illegal characters
        tmp_t = self.detect_illegal(self.t_album.get(), '#\/:*?"<>|')
        if(tmp_t == 1):#All characters entered in title entry are legal. Proceed as normal
            #pass
            tmp['album'] = self.t_album.get()
            tmp.save(v2_version=3)
            #Refresh mp3 in dirlist and album art
            self.refresh_file()
        else:#Illegal characters were entered. Will not be translated to filename. Pop-up warning.
            self.genww_ic()
            tmp['album'] = self.t_album.get()
            tmp.save(v2_version=3)
            #Refresh mp3 in dirlist and album art
            self.refresh_file()
            #self.t_album.delete(0, 'end')#Remove illegal entry and place legal one
            #self.t_album.insert(0, tmp_t)
        
        
        #Set focus to next song in dirlist    
        self.dirdisplay.focus_set()#Set input focus (up/down keys) to dirdisplay
        self.dirdisplay.selection_set((self.nextID, self.nextID))
        self.dirdisplay.focus(self.nextID)
        
        
    def extracttags(self, mp3infocus):#Takes the path of MP3 in focus and gets data for entry boxes
        #Clear entry boxes first
        self.clearentries()
        x=self.mp3easygen(mp3infocus)
        self.t_title.insert(0, self.get_songtitle(x))
        self.t_artist.insert(0, self.get_artist(x))
        self.t_album.insert(0, self.get_album(x))
        
    def clearentries(self):
        try:
            self.t_title.delete(0,'end')
            self.t_artist.delete(0,'end')
            self.t_album.delete(0,'end')
        except AttributeError:
            pass
        
    def disableentries(self):
        try:
            self.t_title.config(state=DISABLED)
            self.t_artist.config(state=DISABLED)
            self.t_album.config(state=DISABLED)
        except AttributeError:
            pass
        
    def enableentries(self):
        try:
            self.t_title.config(state=NORMAL)
            self.t_artist.config(state=NORMAL)
            self.t_album.config(state=NORMAL)
        except AttributeError:
            pass   
    
    def genww_ic(self):#Generate a pop-up that notifies user about illegal characters
        cw_ww = Toplevel(self, background='white')#Generate window
        cw_ww.focus_set()
        cw_ww.bind("<Return>", lambda event: self.cw_inclose(cw_ww))
        cw_ww.protocol("WM_DELETE_WINDOW", lambda: self.cw_inclose(cw_ww))
        cw_ww.title('Warning')#Title
        self.center_cw(cw_ww, ww_w, ww_h)#Center the window
        cw_ww.grab_set()
        cw_ww.rowconfigure(0, weight=1)
        cw_ww.rowconfigure(1, weight=1)
        cw_ww.rowconfigure(2, weight=1)
        cw_ww.columnconfigure(0, weight=1)
        
        #Elements of cw_ww window, made them self. so they persist
        img_slot = ttk.Label(cw_ww, image=self.ic_image, background="white")
        img_slot.grid(row=0, column=0, sticky=W)
        cw_ww_msg = Label(cw_ww, text=ILLEGAL_CHARACTERS, background="white", foreground="light sky blue", anchor=W, justify=LEFT, font=14)
        cw_ww_msg.grid(row=0, column=1)
        cw_ww_buf= Label(cw_ww, background="white")
        cw_ww_buf.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        cw_ww_okay = Button(cw_ww, text='OK', command= lambda: self.cw_inclose(cw_ww))
        cw_ww_okay.config(background='light sky blue', foreground='white')
        cw_ww_okay.grid(row=2, column=0, columnspan=2, sticky=NS)
        
        
        
        
##########################
#Directory List Functions#
##########################

    def init_dirlist(self):#Format left pane, 'dirlist'
        pass
        #Colours
        self.dirlist.hlist["background"] = "light sky blue"#Colour of background inside dirlist
        self.dirlist.hlist["foreground"] = "light cyan"#Colour of text
        self.dirlist["highlightcolor"] = "light grey"#Colour of border when you click dirlist
        self.dirlist.hlist["selectforeground"] = "light cyan"#Colour of text when you click on it
        self.dirlist.hlist["selectbackground"] = "steel blue"#Colour of highlight when you click text
 
        
    def populate_table(self, event):#Called when user double clicks on a directory in 'dirlist'
        self.disablealbumartbutton()#Ensure add album art is disabled
        self.clearentries()#Clear any tag data inside entries
        self.disableentries()#Disable user using entries
        self.clr_albumartslot()#Clear any album art data displayed
        self.working_directory = event#Used for suggestion scanning
        self.clearsuggestions()#Clear suggestion queue so they don't carry over from old directory
        self.clearstatusbar()
        self.disable_FG()
        self.directory_search(self.working_directory)
    
            
    def directory_search(self, directory):#Searches given directory for MP3s, prints, adds to 'dirdisplay'
        try:#Effectively clears 'dirdisplay' of previous contents
            x = self.dirdisplay.get_children()
            for item in x:
                self.dirdisplay.delete(item)
        except AttributeError:#If there was nothing displayed, go on
            pass
        for file in [doc for doc in os.listdir(directory) if doc.endswith(".mp3")]:
            try:#Add all MP3s without weird characters in filename to 'dirdisplay'
                self.enter_dirdata(file, directory)
            except UnicodeEncodeError:
                print("DO SOMETHING HERE TO TELL USER TO CHANGE FILE NAME")
        try:
            #Populate status bar for total of directory
            self.timetotal.config(text = self.intotime(self.s_timetotal))
            self.sizetotal.config(text = self.intosize(self.s_sizetotal))
        except AttributeError:
            pass

    def enter_dirdata(self, file, directory):#Adds given MP3 at directory path to 'dirdisplay'
        directorynfile = directory+'/'+file
        try:#Take the MP3 and turn it into an MP3 object to work with
            fileasmp3= self.mp3easygen(directorynfile)
            #Add MP3's time length to total for directory
            self.s_timetotal = self.s_timetotal + int(fileasmp3.info.length)
            #Add MP3's file size to total for directory
            self.s_sizetotal = self.s_sizetotal + os.path.getsize(directorynfile)
            #Values populates 'dirdisplay' using functions and variables for filename, title, artist, album plus a (hidden) path to file
            self.dirdisplay.insert('', 'end', file, text=file, values=(file, self.get_artist(fileasmp3), self.get_songtitle(fileasmp3), self.get_album(fileasmp3), directory))
        except TclError:
            print(file, "created a Whoopsie!")
            
    def mp3easygen(self, mp3toscan):#Take path+file given and turn it into an MP3 object to work with, returns it
        mp3rep = MP3(mp3toscan, ID3=EasyID3)
        try:#Checks if MP3 given already has tags, if it does move on
            mp3rep.add_tags(ID3=EasyID3)
        except mutagenx.id3.error:
            pass
        return mp3rep
    
    
    def get_artist(self, mp3representation):#Get Artist tag from MP3, return
        try:#Handling incase the tag is empty, return 'None'
            artist=str(mp3representation['artist'])
            result=artist[2:(len(artist)-2)]
        except KeyError:
            result=''
            
        return result
    
    def get_songtitle(self, mp3representation):#Get Song Title tag from MP3, return
        
        try:#Handling incase the tag is empty, return 'None'
            songtitle = str(mp3representation['title'])
            result = songtitle[2:(len(songtitle)-2)]
        except KeyError:
            result = ''
        return result    
    
    def get_album(self, mp3representation):#Get Album tag from MP3, return
        try:#Handling incase the tag is empty, return 'None'
            album = str(mp3representation['album'])
            result = album[2:(len(album)-2)]
        except KeyError:
            result = ''
        return result
    
    
    
#############################
#Directory Display Functions#
#############################

    def init_dirdisplay(self, Treeview):#Format right pane, 'dirdisplay' with colors, scrollbars
        #Scroll bars
        self.dirdisplay.configure(xscroll= self.xsb.set)
        self.dirdisplay.configure(yscroll= self.ysb.set)
        #The first node becomes invisible. Each entry is named after the file name including .mp3
        self.dirdisplay['show']= 'headings'
        #Column configuration
        self.dirdisplay.column('File Name', width= 300, anchor= W)
        self.dirdisplay.heading('File Name', text= 'File Name', anchor= W)
        self.dirdisplay.column('Artist', width= 75, anchor= W)
        self.dirdisplay.heading('Artist', text= 'Artist', anchor= W)
        self.dirdisplay.column('Song Title', width= 300, anchor= W)
        self.dirdisplay.heading('Song Title', text= 'Song Title', anchor= W)
        self.dirdisplay.column('Album', width= 75, anchor= W)
        self.dirdisplay.heading('Album', text= 'Album', anchor= W)
        #Colour schemes when populated
        ttk.Style().configure("Treeview", background='white', foreground='steel blue')
        
        
    def display_chosen(self, event):#Called when user clicks a song in 'dirdisplay', finds album art, populates entry boxes
        clickedfile = self.dirdisplay.focus()#Get child (row) id of click (not numerical index, effectively filename
        self.workingsongid=clickedfile
        self.refreshpos=self.dirdisplay.index(self.dirdisplay.focus())#Get's the index in dirdisplay of clicked song(the song you're working on)
        #print(self.refreshpos)
        if(clickedfile != ''):
            clickedfilepath = self.dirdisplay.set(clickedfile, 'path')#Get path column data
            mp3ID3rep = self.mp3id3gen(clickedfilepath+'/'+clickedfile)
            self.mp3fileinfocus = clickedfilepath+'/'+clickedfile#Tells the application which MP3 is selected
            self.nextID = self.dirdisplay.next(clickedfile)#Get next child
            #Set status bar segment for size and length of MP3
            self.s_timecurrent = self.intotime(mp3ID3rep.info.length)#Get length of clicked song
            s_tmp = os.path.getsize(clickedfilepath+'/'+clickedfile)
            self.s_sizecurrent = self.intosize(s_tmp)
            self.timecurrent.config(text = self.s_timecurrent)
            self.sizecurrent.config(text = self.s_sizecurrent)
            if(self.nextID == ""):#Clicked element is the last element in dirdisplay
                pass
            else:#Clicked element isn't the last in dirdisplay
                pass
                #print('Next is')
                #print(self.nextID)
            self.enable_FG()
            self.enablealbumartbutton()#Enable add album art button
            self.enableentries()#Enable entry boxes so extract tags works
            self.extracttags(self.mp3fileinfocus)#Extract title, artist, album from clicked MP3
            tempart= self.get_coverart(mp3ID3rep)
            try:
                pil_image=Image.open(tempart)
                pil_imagesized=pil_image.resize((100,100), Image.ANTIALIAS)
                self.albumartpic = ImageTk.PhotoImage(pil_imagesized)
                self.albumartslot['image']=self.albumartpic
            except FileNotFoundError:
                #print("No album art found")
                self.clr_albumartslot()
            self.t_title.focus_set()#Set focus to first entry widget, t_title
            self.t_title.selection_range(0, 'end')
            self.t_title.icursor(0)#Sets cursor to first position in entry widget
        else:
            pass
        
    def mp3id3gen(self, mp3toscan):#Take path+file given and turn it into an MP3 object to work with, returns it
        mp3rep = MP3(mp3toscan, ID3=ID3)
        try:#Checks if MP3 given already has tags, if it does move on
            mp3rep.add_tags(ID3=ID3)
        except mutagenx.id3.error:
            pass
        return mp3rep
            
    def get_coverart(self,mp3ID3rep):#Creates a temporary image file of album art, returns it
        name='testart'
        ext='.img'
        frames=mp3ID3rep.tags.getall("APIC")
        for frame in frames:
            if(frame.mime=="image/jpeg"):
                ext='.jpeg' 
                test=frame.data
                try:
                    with open(name+ext, 'wb') as img:
                        img.write(test)
                except:
                    print("Cannot print at ", name+ext)
            elif(frame.mime=="image/jpg"):
                ext='.jpg'
                test=frame.data
                try:
                    with open(name+ext, 'wb') as img:
                        img.write(test)
                except:
                    print("Cannot print at ", name+ext)
            elif(frame.mime=="image/png"):
                ext='.png'
                test=frame.data
                try:
                    with open(name+ext, 'wb') as img:
                        img.write(test)
                except:
                    print("Cannot print at ", name+ext)
            elif(frame.mime=='image/gif'):
                ext='.gif'
                test=frame.data
                try:
                    with open(name+ext, 'wb') as img:
                        img.write(test)
                except:
                    print("Cannot print at ", name+ext)

        return name+ext
    
######################
#Status Bar Functions#    
######################

    def intotime(self, seconds):#Takes info.length from MP3 and turns into hrs/minutes/seconds
        sseconds= int(seconds)
        hrs="000"
        mins="00"
        secs="00"
        firsttmp=divmod(sseconds,3600)
        tmphrs=firsttmp[0]
        if(tmphrs > 0):
            if(tmphrs < 10):
                hrs="00"+str(int(tmphrs))
            elif(tmphrs < 100):
                hrs="0"+str(int(tmphrs))
            elif(tmphrs < 1000):
                hrs= str(int(tmphrs))
            elif(tmphrs > 999):
                hrs=1000#Will be changed later in code with an if
        secondtmp=divmod(firsttmp[1], 60)
        tmpmins=secondtmp[0]
        if(tmpmins > 0):
            if(tmpmins < 10):
                mins="0"+str(int(tmpmins))
            elif(tmpmins < 60):
                mins= str(int(tmpmins))
        if(secondtmp[1] < 10):
            secs="0"+str(secondtmp[1])
        elif(secondtmp[1] > 9):
            secs= str(secondtmp[1])
        elif(secondtmp[1] == 0):
            return "000:00:00"
        if(hrs ==1000):
            return "999:59:59+"
        return hrs+":"+mins+":"+secs
    
    def intosize(self, size):#Returns the size of file in GB, MB or KB
        #Max - 999GB = 999*1024*1024*1024
        #1GB - 999MB = 999*1024*1024
        #1MB - 999KB = 999*1024
        #1KB - 999 B = 999
        num = "000"
        ending = " MB"
        if(size > 999*1024*1024*1024):#Size of file is over max
            num = "999"
            ending = "GB+"
        elif(size > 1*1024*1024*1024):#Size of file is over 999MB
            num = str(size/(1024*1024*1024))
            ending = " GB "
        elif(size > 1*1024*1024):#Size of file is over 999KB
            num = str(size/(1024*1024))
            ending = " MB "
        elif(size > 1*1024):#Size of file is over 999B
            num = str(size)
            ending = " B  "
        
        if('.' in num[:3]):#Ensure three characters plus '.' if needed
            result=num[:4]+ending[:(len(ending)-1)]
        else:
            result=num[:3]+ending
        return result
            
            
    def clearstatusbar(self):
        try:
            self.timecurrent.config(text='000:00:00')
            self.timetotal.config(text='000:00:00')
            self.s_timetotal = 0
            self.sizecurrent.config(text='000 GB ')
            self.sizetotal.config(text='000 GB ')
            self.s_sizetotal = 0
        except AttributeError:
            pass
        
class Scannerthreadobj(threading.Thread):#Scanner thread object
    def __init__(self, queue, s_queue, id, mode, directory):#Accepts a queue to associate itself with, id
        threading.Thread.__init__(self)
        self.queue = queue#Queue to use to report if done
        self.s_queue = s_queue#Queue to put suggestions
        self.id = id#Criteria to make suggestion search with
        self.directory=directory#Working directory to scan
        self.mode = mode#Which tag to suggest for mode=(0=title, 1=artist, 2=album)
        self.daemon = True
    def run(self):#What each scanner thread does
        for file in [doc for doc in os.listdir(self.directory) if doc.endswith(".mp3")]:
            try:
                if(self.id.lower() in file.lower()):#Case insensitive search
                    #Generate
                    tmpaddress = self.directory+'/'+file
                    tmp = App.mp3easygen(self, tmpaddress)
                    if(self.mode==0):#mode = 0 - title
                        if(self.id.lower() not in App.get_songtitle(self, tmp).lower()):
                            print(self.id.lower())
                            print(App.get_songtitle(self, tmp))
                            #Generate Suggestion to put in queue
                            s=Suggestion(file, self.directory, self.mode, self.id)
                            self.s_queue.put(s)
                    if(self.mode==1):#mode = 1 - artist
                        if(self.id.lower() not in App.get_artist(self, tmp).lower()):
                            #Generate Suggestion to put in queue
                            s=Suggestion(file, self.directory, self.mode, self.id)
                            self.s_queue.put(s)
                    if(self.mode==2):#mode = 2 - Album
                        if(self.id.lower() not in App.get_album(self, tmp).lower()):
                            #Generate Suggestion to put in queue
                            s=Suggestion(file, self.directory, self.mode, self.id)
                            self.s_queue.put(s)
            except UnicodeEncodeError:
                pass
        self.queue.put("Task finished")#Tells the application this thread is done

class Suggestion:#.mp3 filename, directory, mode = (0=title, 1=artist, 2=album)- NOT STRING, change to apply    
    def __init__(self, filename, directory, mode, changetoapply):
        self.filename=filename
        self.directory=directory
        self.mode=mode
        self.changetoapply=changetoapply
    def __str__(self):#What happens when you 'print()' a Suggestion
        if(self.mode == 0):#0=title
            change='Title'
        elif(self.mode == 1):#1=artist
            change='Artist'
        elif(self.mode == 2):#2=album
            change='Album'
        return self.directory+'/'+self.filename+'>>> '+change+' : '+self.changetoapply


if __name__ == "__main__":
    main()