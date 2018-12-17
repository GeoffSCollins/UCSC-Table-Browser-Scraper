import time
import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox
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

        self.label = tk.Label(self.master, text="Please enter the regions you want the mean,"
                                                " min and max from:").grid(row=3)

        self.inputBox = tk.Text(self.master, height=25, width=50)
        self.inputBox.grid(row=4)

        self.startButton = tk.Button(self.master, text="Start", command=self.start).grid(row=5)

    # Getting the inputted data from the user after pressing the start button and running the program
    def start(self):
        table_browser_url = str(self.inputBoxURL.get("1.0", tk.END)).rstrip()
        regions_box_text = self.inputBox.get("1.0", tk.END).rstrip()

        if regions_box_text:
            with open('Gene File From Script.txt', 'w') as geneFile:
                geneFile.write(self.inputBox.get("1.0", tk.END))
            self.master.destroy()
            self.make_progress_bar()

            try:
                self.driver = webdriver.Chrome(os.getcwd() + "/chromedriver.exe")
                self.get_statistics(self, table_browser_url)
            except Exception as e:
                self.driver.quit()
                self.progressBar.close()
                RestartBox(e)

        else:
            RestartBox("The regions box was empty.")
            self.master.destroy()

    def make_progress_bar(self):
        self.progressBar = ProgressBar()

    # Main program that actually retrieves data from UCSC Table Browser
    @staticmethod
    def get_statistics(self, url):
        self.driver.get(url)

        # This gets the names of the tracks
        select_box = self.driver.find_element_by_name("hgta_track")
        options_array = [x for x in select_box.find_elements_by_tag_name("option")]
        name_array = [0] * len(options_array)

        for i in range(len(options_array)):
            element = options_array[i]
            name_array[i] = element.get_attribute("value")

        # Get lines that have regions in them
        num_lines = sum(1 for line in open('Gene File From Script.txt') if not len(line.strip()) == 0)

        with open('Gene File From Script.txt', 'r') as geneFile:
            for lineNum, line in enumerate(geneFile):
                gene_name = line.split()[0]
                region = line.split()[1]

                region_element = self.driver.find_element_by_name("position")
                region_element.clear()
                region_element.send_keys(region)

                select = Select(self.driver.find_element_by_id("hgta_track"))
                options = select.options

                dir_path = os.path.dirname(os.path.realpath(__file__))
                file_name = dir_path + '/Output/' + gene_name + '.txt'

                with open(file_name, 'w') as outputFile:
                    outputFile.write("Gene Name\tTrack Name\tRegion\tMean\tMin\tMax\n")

                    for index in range(len(options)):
                        if index == 0:
                            self.progressBar.set_finish_time(int(num_lines * len(options)))

                        track_name = name_array[index]
                        select = Select(self.driver.find_element_by_id("hgta_track"))
                        options = select.options

                        select.select_by_index(index)
                        self.driver.find_element_by_name('hgta_doSummaryStats').click()

                        file = self.driver.page_source

                        soup = BeautifulSoup(file, 'html.parser')

                        ucsc_output_table = soup.text[soup.text.find('mean'):soup.text.find('standard deviation')].rstrip()

                        mean_line = ucsc_output_table.partition('\n')[0]
                        mean_line_start_position = mean_line.find('n')+1
                        mean = float(mean_line[mean_line_start_position:])

                        min_line = ucsc_output_table.split('\n')[1]
                        min_line_start_position = min_line.find('n') + 1
                        ucsc_min = float(min_line[min_line_start_position:])

                        max_line = ucsc_output_table[ucsc_output_table.find("max"):]
                        max_line_start_position = max_line.find('x') + 1
                        ucsc_max = float(max_line[max_line_start_position:])

                        # Print data to another file
                        outputFile.write(str(gene_name) + '\t' + str(track_name) + '\t'+ str(region) + '\t' + str(mean)
                                         + '\t' + str(ucsc_min) + '\t' + str(ucsc_max) + '\n')

                        time.sleep(10)
                        self.driver.execute_script("window.history.go(-1)")
                        percent_complete = (index + 1) / len(options)
                        self.progressBar.update_progress_bar(percent_complete/num_lines)
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

        self.update_progress_bar(0)

    def update_progress_bar(self, value):
        self.value = value
        self.progress["value"] = self.value
        tk.Tk.update(self.popup)

    def set_finish_time(self, iterations):
        self.finishTime = self.startTime + datetime.timedelta(seconds=(iterations * 15)+10)
        self.finishText.config(text="Finish time: " + str(self.finishTime.time().replace(microsecond=0)))
        self.finishText.pack()
        tk.Tk.update(self.popup)

    def close(self):
        self.popup.destroy()


class RestartBox(tk.Tk):

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
    TableBrowserStats()
    root.mainloop()
