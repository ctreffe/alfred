$(".text-element table").addClass("table table-hover")

// call this method when you want to leave the page without asking the user
var glob_unbind_leaving;

$(document).ready(function () {

    // This is commented out, because jumplist is currently not implemented in the responsive design
    // jump on change in jumplist
    // $('#jumpList').change(function(e) {
    //     $("#appendbox").append("<input type='hidden' name='move' value='jump' />");
    //     $("#appendbox").append("<input type='hidden' name='par' value='"+ $('#jumpList').val() +"' />");
    //     $("#form").submit();
    // });

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