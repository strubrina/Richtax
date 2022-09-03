# Richtax
 
 The Richtax App is a tool that enables you to easily enrich your TEI taxonomies with Linked Open Data references.
 
Let your taxonomy terms be compared to Wikidata entries and their descriptions and choose a matching Wikidata item to be linked to your taxonomy entry in an easy-to-handle user interface. The application will enrich your taxonomy entries with Wikidata Q Identifiers - unique identifiers that will bring your taxonomy one step closer to being a part of the Semantic Web.

The Richtax App is written in Python and based on [Flask](https://flask.palletsprojects.com/en/2.2.x/) and [Jinja](https://jinja.palletsprojects.com/en/3.1.x/). 
It can be executed from your terminal and runs on localhost. So, you do not have to worry about uploading any of your files to the internet, but you always have them locally on your computer.

Further information about the app and documentation can be found on the web pages when running the app. 


## Starting the App (on Windows)

1. If you do not have Python installed, please download [Python 3.9.11](https://www.python.org/downloads/release/python-3911/) or a later version. If you are a Python beginner or have downloaded it the first time, don't forget to add the PATH to the environment variables. 

2. Download the Richtax Code from GitHub, unzip it and store it on your computer.

3. Open your terminal/shell and check if Python was installed properly by entering `py --version` (The version of your Python distribution should be displayed now.)

4. Navigate to the folder where the app is stored (for example: C:/Users/alex/Documents/richtax-main) 

5. If there might be interferences with other versions of the required moduls for this app, I recommend creating a virtual environment. Here you can find [helpful instructions](https://towardsdatascience.com/virtual-environments-for-absolute-beginners-what-is-it-and-how-to-create-one-examples-a48da8982d4b) on virtual environments. 

6. Then (in your venv or just like this) install the required moduls using `pip install -r requirements.txt`

7. Run the app with the command `py main.py` 

8. Press CTRL + click on the adress of localhost: http://127.0.0.1:8080 (You can ignore the Warning about localhost just being a development server.)

9. Your browser should open the application now - please refer to the documentation in the Richtax app to learn more about the workflow.

10. There are two example files attached in the example folder - have fun testing Richtax or using it for your own taxonomies :) 


## Using the App

Please refer to the documentation in the application itself. 

In case the app crashes, just go to your terminal and press CTRL + C and restart the app. 


## Closing the App

To quit the app just follow the instructions in the terminal and press CTRL + C. 

