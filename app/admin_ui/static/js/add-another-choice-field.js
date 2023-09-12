/*
This will wire up all of our `Add a new record` links to open a form for a new
record.

https://stackoverflow.com/a/5744595/728583
https://github.com/yourlabs/django-autocomplete-light/commit/599687fc71fe5ecf054afc47935626b81e6a8bf2
https://usefulangle.com/post/4/javascript-communication-parent-child-window
*/

document.querySelectorAll(".add-another").forEach(function (elem) {
    return elem.addEventListener('click', function (e) {
        window.open(this.dataset.form_url, id_to_windowname(this.dataset.select_id));
        e.preventDefault();
    });
});

var dismissAddAnotherPopup = function (win, newId, newRepr) {
    var formId = windowname_to_id(win.name);
    var elem = document.getElementById(formId);
    newRepr = htmlDecode(newRepr);

    if (elem) {
        if ($(elem).is('select')) {
            var o = new Option('*' + newRepr, newId);
            elem.options[elem.options.length] = o;
            o.selected = true;
        }
    } else {
        console.log("Could not get input id for win " + formId);
    }

    console.log(newId);

    win.close();
}


function htmlDecode(input) {
    var e = document.createElement('div');
    e.innerHTML = input;
    return e.childNodes.length === 0 ? "" : e.childNodes[0].nodeValue;
}

// IE doesn't accept periods or dashes in the window name, but the element IDs
// we use to generate popup window names may contain them, therefore we map them
// to allowed characters in a reversible way so that we can locate the correct
// element when the popup window is dismissed.
var id_to_windowname = function (text) {
    text = text.replace(/\./g, '__dot__');
    text = text.replace(/\-/g, '__dash__');
    text = text.replace(/\[/g, '__braceleft__');
    text = text.replace(/\]/g, '__braceright__');
    return text;
}

var windowname_to_id = function (text) {
    text = text.replace(/\__dot__/g, '.');
    text = text.replace(/\__dash__/g, '-');
    text = text.replace(/\__braceleft__/g, '[');
    text = text.replace(/\__braceright__/g, ']');
    return text;
}