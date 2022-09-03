#############################################################################################
# IMPORT SECTION

#import all the required modules
from flask import Flask, request, render_template, send_file
from SPARQLWrapper import SPARQLWrapper, JSON
import os
import pandas as pd
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import xmltodict

##############################################################################################
# INITIALIZATION AND PREPROCESSING

# initialize flask app
app = Flask(__name__)

# create a directory for input inserted or uploaded by users
uploads_dir = os.path.join(app.instance_path, 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

# create a directory for output served to users at the end of data processing
downloads_dir = os.path.join(app.instance_path, 'downloads')
os.makedirs(downloads_dir, exist_ok=True)

# create some files to cache data
xml_input_file = 'input_data.xml'
xml_output_file = 'output_data.xml'
xml_output_clean = 'output.xml'

#############################################################################################
# VIEWS

# app routes to call and render static web pages

@app.route("/")
def index():
    # open index page in web browser
    return render_template('index.html')

@app.route("/input")
def input():
    # open input page in web browser
    return render_template('input.html')

@app.route("/documentation")
def documentation():
    # open contact page in web browser
    return render_template('documentation.html')

@app.route("/impressum")
def impressum():
    # open impressum in web browser
    return render_template('impressum.html')


#############################################################################################
# DATA PROCESSING FUNCTIONS - STARTING THE APP WORKFLOW
# the following 2 app routes are initialized by hitting the submit button (after users insert or upload files)


#######################################
# PROCESSING INSERTED TAXONOMY

# these processes are started when the form with the inserted input is submitted
@app.route("/insert", methods=['POST'])

# processing the inserted data
def process():

    # retrieve input from users provided via insert option (request looks for name attribute of the form)
    xml_input = request.form['insertXML']

    # set language according to users choice that will be used for the sparql query
    global xml_language
    xml_language = request.form['language']

    # check if insertion was successfull
    if request.method == 'POST':
        # write inserted data to xml file and save to input directory
        with open(os.path.join(uploads_dir, xml_input_file), 'w', encoding='utf-8') as f:
            f.write(str(xml_input))

        # continue with data processing
        return process_data()

    else:
        # return error message if there were any problems with saving the inserted text to a file
        return "Sorry, but there seem to be a problem with writing the inserted text to a file."


#######################################
# PROCESSING UPLOADED FILE

# these processes are started when the form with the inserted input is submitted
@app.route("/upload", methods=['POST'])

# processing the uploaded data
def upload():

    # set language according to users choice that will be used for the sparql query
    global xml_language
    xml_language = request.form['language']

    # check if upload was successfull
    if request.method == 'POST':
        # save uploaded file to input directory
        uploadedXML = request.files['uploadXML']
        uploadedXML.save(os.path.join(uploads_dir, xml_input_file))

        # continue with data processing
        return process_data()

    else:
        # return error message if there were any problems with saving the uploaded text to a file
        return "Sorry, but there seem to be problems with the upload of your file."


##########################################################################################
# CHECK INPUT AND UPLOAD

# processing the saved input data
def process_data():

    # test if input file was generated properly
    if os.path.exists(os.path.join(uploads_dir, xml_input_file)) == True:

        try:
            # parse input file with element tree parser to check if there is a taxonomy in the file
            global tree
            tree = ET.parse(os.path.join(uploads_dir, xml_input_file))

            # get the first element of the tree
            root = tree.getroot()

            # return an error message if neither the root element is a taxonomy element nor at any other a taxonomy can be found in the uploaded file
            if  root.tag != "taxonomy" and root.find("./taxonomy") == None and root.find(".//taxonomy")\
                and root.tag != "{http://www.tei-c.org/ns/1.0}taxonomy" and root.find('./{http://www.tei-c.org/ns/1.0}taxonomy') == None \
                    and root.find('.//{http://www.tei-c.org/ns/1.0}taxonomy') == None:
                missing_msg = "There is no (valid) taxonomy in your input."
                return render_template('retry.html', missing_msg = missing_msg)


            # return an error message if there are no category elements inside the taxonomy as this means that it is empty
            elif root.find("./category") == None and root.find(".//category") == None \
                    and root.find('./{http://www.tei-c.org/ns/1.0}category') == None and root.find('.//{http://www.tei-c.org/ns/1.0}category') == None:
                empty_msg = "Your input seems to be empty."
                return render_template('retry.html', empty_msg = empty_msg)

            else:

                try:
                    # parse input file to check if document is valid and continue with processing of the taxonomy
                    global xdata
                    xdata = minidom.parse(os.path.join(uploads_dir, xml_input_file))
                    return process_taxonomy()

                except Exception as e:
                # ask user to insert valid data if this error occur
                    error_msg = "Only well-formed taxonomies can be processed."
                    return render_template('retry.html', error_msg = error_msg, e=e)

        except Exception as e:
            # ask user to insert valid data if input is not processable, because of failed parsing
            invalid_msg = "Your input seems to be invalid."
            return render_template('retry.html', invalid_msg = invalid_msg)


    # return an error message if the input file was not created correctly
    else:
        upload_error_msg = "An error occurred during the upload of your data."
        return render_template('retry.html', upload_error_msg = upload_error_msg)


##########################################################################################
# PREPROCESS INPUT FOR WIKIDATA QUERY

#processing the provided taxonomy
def process_taxonomy():

    # check if the taxonomy only contains catDesc elements or also term elements
    # this check is for uploads with normal XML files, but also for TEI files which do always produce namespaces that have to be considered as well
    global catDesc_check
    catDesc_check = tree.find(".//catDesc") and tree.find('.//{http://www.tei-c.org/ns/1.0}catDesc')
    global catTerm_check
    catTerm_check = tree.find('.//term')
    global catTerm_TEI_check
    catTerm_TEI_check = tree.find('.//{http://www.tei-c.org/ns/1.0}term')

    global cols
    global rows

    # create columns and rows for a panda dataframe
    # for English taxonomies make two versions of search terms:
    # one with the first letter being lower case and another with upper case word beginnings
    if xml_language == 'en':
        cols = ["xml_id", "taxTerm", "taxTerm_capitals", "taxTerm_lowercase"]
        rows = []
        global language
        language = 'English'

    # for Germantaxonomies use only search terms starting with upper case
    else:
        cols = ["xml_id", "taxTerm", "taxTerm_capitals"]
        rows = []
        language = 'German'

    # get all category elements
    category = xdata.getElementsByTagName("category")

    # get all xml:id values from the category elements and append a row with the corresponding xml:ids
    for cat in category:
        xml_id = cat.getAttribute("xml:id")
        # return error if xml:id is missing
        if xml_id == "":
            missing_xmlid_msg = "There are missing one or more xml:ids in your <category> elements."
            return render_template('retry.html', missing_xmlid_msg = missing_xmlid_msg)
        else:
            rows.append({"xml_id": xml_id})

    # create a panda dataframe for further processing
    global xml_df
    xml_df = pd.DataFrame(rows, columns = cols)


    # checking if the text content is written directly into the catDesc or into nested term elements
    if catTerm_check is None and catTerm_TEI_check is None:

        # creating a variable to save list of search terms
        global tax_term

        # generating a list with the text content (character data) of the catDesc elements
        tax_term = xdata.getElementsByTagName("catDesc")

        # looking into the catDesc element and only process the content if it is text and if there is no other child element inside
        if tax_term.item(0).childNodes.item(0).nodeName == "#text" and tax_term.item(0).childNodes.item(1) == None:
               return process_searchterms()

        # telling the user that there seems to be something nested in catDesc that is not a term
        else:
            catDesc_nested_msg = "There seem to be elements inside the <catDesc> elements that are not supported."
            return render_template('retry.html', catDesc_nested_msg = catDesc_nested_msg)

    else:
        # generating a list with the text content (character data) of the term elements
        tax_term = xdata.getElementsByTagName("term")

        # only support term elements that have text as childNodes
        if tax_term.item(0).childNodes.item(0).nodeName != "#text":
            term_nested_msg = "There seem to be elements inside the <term> elements that are not supported."
            return render_template('retry.html', term_nested_msg = term_nested_msg)

        # process the data if there is only text in the term element
        else:
            return process_searchterms()


# process of the text content from the elements of the element tree
def process_searchterms():

    # create further lists of variations of the search term:
    # a list for the original text data and lists for manipulated data (uppercase and lowercase)
    catListOriginal = []
    catListCapitals = []
    catListSmallLetters = []

    # append the text data from the nodelist of catDesc or term elements to the lists
    for tt in tax_term:

        # strip the leading and trailing spaces for better processing of the text data
        item_original = (tt.firstChild.nodeValue).strip()
        item_capitals = (tt.firstChild.nodeValue.capitalize()).strip()
        item_lowercase = (tt.firstChild.nodeValue.lower()).strip()

        #append the stripped terms to different lists
        catListOriginal.append(item_original)
        catListCapitals.append(item_capitals)
        catListSmallLetters.append(item_lowercase)

    # for English taxonomies add one column for lowercase spelling
    if xml_language == 'en':

        xml_df["taxTerm_original"] = catListOriginal
        xml_df["taxTerm_capitals"] = catListCapitals
        xml_df["taxTerm_lowercase"] = catListSmallLetters

    # for Germantaxonomies there is no need for a column with lowercase spelling
    else:
        xml_df["taxTerm_original"] = catListOriginal
        xml_df["taxTerm_capitals"] = catListCapitals

    # generate an empty container list to store the data of the dataframe in another structure
    # this helps to have a list of search terms for every entry, so their relation is more comprehensible
    global tablelist
    tablelist = []

    # from the dataframe generate a nested list of all the rows containing the xml:id and different spelling variants of the individual taxonomy entries
    for index,rows in xml_df.iterrows():

        # for english taxonomies there is one additional row with lowercase word beginnings
        if xml_language == 'en':
            rowlist = [rows.taxTerm_original, rows.taxTerm_capitals, rows.taxTerm_lowercase, rows.xml_id]
            tablelist.append(rowlist)

        # for Germantaxonomies the lists do not include lowercase word beginnings
        else:
            rowlist = [rows.taxTerm_original, rows.taxTerm_capitals, rows.xml_id]
            tablelist.append(rowlist)

    # continue with query function
    return wikidata_query()


##################################################################
# WIKIDATA QUERY VIA SPARQLWRAPPER

# using the preprocessed data for Wikidata queries
def wikidata_query():

    # initializing the SPARQLWrapper
    # indicate agent to prevent queries being blocked from Wikidata - see also Wikidata User-Agent policy: https://meta.wikimedia.org/wiki/User-Agent_policy
    sparql = SPARQLWrapper(
    "https://query.wikidata.org/sparql", agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0")

    # set the format for results to JSON
    sparql.setReturnFormat(JSON)

    # initialize an empty comtainer list to add all the results and another container list for all the search terms that should get requested by the sparql query
    result_data= []
    global processing_termlist
    processing_termlist = []

    # take one row of the dataframe that is now saved in a list
    for termlist in tablelist:
        # First element of termlist contains original spelling of search term
        # Displaying the search process on the terminal :)
        print("Looking for the term " + str(termlist[0]))
        processing_termlist.append(termlist[0])

        # transform list to a set to avoid duplicates (for example when "original spelling" is the same like lowercase spelling)
        termset = set(termlist)

        # initalize a container list to add all the data that is found to all possible terms with different spelling of one taxonomy entry
        cat_data = []

        # take all variants of one term and try to find Wikidata entries
        for term in termset:
            # this is the query that is send to the Wikidata API - it looks for the search terms and sets the language to whatever language was choosen by the user
            # there are more results when we cancel the 3rd and the 4th condition, but it seems to be also less precise and not so performant
            sparql.setQuery(
            """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE{
                ?item ?label \"""" + term + """\"@""" + xml_language + """.
                ?article schema:about ?item .
                ?article schema:inLanguage \"""" + xml_language + """\" .
                ?article schema:isPartOf <https://""" + xml_language + """.wikipedia.org/>.
                SERVICE wikibase:label { bd:serviceParam wikibase:language \"""" + xml_language + """\". }
            }
                """
            )

            try:
                # save query results in a dictionary
                result = sparql.queryAndConvert()

                # initialize a container list for the query results for all variants of a term and another list that contains the data to one single search term
                term_rows = []
                term_data = []

                # if the query provides no results, fill rows with dashes, but for better reference always keep the search term and the xml:id in the list
                if (result["results"]["bindings"]) == []:

                    # append rows that indicate missing results for english queries
                    # for english taxonomies the xml:id is to be found on the index no. 3
                    if xml_language == 'en':
                        term_rows.append(["No results", "-", "-", "-", term, termlist[3]])

                    # append rows that indicate missing results for Germanqueries
                    # for Germantaxonomies the xml:id is on index no. 2
                    else:
                        term_rows.append(["No results", "-", "-", "-", term, termlist[2]])

                # if query provides results extract the data of wikidata result and add them to the single term list
                else:

                    # access the lists in the result which is a nested list in json format and store results in variables
                    for r in result["results"]["bindings"]:

                        #store whole URL from Wikidata entry
                        wd_url = r['item']['value']

                        #store Q Identifier from Wikidata entry
                        wd_qnr = wd_url.removeprefix('http://www.wikidata.org/entity/')

                        #store label (= proper noun) from Wikidata entry
                        wd_itemLabel = r['itemLabel']['value']

                        # as some Wikidata entries do not provide itemDescriptions they
                        wd_itemDescription = (r.get('itemDescription', {'value': 'Not Found'})).get('value', 'Not Found')

                        # append the results for english queries - every term may have various Wikidata entries
                        # for english taxonomies the xml:id is to be found on the index no. 3
                        if xml_language == 'en':
                            term_rows.append([wd_qnr, wd_itemLabel, wd_itemDescription, wd_url, term, termlist[3]])

                            # append the results for Germanqueries - every term may have various Wikidata entries
                        # for Germantaxonomies the xml:id is on index no. 2
                        else:
                            term_rows.append([wd_qnr, wd_itemLabel, wd_itemDescription, wd_url, term, termlist[2]])

                # put results for individual search term that was searched for into container list
                for t in term_rows:
                    term_data.append(t)

                # put all results for different variants of one search term into container list
                cat_data.append(term_data)

            # for errors with the sparql query provide an error message in the terminal
            except Exception as e:
                        print(e)

        # put results for one category into list containing all results
        result_data.append(cat_data)

    # for html rendering in datatables extract lists
    # result_headerlist contains datatable header and term_table with all different spellings of one term
    global result_headerlist
    result_headerlist = ["QIdentifier", "WikidataLabel", "Description", "WikidataLink", "SearchTerm", "XMLID"]

    # initialize an empty container list to append results
    term_table = []

    # store every result for one search term in a seperate row
    for term_results in result_data:
        term_table.append(term_results)

    # initialize another empty container list to clean data
    global term_table_clean
    term_table_clean = []

    # for english taxonomies there might be 3 to 4 termblocks
    # e.g. for upper and lower case of the original term and multi-word compounds -> petrarchan sonnet, Petrarchan Sonnet, Petrarchan sonnet etc.
    for term_block in term_table:
        if len(term_block) == 4:
            if term_block[0][0][0] == term_block[1][0][0] == term_block[2][0][0] == term_block[3][0][0]:
                term_table_clean.append([[["No matches", "-", "-", "-", "-" , str(term_block[0][0][5])]]])
            else:
                term_table_clean.append(term_block)
        elif len(term_block) == 3:
            if term_block[0][0][0] == term_block[1][0][0] == term_block[2][0][0]:
                term_table_clean.append([[["No matches", "-", "-", "-", "-", str(term_block[0][0][5])]]])
            else:
                term_table_clean.append(term_block)

        # for category elements that do not have an xml:id or for Germansearch terms there might be only 2 termblocks (for upper and lower case of the original term)
        elif len(term_block) == 2:
            if term_block[0][0][0] == term_block[1][0][0]:
                term_table_clean.append([[["No matches", "-", "-", "-", "-" , str(term_block[0][0][5])]]])
            else:
                term_table_clean.append(term_block)
        elif len(term_block) == 1:
            if term_block[0][0][0] == "No results":
                term_table_clean.append([[["No matches", "-", "-", "-", "-" , str(term_block[0][0][5])]]])
            else:
                term_table_clean.append(term_block)

        # in case of an unforeseen problem with the length of the search term lists provide an error message
        else:
            data_problem_error_msg = "Sorry, but your data could not be processed."
            return render_template('retry.html', data_problem_error_msg = data_problem_error_msg)

    # count the maximum number of matches to give the user an overview
    maximum_matches = (len(term_table_clean))

    # initialize a variable for actual matches
    actual_matches = 0

    # count all the results that contain any textual results other than "No matches" (which are all search term that did not provide any results at all)
    for nested_list in term_table_clean:
        if nested_list[0][0][0] != "No matches":
            actual_matches +=1


    # if the whole process was successfull, load the results into a new html view
    return render_template('result.html', maximum_matches = maximum_matches, actual_matches = actual_matches, language = language)


#########################################################################################

# this function is triggered by the user submitting hitting the "Go-to-results" button on the result.html
@app.route("/enrich", methods=['POST'])

# rendering the search results
def enrich():
    # the results will be loaded, if the user confirms that his language choice was correct and that he wants to see the results
    return render_template('enrich.html', result_headerlist=result_headerlist, term_table_clean=term_table_clean, processing_termlist=processing_termlist)


##########################################################################################
# PROCESS DATATABLES AFTER SELECTION / MANIPULATION THROUGH USER

# the following processes are initialized by the user submitting his selection of Wikidata references
@app.route("/reconcile", methods=['POST'])

# processing the selected data from the datatables
def reconcile():

    # access form to be processed
    if request.method == "POST":

        # save the xml:ids plus the corresponding Wikidata Q Identifier that was slected by the user into dictionary
        list_ids = request.form.to_dict(flat=False)

        #initialize an empty container list to save the Wikidata Q Identifiers
        list_wd_ids = []

        # take the ids from the dictionary and append to new list
        for ids in list_ids.values():
            list_wd_ids.append(ids[0])

        # get the namespace abbreviation that was entered by the user
        namespace = request.form['namespace']

        # parse the input xml file and get root tree starting with root element (=taxonomy)
        if os.path.exists(os.path.join(uploads_dir, xml_input_file)) == True:
            input_xml_tree = ET.parse(os.path.join(uploads_dir, xml_input_file))

            # look for the root element of the element tree
            root = input_xml_tree.getroot()

            # check if there are category elements in the tree
            if root.find(".//category") != None:

                # simultaneously iterate through category elements in the xml tree and in the Wikidata Q Identifier list generated by user's choice
                # add a corresp attribute to every category element and fill it with the corresponding value of the Wikidata Q Identifier list
                for elem,wd_id in zip(root.iter('category'), list_wd_ids):

                    # only set correspond attribute if there is a Q Identifier available
                    if str(wd_id) != "No results" and str(wd_id) != "No matches":
                        elem.set("corresp", str(namespace) + ":" + str(wd_id))

            # there might also be TEI elements with namespaces that need to be handled as well
            else:

                # add also here corresp attributes to every TEI category element and fill it with the corresponding value of the Wikidata Q Identifier list
                for elem,wd_id in zip(root.iter('{http://www.tei-c.org/ns/1.0}category'), list_wd_ids):

                    # only set correspond attribute if there is a Q Identifier available
                    if str(wd_id) != "No results" and str(wd_id) != "No matches":
                        elem.set("corresp", str(namespace) + ":" + str(wd_id))


            # save the enriched xml tree to an output file
            input_xml_tree.write(os.path.join(downloads_dir, xml_output_file), encoding="utf-8", xml_declaration=True, short_empty_elements=True)

            # create a new output container (for removing blank lines)
            clean_xml_output = ""

            # open the generated output file write seperate lines to the clean the output file
            with open(os.path.join(downloads_dir, xml_output_file), "r", encoding="utf-8") as f:

                # go through every line of the output file
                for line in f:

                    # ignore blank lines
                    if not line.isspace():
                        # in case during the processing there were namespace abbreviations generated in TEI files remove the namespace-pattern

                        # first clean the TEI tag and add clean lines
                        if "ns0:TEI xmlns:ns0" in str(line):

                            line = str(line).replace("ns0:TEI xmlns:ns0","TEI xmlns")
                            clean_xml_output+=line

                        # then clean all other tags and add clean lines
                        elif "ns0:" in str(line):
                            line = str(line).replace("ns0:", "")
                            clean_xml_output+=line

                        # for processed data without elements just write every single line to the new ouptut document
                        else:
                            clean_xml_output+=line


            # write enriched taxonomy to the output file
            f = open(os.path.join(downloads_dir, xml_output_clean), 'w', encoding="utf-8")
            f.write(clean_xml_output)


            # provide download page of web app
            return render_template('download.html', namespace = namespace)

        # provide error message if anything failed in reconciliation process
        else:
            return "Unfortunately, the reconciliation failed."


##########################################################################################
# DOWNLOAD PROCESS

# the following processes are initiliazed by
@app.route('/download')
def download():
    # allow download of output file for users by clicking the download button
    # unfortunately it's not possible to send file and render template with download message simultaneously
    if os.path.exists(os.path.join(downloads_dir, xml_output_clean)) == True:
        path = os.path.join(downloads_dir, xml_output_clean)
        return send_file(path, as_attachment=True, attachment_filename="enriched_output.xml")

    # return an error message if the download is not possible
    else:
        download_error_msg = "Sorry, but something went wrong with the download option."
        return render_template('download.html', download_error_msg = download_error_msg)




#################################################################################################
# EXECUTION OF SCRIPT

# parameter setting to run the app on the localhost
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
