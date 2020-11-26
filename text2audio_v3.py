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


class Application:
    def __init__ (self, getFileNameFromPath, convertFiles, commandQueue):
        self.DELAY =                    100
        self.paths =                    []
        self.converting =               False
        # Declare main window and its components
        self.root =                     Tk()
        self.titleLabel =               Label(self.root, text="Text2Audio Converter", font=("Arial", 32), anchor="center")
        self.selectedFilesListBox =     Listbox(self.root)
        self.addButton =                Button(self.root, text="Add",           command=lambda: self.addButtonCommand(getFileNameFromPath))
        self.removeButton =             Button(self.root, text="Remove",        command=self.removeButtonCommand)
        self.removeAllButton =          Button(self.root, text="Remove all",    command=self.removeAllButtonCommand)
        self.convertButton =            Button(self.root, text="Convert files", command=lambda: self.convertButtonCommand(convertFiles, commandQueue))
        self.progressBar =              Progressbar(self.root)
        self.consoleLogTxt =            scrolledtext.ScrolledText(self.root, bg="black", fg="green", state="disabled")
        # Handle exit while converting
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
        # Queue handlers
        self.root.after(self.DELAY, self.commandQueueHandler, commandQueue)
    
    # GUI FUNCTIONS
    def start (self):
        # Set main window and its components
        self.root.title                 ("Text2Audio Converter")
        self.root.geometry              ("600x700")
        self.root.resizable             (False, False)
        self.titleLabel.place           (relx=0,     rely=0,     relwidth=1,    relheight=0.2)
        self.selectedFilesListBox.place (relx=0.025, rely=0.2,   relwidth=0.7,  relheight=0.5)
        self.addButton.place            (relx=0.76,  rely=0.2,   relwidth=0.2,  relheight=0.062)
        self.removeButton.place         (relx=0.76,  rely=0.275, relwidth=0.2,  relheight=0.062)
        self.removeAllButton.place      (relx=0.76,  rely=0.35,  relwidth=0.2,  relheight=0.062)
        self.convertButton.place        (relx=0.76,  rely=0.64,  relwidth=0.2,  relheight=0.062)
        self.progressBar.place          (relx=0.025, rely=0.725, relwidth=0.95, relheight=0.031)
        self.consoleLogTxt.place        (relx=0.025, rely=0.775, relwidth=0.95, relheight=0.2)
        # Start
        self.root.mainloop()

    def addButtonCommand (self, getFileNameFromPath):
        paths = filedialog.askopenfilenames(parent=self.root, initialdir="./", title="Select file", filetypes=(("all files","*.txt *.pdf"),("txt files","*.txt"),("pdf files","*.pdf")))
        for path in paths:
            self.paths.append(path)
            self.selectedFilesListBox.insert(self.selectedFilesListBox.size() + 1, getFileNameFromPath(path))

    def removeButtonCommand (self):
        selected = self.selectedFilesListBox.curselection()
        for file in selected:
            index = self.selectedFilesListBox.index(file)
            del self.paths[index]
            self.selectedFilesListBox.delete(index)

    def removeAllButtonCommand (self):
        self.paths = []
        self.selectedFilesListBox.delete(0, END)

    def convertButtonCommand (self, convertFiles, commandQueue):
        if not self.paths:
            return
        elif not messagebox.askokcancel("Confirmation", "Are you sure that you want to convert this files?\n (You wont be able to exit until the convertion has finished)"):
            return
        self.converting = True
        # Clear console
        self.consoleLogTxt.delete(1.0, END)
        # Set progress bar
        self.progressBar['maximum'] = int(len(self.paths))
        # Disable buttons
        self.addButton.config       (state="disabled")
        self.removeButton.config    (state="disabled")
        self.removeAllButton.config (state="disabled")
        self.convertButton.config   (state="disabled")
        # Start convert task
        self.convertTask = Process(target=convertFiles, args=(self.paths, commandQueue,))
        self.convertTask.dameon = True
        self.convertTask.start()
        
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
def convertFiles (paths, commandQueue):
    pool = Pool(5, text2mp3_init, [commandQueue])
    pool.map(text2mp3, paths)
    pool.close()
    pool.join()
    sendCommand(commandQueue, "END")

# Function that sets the command queue for the pool workers
def text2mp3_init (commandQueue):
    text2mp3.commandQueue = commandQueue

# Function that cgenerates a mp3 file from text
def text2mp3 (path):
    t = time.time()
    fileName = getFileNameFromPath(path)
    sendCommand(text2mp3.commandQueue, "PRINT", "Converting " + fileName + "...\n")
    tts = gTTS(getTextFromFile(path), lang='es')    
    tts.save("./" + fileName[:-4] + ".mp3")
    t = time.time() - t
    sendCommand(text2mp3.commandQueue, "PRINT", fileName + " has been converted in " + str("%0.2f" % t) + "s\n")
    sendCommand(text2mp3.commandQueue, "UPDATE")

# Function that returns the text of a file
def getTextFromFile (path):
    text = ""
    if path[-4:] == ".txt":
        file = open(path, 'r')
        text = file.read();
    elif path[-4:] == ".pdf":
        file = open(path, 'rb')
        reader = PyPDF2.PdfFileReader(file)
        for i in range(0, reader.numPages):
            text += reader.getPage(i).extractText()
    return text

# Function that sends messages to the GUI process
def sendCommand (commandQueue, command, message=""):
    commandQueue.put((command, message))

# Funcion that returns the names of the files in a directory
def getFileNameFromPath (path):
    head, tail = ntpath.split(path)
    return tail or nthap.basename(head)


# Global variables    
_commandQueue_ = Queue()    # This is for makeing a communication between the the conversion processes and the GUI process



# Main
if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    gui = Application(getFileNameFromPath, convertFiles, _commandQueue_)
    gui.start()

    input()
