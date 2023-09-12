/*
This will wire up our all of our `View selected ___` links to open a form for whichever
record is selected.
*/

$("select.addanotherchoicefieldwidget").on("change", function (e) {
  $("a[data-select_id=" + e.target.id + "]").prop("href", e.target.value);
});
