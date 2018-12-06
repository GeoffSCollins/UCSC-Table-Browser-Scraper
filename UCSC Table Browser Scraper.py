import time
import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime
import sys


class TableBrowserStats(tk.Tk):
    # Making all of the GUI components
    def __init__(self):
        self.master = tk.Toplevel()
        self.master.geometry("400x500")
        self.master.title("Table Browser Statistics Extractor")

        self.labelURL = tk.Label(self.master, text="Please enter the URL for the table browser with tracks loaded:")
        self.labelURL.grid(row=1)

        self.inputBoxURL = tk.Text(self.master, height=1, width=50)
        self.inputBoxURL.grid(row=2)

        self.label = tk.Label(self.master, text="Please enter the regions you want the mean, min and max from:").grid(row=3)

        self.inputBox = tk.Text(self.master, height=25, width=50)
        self.inputBox.grid(row=4)

        self.startButton = tk.Button(self.master, text="Start", command=self.start).grid(row=5)

    # Getting the inputted data from the user after pressing the start button and running the program
    def start(self):
        tableBrowserURL = str(self.inputBoxURL.get("1.0", tk.END))
        tableBrowserURL = tableBrowserURL.rstrip()

        regionsBoxText = self.inputBox.get("1.0", tk.END).rstrip()
        if regionsBoxText:
            with open('Gene File From Script.txt', 'w') as geneFile:
                geneFile.write(self.inputBox.get("1.0", tk.END))
            self.master.destroy()
            self.makeProgressBar()

            try:
                self.driver = webdriver.Chrome(os.getcwd() + "/chromedriver.exe")
                self.getStatistics(self, tableBrowserURL)
            except Exception as e:
                self.driver.quit()
                self.progressBar.close()
                restartBox(e)

        else:
            restartBox("The regions box was empty.")
            self.master.destroy()

    def makeProgressBar(self):
        self.progressBar = ProgressBar()
        self.progressBar.updateProgressBar(0)

    # Main program that actually retrieves data from UCSC Table Browser
    @staticmethod
    def getStatistics(self, URL):
        self.driver.get(URL)

        # This gets the names of the tracks
        select_box = self.driver.find_element_by_name("hgta_track")
        optionsArr = [x for x in select_box.find_elements_by_tag_name("option")]
        nameArr = [0] * len(optionsArr)

        for i in range(len(optionsArr)):
            element = optionsArr[i]
            nameArr[i] = element.get_attribute("value")

        # Get lines that have regions in them
        numLines = sum(1 for line in open('Gene File From Script.txt') if not len(line.strip()) == 0)

        with open('Gene File From Script.txt', 'r') as geneFile:
            for lineNum, line in enumerate(geneFile):
                geneName = line.split()[0]
                region = line.split()[1]

                regionElement = self.driver.find_element_by_name("position")
                regionElement.clear()
                regionElement.send_keys(region)

                select = Select(self.driver.find_element_by_id("hgta_track"))
                options = select.options

                dir_path = os.path.dirname(os.path.realpath(__file__))
                fileName = dir_path + '/Output/' + geneName + '.txt'

                with open(fileName, 'w') as outputFile:
                    outputFile.write("Gene Name\tTrack Name\tRegion\tMean\tMin\tMax\n")

                    for index in range(len(options)):
                        if index == 0:
                            self.progressBar.setFinishTime(int(numLines * len(options)))

                        trackName = nameArr[index]
                        select = Select(self.driver.find_element_by_id("hgta_track"))
                        options = select.options

                        select.select_by_index(index)
                        self.driver.find_element_by_name('hgta_doSummaryStats').click()

                        file = self.driver.page_source

                        soup = BeautifulSoup(file, 'html.parser')

                        goodText = soup.text[soup.text.find('mean'):soup.text.find('standard deviation')].rstrip()

                        meanLine = goodText.partition('\n')[0]
                        startPosFirst = meanLine.find('n')+1
                        mean = float(meanLine[startPosFirst:])

                        minLine = goodText.split('\n')[1]
                        startPosSec = minLine.find('n') + 1
                        min = float(minLine[startPosSec:])

                        startThirdLine = goodText.find("max")
                        maxLine = goodText[startThirdLine:]
                        startPosThird = maxLine.find('x') + 1
                        max = float(maxLine[startPosThird:])

                        # Print data to another file
                        outputFile.write(str(geneName) + '\t' + str(trackName) + '\t'+ str(region) + '\t' + str(mean) + '\t' + str(min) + '\t' + str(max) + '\n')

                        time.sleep(10)
                        self.driver.execute_script("window.history.go(-1)")
                        percentComplete = (index + 1) / len(options)
                        self.progressBar.updateProgressBar(percentComplete/numLines)
                        time.sleep(5)

        self.driver.quit()
        sys.exit(0)

class ProgressBar(tk.Tk):
    def __init__(self):
        self.popup = tk.Toplevel()
        self.popup.geometry("200x60+300+300")
        self.popup.title("Progress")

        self.progress = ttk.Progressbar(self.popup, orient="horizontal", length=200, mode="determinate")

        self.value = 0
        self.progress["value"] = 0
        self.max = 1
        self.progress["maximum"] = 1

        self.startTime = datetime.datetime.now()

        self.startText = tk.Label(self.popup, text="Start time: " + str(self.startTime.time().replace(microsecond=0)))
        self.finishText = tk.Label(self.popup, text="Finish time: Plese wait...")

        self.progress.pack()
        self.startText.pack()
        self.finishText.pack()

    def updateProgressBar(self, value):
        self.value = value
        self.progress["value"] = self.value
        tk.Tk.update(self.popup)

    def setFinishTime(self, iterations):
        self.finishTime = self.startTime + datetime.timedelta(seconds=(iterations * 15)+10)
        self.finishText.config(text="Finish time: " + str(self.finishTime.time().replace(microsecond=0)))
        self.finishText.pack()
        tk.Tk.update(self.popup)

    def close(self):
        self.popup.destroy()

class restartBox(tk.Tk):

    def __init__(self, error):
        self.result = messagebox.askyesno("Do you want to restart?", "This error occured: " + str(error) + "\nDo you want to restart?", icon='warning')

        if self.result:
            TableBrowserStats()
        else:
            sys.exit(1)


if __name__ == "__main__":
    if not os.path.exists(os.getcwd() + "/Output"):
        os.makedirs(os.getcwd() + "/Output")

    root = tk.Tk()
    root.withdraw()
    GUI = TableBrowserStats()
    root.mainloop()
