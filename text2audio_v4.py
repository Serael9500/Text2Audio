from gtts import gTTS # Lib fot converting text to speech
import glob # Lib for reading directory files
import PyPDF2 # Lib for reading a pdf file
import multiprocessing # Lib for theading using multiple CPU cores
from multiprocessing import Process, Pool, Queue
import queue
from functools import partial
import time
import ntpath # Lib for processing path
import tkinter # GUI lib
from tkinter import *   
from tkinter.ttk import *
from tkinter import filedialog, scrolledtext, messagebox
from pydub import AudioSegment  # Lib for editing mp3 files
import os

# TODO: FINISH COMBINE 2 MP3 FILES IMPELENTATION 

# Class that stores the file properties
class Data:
    def __init__ (self, path, language):
        self.path = path
        self.language = language
        self.name = self.getFileNameFromPath(path)

    def getFileNameFromPath (self, path):
        head, tail = ntpath.split(path)
        return tail or nthap.basename(head)

    def getLanguage (self):
        if self.language == "es-es":
            return "Spanish(Spain)"
        elif self.language == "en-us":
            return "English(US)"
        elif self.language == "en-uk":
            return "English(UK)"
        return "-"


# Class that encapsulates a table made with Treeview
class Table():
    def __init__(self, parent):
        self.treeview = Treeview(parent)
        self.treeview['columns'] = ("language")
        self.treeview.heading("#0", text="File name", anchor='w')
        self.treeview.column("#0", anchor='w')
        self.treeview.heading('language', text="Language", anchor='w')
        self.treeview.column('language', anchor='w')

    def add (self, data):
        self.treeview.insert('', 'end', text=data.name, values=(data.getLanguage()))

    def edit (self, index, data):
        self.remove(index)
        self.treeview.insert('', index, text=data.name, values=(data.getLanguage()))

    def remove (self, index):
        children = self.treeview.get_children()
        self.treeview.delete(children[index])

    def removeAll (self):
        children = self.treeview.get_children()
        for child in reversed(children):
            self.treeview.delete(child)

    def getSelectedIndex (self):
        selectedItems = self.treeview.selection()
        indexes = []
        for item in reversed(selectedItems):
            indexes.append(self.treeview.index(item))
        return indexes


class Application:
    def __init__ (self, convertFiles, commandQueue):
        self.DELAY =        100
        self.data =         []
        self.converting =   False
        self.language =     "es-es"
        # Generate main window
        self.mainWindow(convertFiles, commandQueue)
        # Handle exit while converting
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
        # Queue handlers
        self.root.after(self.DELAY, self.commandQueueHandler, commandQueue)

    def mainWindow (self, convertFiles, commandQueue):
        # Define window elements
        self.root =                 Tk()
        self.titleLabel =           Label(self.root, text="Text2Audio Converter", font=("Arial", 32), anchor="center")
        self.selectedFilesTable =   Table(self.root)
        self.addButton =            Button(self.root, text="Add",             command=self.addButtonCommand)
        self.removeButton =         Button(self.root, text="Remove",          command=self.removeButtonCommand)
        self.removeAllButton =      Button(self.root, text="Remove all",      command=self.removeAllButtonCommand)
        self.selectLanguageButton = Button(self.root, text="Select language", command=self.languageSelectionWindow)
        self.convertButton =        Button(self.root, text="Convert files",   command=lambda: self.convertButtonCommand(convertFiles, commandQueue))
        self.progressBar =          Progressbar(self.root)
        self.consoleLogTxt =        scrolledtext.ScrolledText(self.root, bg="black", fg="green", state="disabled")
        # Place window elements
        self.root.title                         ("Text2Audio Converter")
        self.root.geometry                      ("600x700")
        self.root.resizable                     (False, False)
        self.titleLabel.place                   (relx=0,     rely=0,     relwidth=1,    relheight=0.2)
        self.selectedFilesTable.treeview.place  (relx=0.025, rely=0.2,   relwidth=0.7,  relheight=0.5)
        self.addButton.place                    (relx=0.76,  rely=0.2,   relwidth=0.2,  relheight=0.062)
        self.removeButton.place                 (relx=0.76,  rely=0.275, relwidth=0.2,  relheight=0.062)
        self.removeAllButton.place              (relx=0.76,  rely=0.35,  relwidth=0.2,  relheight=0.062)
        self.selectLanguageButton.place         (relx=0.76,  rely=0.425, relwidth=0.2,  relheight=0.062)
        self.convertButton.place                (relx=0.76,  rely=0.64,  relwidth=0.2,  relheight=0.062)
        self.progressBar.place                  (relx=0.025, rely=0.725, relwidth=0.95, relheight=0.031)
        self.consoleLogTxt.place                (relx=0.025, rely=0.775, relwidth=0.95, relheight=0.2)

    def languageSelectionWindow (self):
        SUPPORTED_LANGUAGES = [("Spanish (Spain)", "es-es"), ("English (US)", "en-us"), ("English (UK)", "en-uk")]
        language = StringVar()
        language.set(self.language)
        window = Toplevel(self.root)
        for aux in SUPPORTED_LANGUAGES:
            radioButton = Radiobutton(window, text=aux[0], value=aux[1], variable=language, state=ACTIVE if aux[1] == "es-es" else NORMAL)
            radioButton.pack()
        applyButton = Button(window, text="Apply", command=lambda: self.closeLanguageSelectionWindow(window, language.get(), True))
        applyButton.pack()
        cancelButton = Button(window, text="Cancel", command=lambda: self.closeLanguageSelectionWindow(window, language.get(), False))
        cancelButton.pack()
        
    # GUI FUNCTIONS
    def start (self):
        self.root.mainloop()

    def addButtonCommand (self):
        paths = filedialog.askopenfilenames(parent=self.root, initialdir="./", title="Select file", filetypes=(("all files","*.txt *.pdf"),("txt files","*.txt"),("pdf files","*.pdf")))
        for path in paths:
            data = Data(path, self.language)
            self.data.append(data)
            self.selectedFilesTable.add(data)

    def removeButtonCommand (self):
        indexes = self.selectedFilesTable.getSelectedIndex()
        for index in indexes:
            del self.data[index]
            self.selectedFilesTable.remove(index)

    def removeAllButtonCommand (self):
        self.data = []
        self.selectedFilesTable.removeAll()

    def convertButtonCommand (self, convertFiles, commandQueue):
        if not self.data:
            return
        elif not messagebox.askokcancel("Confirmation", "Are you sure that you want to convert this files?\n (You wont be able to exit until the convertion has finished)"):
            return
        self.converting = True
        # Clear console
        self.consoleLogTxt.delete(1.0, END)
        # Set progress bar
        self.progressBar['maximum'] = int(len(self.data))
        # Disable buttons
        self.addButton.config       (state="disabled")
        self.removeButton.config    (state="disabled")
        self.removeAllButton.config (state="disabled")
        self.convertButton.config   (state="disabled")
        # Start convert task
        self.convertTask = Process(target=convertFiles, args=(self.data, commandQueue,))
        self.convertTask.dameon = True
        self.convertTask.start()

    def closeLanguageSelectionWindow (self, window, language, apply):
        if apply:
            self.language = language
            indexes = self.selectedFilesTable.getSelectedIndex()
            for index in indexes:
                self.data[index].language = self.language
                self.selectedFilesTable.edit(index, self.data[index])
        window.destroy()
   
    # Function that handles the behaviour of the program if the user wants the kill it
    def onClosing (self):
        if self.converting:
            messagebox.showinfo("Warning", "You cannot exit while there is a convertion in progress.") 
        else:
            self.root.destroy()

    # Funcion that reads the messages form the queue and makes the right action
    def commandQueueHandler (self, commandQueue):
        try:
            command, msg = commandQueue.get(0)
            print(command, " | ", msg)
            if command == "END":
                self.converting = False
                # Kill convert task
                self.convertTask.terminate()
                # Enable buttons
                self.addButton.config       (state="normal")
                self.removeButton.config    (state="normal")
                self.removeAllButton.config (state="normal")
                self.convertButton.config   (state="normal")
            elif command == "PRINT":
                # Print on console
                self.consoleLogTxt.config   (state="normal")
                self.consoleLogTxt.insert   (INSERT, msg)
                self.consoleLogTxt.config   (state="disabled")
            elif command == "UPDATE":
                # Update progress bar
                self.progressBar["value"] = self.progressBar["value"] + 1
                self.progressBar.update()
        except queue.Empty:
            pass
        finally:
            self.root.after(self.DELAY, self.commandQueueHandler, commandQueue)
            

# Function that starts the process of convertion concurrently and with a maximum of 5 convertions at the same time
def convertFiles (data, commandQueue):
    pool = Pool(5, text2mp3_init, [commandQueue])
    pool.map(convertTask, data)
    pool.close()
    pool.join()
    sendCommand(commandQueue, "END")

# Function that sets the command queue for the pool workers
def text2mp3_init (commandQueue):
    text2mp3.commandQueue = commandQueue

# Function that cgenerates a mp3 file from text
def convertTask (data):
    t = time.time()
    sendCommand(text2mp3.commandQueue, "PRINT", "Converting " + data.name + "...\n")
    if path[-4:] == ".txt":     # Check if it's a txt file
        txt2mp3(data)
    elif path[-4:] == ".pdf":   # Check if it's a pdf
        pdf2mp3(data)
    tts = gTTS(getTextFromFile(data.path), lang=data.language)    
    tts.save("./" + data.name[:-4] + ".mp3")
    t = time.time() - t
    sendCommand(text2mp3.commandQueue, "PRINT", data.name + " has been converted in " + str("%0.2f" % t) + "s\n")
    sendCommand(text2mp3.commandQueue, "UPDATE")

def txt2mp3 (data):
    file = open(data.path, 'r')
    text = file.read();
    text2mp3(data.name[:-4], text, data.language)

def pdf2mp3 (data):
    fileName = data.name[:-4] + "_";
    file = open(data.path, 'rb')
    # Read each page and convert it
    reader = PyPDF2.PdfFileReader(file)
    for i in range(0, reader.numPages):
        text = reader.getPage(i).extractText()
        text2mp3(fileName + str(i), text, data.language)
    # Combine parts
    path = data.path[:-len(data.name)] + "/text2audio_temp/"
    filePath = path + fileName
    os.mkdir(path)
    for i in range(0, reader.numPages - 1):
        pathA = filePath + str(i) + ".mp3"
        pathB = filePath + str(i + 1) + ".mp3"
        # Load parts
        a = AudioSegment.from_mp3(pathA)
        b = AudioSegment.from_mp3(pathB)
        c = a + b
        # Delete parts
        os.remove(pathA)
        os.remove(pathB)
        # Save combined file
        if i < reder.numPages - 1:
            c.export(pathB, format="mp3")
        else:
            c.export(path[:-1] + ".mp3", format="mp3")    
        
def text2mp3 (fileName, text, language):
    tts = gTTS(text, lang=language)    
    tts.save("./" + fileName + ".mp3")

# Function that sends messages to the GUI process
def sendCommand (commandQueue, command, message=""):
    commandQueue.put((command, message))



# Global variables    
_commandQueue_ = Queue()    # This is for makeing a communication between the the conversion processes and the GUI process



# Main
if __name__ == '__main__':
    multiprocessing.freeze_support()
    gui = Application(convertFiles, _commandQueue_)
    gui.start()
