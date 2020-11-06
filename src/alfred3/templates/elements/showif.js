$(document).ready(function() {

    const element = $("#elid-{{ element }}")
    
    {% for target, value in showif.items() %}

    $("#{{ target }}").keyup(
      function () {
        
        if (this.value == "{{ value }}") {
          element.removeClass("hide")
        } else if (element.is(":visible")) {
          element.addClass("hide")
        }
      }
    );

    {% endfor %}
  
  });
  