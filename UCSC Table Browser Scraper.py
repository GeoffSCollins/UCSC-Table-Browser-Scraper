'''
Ideas:
    IF User doesn't enter things in
    Make a timer and progress bar
    Maybe contain start time and estimated finish time
    Automatically import to excel
'''

import time
import threading
import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk

class TableBrowserStats(tk.Tk):

    # Making all of the GUI components
    def __init__(self, master):
        self.master = master
        master.geometry("400x500")
        master.title("Table Browser Statistics Extractor")

        self.labelURL = tk.Label(master, text="Please enter the URL for the table browser with tracks loaded:")
        self.labelURL.grid(row=1)

        self.inputBoxURL = tk.Text(master, height=1, width=50)
        self.inputBoxURL.grid(row=2)

        self.label = tk.Label(master, text="Please enter the regions you want the mean, min and max from:").grid(row=3)

        self.inputBox = tk.Text(master, height=25, width=50)
        self.inputBox.grid(row=4)

        self.startButton = tk.Button(master, text="Start", command=self.start).grid(row=5)

    # Getting the inputted data from the user after pressing the start button and running the program
    def start(self):
        tableBrowserURL = str(self.inputBoxURL.get("1.0", tk.END))
        tableBrowserURL = tableBrowserURL.rstrip()
        inputFile = self.inputBox.get("1.0", tk.END)
        geneFile = open('Gene File From Script.txt', 'w')
        geneFile.write(self.inputBox.get("1.0", tk.END))
        geneFile.close()
        ##############self.newWindow = tk.Toplevel(self.master)
        #############self.prog = progressBar(self.newWindow)
        #############self.master.destroy()

        self.makeProgressBar()
        self.getStatistics(self, tableBrowserURL)

    def makeProgressBar(self):
        self.progressBar = ProgressBar(master=self.master)
        self.progressBar.update()
        self.progressBar.start()

    #Main program that actually retrieves data from UCSC Table Browser
    @staticmethod
    def getStatistics(self, URL):
        driver = webdriver.Chrome("C:/Users/Geoff/Downloads/chromedriver_win32/chromedriver.exe")  # Optional argument, if not specified will search path.
        driver.get(URL);

        #This gets the names of the tracks
        select_box = driver.find_element_by_name("hgta_track")
        optionsArr = [x for x in select_box.find_elements_by_tag_name("option")]
        nameArr = [0] * len(optionsArr)
        p = 0
        for element in optionsArr:
            nameArr[p] = element.get_attribute("value")
            p = p+1

        numLines = sum(1 for line in open('Gene File From Script.txt'))
        currentLine = 0

        geneFile = open('Gene File From Script.txt', 'r')

        for line in geneFile:
            tabPos = line.find('\t')
            geneName = line[0:tabPos]
            region = line[tabPos+1:].rstrip()

            regionElement = driver.find_element_by_name("position")
            regionElement.clear()
            regionElement.send_keys(region)

            select = Select(driver.find_element_by_id("hgta_track"))
            options = select.options

            dir_path = os.path.dirname(os.path.realpath(__file__))
            fileName = dir_path + '/Output/' + geneName + '.txt'
            os.makedirs(os.path.dirname(fileName), exist_ok=True)

            outputFile = open(fileName, 'w')
            outputFile.write("Gene Name\tTrack Name\tRegion\tMean\tMin\tMax\n")

            currentLine+=1

            geneCompletion = currentLine / numLines
            print(geneCompletion)

            for index in range(0, len(options)):
                percentComplete = index / len(options)
                print(percentComplete)

                trackName = nameArr[index]
                select = Select(driver.find_element_by_id("hgta_track"))
                options = select.options

                select.select_by_index(index)
                driver.find_element_by_name('hgta_doSummaryStats').click()

                file = driver.page_source

                soup = BeautifulSoup(file, 'html.parser')

                goodText = soup.text[soup.text.find('mean'):soup.text.find('standard deviation')].rstrip()

                meanLine = goodText.partition('\n')[0]
                startPosFirst = meanLine.find('n')+1
                mean = float(meanLine[startPosFirst:])

                startSecondLine = goodText.find("min")
                minLine = goodText.split('\n')[1]
                startPosSec = minLine.find('n') + 1
                min = float(minLine[startPosSec:])

                startThirdLine = goodText.find("max")
                maxLine = goodText[startThirdLine:]
                startPosThird = maxLine.find('x') + 1
                max = float(maxLine[startPosThird:])

                #print data to another file
                outputFile.write(str(geneName) + '\t' + str(trackName) + '\t'+ str(region) + '\t' + str(mean) + '\t' + str(min) + '\t' + str(max) + '\n')
                #print(str(geneName) + '\t' + str(trackName) + '\t'+ str(region) + '\t' + str(mean) + '\t' + str(min) + '\t' + str(max))

                time.sleep(10)
                #############self.prog.update()
                self.progressBar.update()
                driver.execute_script("window.history.go(-1)")
                time.sleep(5)

class ProgressBar(tk.Tk, threading.Thread):

    #Need to get it to change and have an estimated time remaining or finish time
    def __init__(self, master):
        threading.Thread.__init__(self)
        self.master = master
        master.geometry("250x50")
        master.title("Progress")

        self.progress = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
        self.progress["maximum"] = 100
        self.progressVal = 0
        self.progress["value"] = 0
        #self.update()

    def update(self):
        self.progressVal += 1
        self.progress["value"] = self.progressVal
        #self.master.update()
        print("IM UPDATING")

        if self.progressVal < 100:
            print(self.progress["value"])
            self.master.update()
            time.sleep(0.3)
            self.update()




if __name__ == "__main__":
    root = tk.Tk()
    GUI = TableBrowserStats(root)
    root.mainloop()
