from gtts import gTTS
import glob
import PyPDF2


def text2mp3 (fileName):
    extension = fileName[-4:]
    if extension == ".txt":
        txt2mp3(fileName)
    elif extension == ".pdf":
        pdf2mp3(fileName)

def txt2mp3 (fileName):
    print("Converting " + fileName)
    
    file = open(fileName, 'r')
    _fileName = fileName[:-4]

    text = file.read();

    tts = gTTS(text, lang='es')    
    tts.save(_fileName + ".mp3")

    print(fileName + " has been converted\n")

def pdf2mp3 (fileName):
    print("Converting " + fileName)
    
    file = open(fileName, 'rb')
    reader = PyPDF2.PdfFileReader(file)
    _fileName = fileName[:-4]

    text = ""
    for i in range(0, reader.numPages):
        page = reader.getPage(i)
        text = page.extractText()
        
        tts = gTTS(text, lang='es')    
        tts.save(_fileName + "_pag" + str(i + 1) + ".mp3")

    print(fileName + " has been converted\n")


fileNames = glob.glob("./*.txt") + glob.glob("./*.pdf")
for fileName in fileNames:
    text2mp3(fileName)    

print("Finished")
