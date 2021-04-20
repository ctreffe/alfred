// call this method when you want to leave the page without asking the user
var glob_unbind_leaving;

// call this method for moving
var move = function(direction) {
    $("#alt-submit").attr("name", "move");
    $("#alt-submit").val(direction);
    $("#form").submit();
}

$(document).ready(function () {

    // ask user before leaving, but not if he/she uses the form go to the next page.
    var beforeunload = function (event) {
        return "Möchten Sie wirklich die Seite verlassen?\n"
            + "Dadurch wird das Ausfüllen des Fragebogens abgebrochen.";
    };

    glob_unbind_leaving = function () {
        $(window).unbind('beforeunload', beforeunload);
    };



    $(window).bind('beforeunload', beforeunload);
    $('#form').submit(glob_unbind_leaving);

    // prevent users from submitting form via enter
    $(document).on("keydown", ":input:not(textarea):not(:submit)", function(event) {
        if (event.key == "Enter") {
            event.preventDefault();
        }
    });
      
});

// Responsive support for choice elements (switch to vertical layout on XS screens)
const responsive_choices = function () {
    if (window.screen.width <= 576) {

        $(".choice-button-group.btn-group").addClass("btn-group-vertical changed");
        $(".choice-button-group.btn-group").removeClass("btn-group");
        $(".form-check-inline").addClass("changed");
        $(".form-check-inline").removeClass("form-check-inline");
        
    } else {
        $(".choice-button-group.changed").addClass("btn-group");
        $(".choice-button-group.changed").removeClass("btn-group-vertical changed");

        $(".form-check.changed").addClass("form-check-inline");
        $(".form-check.changed").removeClass("changed")
    };
}

$(window).resize(function () {
    responsive_choices();
})

$(document).ready(function() {
    responsive_choices();
})