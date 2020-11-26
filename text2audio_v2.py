from gtts import gTTS
import glob
import PyPDF2
import multiprocessing
from multiprocessing import Process, Lock
import time


lock = Lock()

def text2mp3 (fileName):
    extension = fileName[-4:]
    if extension == ".txt":
        txt2mp3(fileName)
    elif extension == ".pdf":
        pdf2mp3(fileName)

def txt2mp3 (fileName):
    printer("Converting " + fileName + "...")
    
    t = time.time()
    
    file = open(fileName, 'r')
    _fileName = fileName[:-4]

    text = file.read();

    tts = gTTS(text, lang='es')    
    tts.save(_fileName + ".mp3")

    t = time.time() - t
    printer(fileName + " has been converted in " + str(t) + "s\n")

def pdf2mp3 (fileName):
    printer("Converting " + fileName + "...")
    
    t = time.time()
    
    file = open(fileName, 'rb')
    reader = PyPDF2.PdfFileReader(file)
    _fileName = fileName[:-4]

    text = ""
    for i in range(0, reader.numPages):
        page = reader.getPage(i)
        text += page.extractText()
        
    tts = gTTS(text, lang='es')    
    tts.save(_fileName + ".mp3")

    t = time.time() - t
    printer(fileName + " has been converted in " + str(t) + "s\n")

def printer (obj):
    lock.acquire()
    try:
        print(obj)
    finally:
        lock.release()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    fileNames = glob.glob("./*.txt") + glob.glob("./*.pdf")

    procs = []
    print("Files to convert:")
    for fileName in fileNames:
        print("\t" +fileName)
        proc = Process(target=text2mp3, args=(fileName,))
        proc.daemon = True
        procs.append(proc)        
        proc.start()
    print()

    for proc in procs:
        proc.join()
    
    print("Finished")
