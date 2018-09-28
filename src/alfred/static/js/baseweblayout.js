// call this method when you want to leave the page without asking the user
var glob_unbind_leaving;

$(document).ready(function(){

    // jump on change in jumplist
    $('#jumpList').change(function(e) {
        $("#appendbox").append("<input type='hidden' name='move' value='jump' />");
        $("#appendbox").append("<input type='hidden' name='par' value='"+ $('#jumpList').val() +"' />");
        $("#form").submit();
    });

    // ask user before leaving, but not if he/she uses the form go to the next page.
    var beforeunload = function(event){
        return "Möchten Sie wirklich die Seite verlassen?\n"
            + "Dadurch wird das Ausfüllen des Fragebogens abgebrochen.";
    };

    glob_unbind_leaving = function() {
        $(window).unbind('beforeunload', beforeunload);
    };

    $(window).bind('beforeunload', beforeunload);
    $('#form').submit(glob_unbind_leaving);
});