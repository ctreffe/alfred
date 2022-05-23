// call this method when you want to leave the page without asking the user
var glob_unbind_leaving;

// call this method for moving
var move = function(direction) {
    $("#alt-submit").attr("name", "move");
    $("#alt-submit").val(direction);
    $("#form").submit();
}


var move_prep = function() {
    $("#back_button").prop("disabled", true);
    $("#forward_button").prop("disabled", true);
    $("#finish_button").prop("disabled", true);

    $("#back_button").unbind("click");
    $("#forward_button").unbind("click");
    $("#finish_button").unbind("click");
}

$("#back_button").one("click", function(){
    move_prep();
    move("backward");
})

$("#forward_button").one("click", function(){
    move_prep();
    move("forward");
})

$("#finish_button").one("click", function(){
    move_prep();
    move("forward");
})

// ask user before leaving, but not if he/she uses the form go to the next page.

var ask_before_leaving = function (e) {
    // Cancel the event
    e.preventDefault(); // If you prevent default behavior in Mozilla Firefox prompt will always be shown
    // Chrome requires returnValue to be set
    e.returnValue = '';
  };

var allow_leaving = function() {
    window.removeEventListener("beforeunload", ask_before_leaving)
}

window.addEventListener('beforeunload', ask_before_leaving);
$("#form").submit(allow_leaving);


// prevent users from submitting form via enter
$(document).on("keydown", ":input:not(textarea):not(:submit)", function(event) {
    if (event.key == "Enter") {
        event.preventDefault();
    }
});
  

// Responsive support for choice elements (switch to vertical layout on XS screens)
const responsive_adjustments = function () {
    if (innerWidth <= 576) {
        $(".choice-button-group.btn-group").addClass("btn-group-vertical changed");
        $(".choice-button-group.btn-group").removeClass("btn-group");

        $(".choice-button-bar.btn-group").addClass("btn-group-vertical changed-bar choice-button-group");
        $(".choice-button-bar.btn-group").removeClass("btn-group choice-button-bar");
        
        $(".form-check-inline").addClass("changed");
        $(".form-check-inline").removeClass("form-check-inline");

    } else {

        $(".choice-button-group.changed").addClass("btn-group");
        $(".choice-button-group.changed").removeClass("btn-group-vertical changed");

        $(".choice-button-group.changed-bar").addClass("btn-group choice-button-bar");
        $(".choice-button-group.changed-bar").removeClass("btn-group-vertical changed-bar choice-button-group");

        $(".form-check.changed").addClass("form-check-inline");
        $(".form-check.changed").removeClass("changed")
    };
}

$(window).resize(responsive_adjustments);
$(document).ready(responsive_adjustments);
$(function(){$(".brand-link").tooltip({html: true, placement: 'right'});}); // initialize tooltip