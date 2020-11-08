$(document).ready(function () {
    res = $('#screen_resolution').val(); 
    $.post('/save', {screen_resolution: res, javascript_active: true})
});