function saveTextAsFile()
{
    var textToSave = document.getElementById("inputTaxonomy").value;
    var textToSaveAsBlob = new Blob([textToSave], {type:"text/plain"});
    var textToSaveAsURL = window.URL.createObjectURL(textToSaveAsBlob);
    var fileName = "Taxonomy.txt";

    var downloadLink = document.createElement("a");
    downloadLink.download = fileName;
    downloadLink.innerHTML = "Download File";
    downloadLink.href = textToSaveAsURL;
    downloadLink.onclick = destroyClickedElement;
    downloadLink.style.display = "none";
    document.body.appendChild(downloadLink);

    downloadLink.click();
}

function destroyClickedElement(event)
{
    document.body.removeChild(event.target);
}

function loadFileAsText()
{
    var fileToLoad = document.getElementById("fileToLoad").files[0];

    var fileReader = new FileReader();
    fileReader.onload = function(fileLoadedEvent)
    {
        var textFromFileLoaded = fileLoadedEvent.target.result;
        document.getElementById("inputTaxonomy").value = textFromFileLoaded;
    };
    fileReader.readAsText(fileToLoad, "UTF-8");
}


function CopyToClipboard() {
    /* Getting text of textarea */
    var copyText = document.getElementById("outputXML");

    /* Selecting the textarea */
    copyText.select();

    /* Copying text inside the textarea */
    navigator.clipboard.writeText(copyText.value);

    /* Alert the copied text */
    alert("Copied to Clipboard!");
  }


