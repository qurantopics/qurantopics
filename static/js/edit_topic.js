
function moveSelectedBefor(img) {
	var table = document.getElementById("ayat_table");
    var trs = table.tBodies[0].getElementsByTagName("tr");
    
    var index;
    if (img) {
        index = img.nextSibling.nextSibling.value -1;
    } else {
        index = trs.length
    }
    
    var beforeSelection = new Array();
    var selected = new Array();
    var afterSelection = new Array();

    var row;
    
    for(var i=0; i<trs.length; i++)
    {
        row = trs[i];
        if (isSelected(row)) {
            selected.push(row);
        } else if (i < index) {
            beforeSelection.push(row);
        } else {
            afterSelection.push(row);
        }
    }
    
    var newRows = beforeSelection.concat(selected, afterSelection);
    deleteAllRows(table);
    
    for(var i=0; i<newRows.length; i++)
    {
        row = newRows[i];
        table.tBodies[0].appendChild(row);
        row.cells[0].childNodes[3].value = i + 1;
        row.cells[2].childNodes[0].textContent = (i + 1) + '.';
        clearSelection(row);
    }

}

function isSelected(row) {
    return getCheckBox(row).checked;
}

function clearSelection(row) {
    getCheckBox(row).checked = false;
}

function getCheckBox(row) {
    return row.cells[1].childNodes[1];
}

function deleteAllRows(table) {
    while (table.rows.length != 0) {
        table.deleteRow(0); 
    }
}
