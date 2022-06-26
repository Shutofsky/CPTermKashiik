#!/usr/bin/python3
# -*- coding: utf-8 -*-
import curses
import random
import time
import json
import threading
import codecs
import string
import os
import ctypes
from sys import platform
from math import floor

termConf = dict()
termData = dict()

def millis():
    global termConf, termData
    return (time.time() - termConf['startTime']) * 1000.0

class readDBParms(threading.Thread):
    global termConf, termData
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
             
    def run(self):
        global termConf, termData
        try:
            while True:
                if termConf['forceClose']:
                    break
                if not termConf['isDBUpdating']:
                    termConf['isDBUpdating'] = True
                    with codecs.open(termConf['confPath'] + termConf['confName'], 'r', 'utf-8') as f:
                        termData = json.load(f) 
                    termConf['isDBUpdating'] = False
                time.sleep(2)
        finally:
            print('Exited!')
          
    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
  
    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')
      
def initCurses():
    global termConf, termData
    global curses
    curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(termConf['MAIN_COLOR']['pair'], termConf['MAIN_COLOR']['fg'], termConf['MAIN_COLOR']['bg'])
    curses.init_pair(termConf['HL_COLOR']['pair'], termConf['HL_COLOR']['fg'], termConf['HL_COLOR']['bg'])
    curses.init_pair(termConf['HL_1_COLOR']['pair'], termConf['HL_1_COLOR']['fg'], termConf['HL_1_COLOR']['bg'])
    curses.noecho()
    curses.raw()
    curses.curs_set(0)

def charGen():
    global termConf, termData
    charFlag = 1
    termConf['playChars'] = []
    for i in range(termData['numChars']):
        charFlag = 1
        while charFlag:
            charFlag = 0
            tmpChar = random.randint(0,255)
            for k in range(len(termConf['playChars'])):
                if (termConf['playChars'][k] == tmpChar):
                    charFlag = 1
        termConf['playChars'].append(tmpChar)

def matrixGen():
    global termConf, termData
    termConf['matrix'] = []
    charGen()
    for i in range(termData['rows']):
        tmpList = []
        for j in range(termData['cols']):
            tmpList.append(termConf['playChars'][random.randint(0,termData['numChars']-1)])
        termConf['matrix'].append(tmpList)

def codeGen():
    global termConf, termData
    dirFlag = 0
    i = 0
    col = random.randint(0, termData['cols']-1)
    row = random.randint(0, termData['rows']-1)
    termConf['codeList'].append(termConf['matrix'][col][row])
    for i in range(1,termData['hackLen']):
        if(dirFlag == 0):
            row = (row + random.randint(1, termData['rows']+1)) % 8
            termConf['codeList'].append(termConf['matrix'][col][row])
            dirFlag = 1
        else:
            col = (col + random.randint(1, termData['cols']+1)) % 8
            termConf['codeList'].append(termConf['matrix'][col][row])
            dirFlag = 0
    termConf['codeList'].reverse()
    for i in range(termData['hackLen']):
        termConf['codeString'] += "{:02x} ".format(termConf['codeList'][i])

def matrixPrint():
    global termConf, termData
    termConf['matrixWin'].clear()
    for i in range(termData['rows']):
        for j in range(termData['cols']):
            termConf['matrixWin'].addstr(i, j*3, "{:02x} ".format(termConf['matrix'][i][j]), 
                curses.color_pair(termConf['MAIN_COLOR']['pair']))
    termConf['matrixWin'].refresh()

def outWin(win, y, x, text, color):
    win.clear()
    win.addstr(y, x, text, curses.color_pair(color))
    win.refresh()

def printElMatrix(row,col,color):
    global termConf, termData
    if (termConf['matrix'][row][col] != ''):
        termConf['matrixWin'].addstr(row, col*3, "{:02x} ".format(termConf['matrix'][row][col]),color) 
    else:
        termConf['matrixWin'].addstr(row, col*3, "   ",color) 
                
def hlPos(row, col, direction):
    global termConf, termData
    if (not direction):
        for j in range(termData['cols']):
            printElMatrix(row, j, curses.color_pair(termConf['HL_COLOR']['pair']))
        for i in range(termData['rows']):
            printElMatrix(i, col, curses.color_pair(termConf['HL_1_COLOR']['pair']))
    else:
        for i in range(termData['rows']):
            printElMatrix(i, col, curses.color_pair(termConf['HL_COLOR']['pair']))
        for j in range(termData['cols']):
            printElMatrix(row, j, curses.color_pair(termConf['HL_1_COLOR']['pair']))
    printElMatrix(row, col, curses.color_pair(termConf['MAIN_COLOR']['pair'])|curses.A_REVERSE)
    termConf['matrixWin'].refresh()

def unhlPos(row, col):
    global termConf, termData
    for j in range(termData['cols']):
        printElMatrix(row, j, curses.color_pair(termConf['MAIN_COLOR']['pair']))
    for i in range(termData['rows']):
        printElMatrix(i, col, curses.color_pair(termConf['MAIN_COLOR']['pair']))
    termConf['matrixWin'].refresh()

def compareLists():
    global termConf, termData
    for i in range(termData['hackLen']):
        indBuf = len(termConf['buffList']) - 1 - i
        indCode = len(termConf['codeList']) - 1 - i
        if (termConf['buffList'][indBuf] != termConf['codeList'][indCode]):
            return False
    return True

def playHack():
    global termConf, termData
    dirFlag = 1 # fix rows
    row = 0
    col = 0
    startTime = 0
    curTime = 0
    termConf['matrixWin'].nodelay(True)
    termConf['matrixWin'].keypad(True)
    unhlPos(row, col)
    hlPos(row, col, dirFlag)
    while True:
        if (termConf['timeFlag'] == 1):
            curTime = millis()
            if ((curTime - startTime) >= 100):
                startTime = curTime
                termData['timeOut'] -= 1
                timeToStr()
                outWin(termConf['timerWin'], 0, 0, termConf['timeStr'], termConf['MAIN_COLOR']['pair'])
                if (termData['timeOut'] <= 0):
                    doLose()
        key = termConf['matrixWin'].getch()
        if dirFlag:
            if key == curses.KEY_LEFT or key == 260 or key == ord('A') or key == ord('a'):
                unhlPos(row,col)
                col -= 1
                if col == -1:
                    col = termData['cols'] - 1
                hlPos(row, col, dirFlag)
            if key == curses.KEY_RIGHT or key == 261 or key == ord('D') or key == ord('d'):
                unhlPos(row,col)
                col = (col + 1) % termData['cols']
                hlPos(row, col, dirFlag)
        else:
            if key == curses.KEY_UP or key == 259 or key == ord('W') or key == ord('w'):
                unhlPos(row,col)
                row -= 1
                if row == -1:
                    row = termData['rows'] - 1
                hlPos(row,col, dirFlag)
            if key == curses.KEY_DOWN or key == 258 or key == ord('S') or key == ord('s'):
                unhlPos(row,col)
                row = (row + 1) % termData['rows']
                hlPos(row, col, dirFlag)
        if key == curses.KEY_ENTER or key == 10 or key == 13:
            if (termConf['timeFlag'] == 0):
                startTime = millis()
                termConf['timeFlag'] = 1
            if (termConf['matrix'][row][col] != ''):
                unhlPos(row,col)
                termConf['buffList'].append(termConf['matrix'][row][col])
                termConf['buffString'] += "{:02x} ".format(termConf['matrix'][row][col]) + " "
                outWin(termConf['bufferWin'], 1, 0, "BUFFER: {:s}".format(termConf['buffString']), termConf['MAIN_COLOR']['pair'])
                termConf['matrix'][row][col] = ''
                dirFlag = (dirFlag + 1) % 2
                hlPos(row, col, dirFlag)
                if (len(termConf['buffList'])>=termData['hackLen']):
                    if(compareLists()):
                        doWin()
                    elif (len(termConf['buffList'])>termData['buffLen']):
                        doLose()

def menuScreen():
    global termConf, termData
    curses.curs_set(2)
    menuSel = []
    menuFullWin = curses.newwin(25, 80, 0, 0)
    menuServWin = curses.newwin(4, 80, 0, 0)
    menuMainWin = curses.newwin(21, 80, 4, 0)
    menuMainWin.clear()
    menuMainWin.refresh()
    x = 0
    y = 0
    outWin(menuServWin, 0, 0, termData['headMenu'], termConf['MAIN_COLOR']['pair'])
    maxLen= 0
    rows = 0
    for menuItem in termData['textMenu'].keys():
        if maxLen < len(menuItem):
            maxLen = len(menuItem)
        rows += 1
    y = int((21 - rows * 2) / 2)
    x = int((80 - maxLen)/2)
    for menuItem in termData['textMenu'].keys():
        menuMainWin.addstr(y, x, menuItem, curses.color_pair(termConf['MAIN_COLOR']['pair']))
        menuSel.append(menuItem)
        y += 2
    menuPos = 0
    y = int((21 - rows * 2) / 2)
    menuMainWin.addstr(y, x, menuSel[0], curses.color_pair(termConf['MAIN_COLOR']['pair']) | curses.A_REVERSE)
    menuMainWin.refresh()
    menuMainWin.keypad(True)
    curses.curs_set(0)
    while True:
        f = False
        key = menuMainWin.getch()
        if key == curses.KEY_UP or key == 259 or key == ord('W') or key == ord('w'):
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(termConf['MAIN_COLOR']['pair']))
            f = True
            if menuPos == 0:
                menuPos = len(menuSel) - 1
            else:
                menuPos -= 1
        if key == curses.KEY_DOWN or key == 258 or key == ord('S') or key == ord('s'):
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(termConf['MAIN_COLOR']['pair']))
            f = True
            if menuPos == len(menuSel) - 1:
                menuPos = 0
            else:
                menuPos += 1
        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter
            # Выбор позиции
            if termData['textMenu'][menuSel[menuPos]]["type"] == "text":
                menuMainWin.clear()
                menuServWin.clear()
                menuMainWin.refresh()
                menuServWin.refresh()
                readScreen(termData['textMenu'][menuSel[menuPos]]["name"])
            elif termData['textMenu'][menuSel[menuPos]]["type"] == "command":
            #    os.system(db_parameters['textMenu'][menuSel[menuPos]]["name"])
                menuFullWin.clear()
                menuMainWin.refresh()
                menuServWin.refresh()
        if f:
            y = int((21 - rows * 2) / 2) + 2*menuPos
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(termConf['MAIN_COLOR']['pair']) | curses.A_REVERSE)
            menuMainWin.refresh()
            f = False

def readScreen(fName):
    global termConf, termData
    curses.curs_set(2)
    readServWin = curses.newwin(4, 80, 0, 0)
    readServWin.clear()
    readServWin.nodelay(True)
    outWin(readServWin, 0, 0, termData['headRead'], termConf['MAIN_COLOR']['pair'])
    if platform == "linux" or platform == "linux2":
        with open(fName, 'r') as fh: 
            outTxtStr = fh.read()
    else:
        with codecs.open(fName, 'r', 'utf-8') as fh: 
            outTxtStr = fh.read()
    outTxtLst = outTxtStr.split('\n')
    readTextPad = curses.newpad(int(len(outTxtLst)/20 + 1)*20, 80)
    for str in outTxtLst:
        readTextPad.addstr(str+'\n', curses.color_pair(termConf['MAIN_COLOR']['pair']))
    readTextPad.refresh(0, 0, 4, 0, 23, 78)
    curses.curs_set(0)
    readServWin.nodelay(False)
    readServWin.keypad(True)
    rowPos = 0
    while True:
        f = False
        readServWin.move(0, 0)
        key = readServWin.getch()
        if key == curses.KEY_NPAGE or key == 338  or key == ord('S') or key == ord('s'):
            if rowPos < int(len(outTxtLst)/20)*20:
                rowPos += 20
                f = True
        if key == curses.KEY_PPAGE or key == 339 or key == ord('W') or key == ord('w'):
            if rowPos > 0:
                rowPos -= 20
                f = True
        if key == curses.KEY_BACKSPACE or key == 27:
            readServWin.clear()
            readServWin.refresh()
            menuScreen()
        if f:
            readTextPad.refresh(rowPos, 0, 4, 0, 23, 78)
            f = False

def doWin():
    menuScreen()

def doLose():
    print("YOU LOSE!")
    dbThread.raise_exception()
    dbThread.join()
    raise SystemExit

def timeToStr():
    global termConf, termData
    decs = int(termData['timeOut'] - 10*floor(termData['timeOut']/10))
    secs = int(termData['timeOut']/10%60)
    mins = int(termData['timeOut']/10/60%60)
    hours = int(termData['timeOut']/10/60/60%60)
    termConf['timeStr'] = "{:02d}:{:02d}:{:02d}.{:02d}".format(hours, mins, secs, decs)

def startTerm(stdscr):
    global termConf, termData
    initCurses()
    termConf['headWin'] = curses.newwin(4, 60, 0, 0)
    termConf['timerWin'] = curses.newwin(4, 20, 0, 60)
    termConf['bufferWin'] = curses.newwin(3, 80, 4, 0)
    termConf['matrixWin'] = curses.newwin(16, 24, 7, 0)
    termConf['codeWin'] = curses.newwin(16, 48, 7, 25)
    outWin(termConf['headWin'], 0, 0, termData['headHack'], termConf['MAIN_COLOR']['pair'])
    outWin(termConf['bufferWin'], 1, 0, "BUFFER: {:s}".format(termConf['buffString']), termConf['MAIN_COLOR']['pair'])
    matrixGen()
    codeGen()
    outWin(termConf['codeWin'], 0, 0, "SELECT CODE: {:s}".format(termConf['codeString']), termConf['MAIN_COLOR']['pair'])
    matrixPrint()
    timeToStr()
    outWin(termConf['timerWin'], 0, 0, termConf['timeStr'], termConf['MAIN_COLOR']['pair'])
    playHack()

def main(stdscr):
    global termConf, termData, dbThread
    with codecs.open("conf/CPTermConst.json", 'r', 'utf-8') as f:
            termConf = json.load(f) 
    termConf['startTime'] = millis()
    dbThread = readDBParms('DBReading')
    dbThread.start()
    time.sleep(1)
    while termConf['isDBUpdating']:
        # Ожидаем, пока обновится состояние из БД
        pass
    startTerm(stdscr)

curses.wrapper(main)