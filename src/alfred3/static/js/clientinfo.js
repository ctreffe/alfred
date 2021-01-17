$(document).ready(function () {
    const screen_resolution = screen.width.toString() + "x" + screen.height.toString();
    const inner_resolution = innerWidth.toString() + "x" + innerHeight.toString();
    var ua = detect.parse(navigator.userAgent);
    
    var info = {
        client_resolution_screen: screen_resolution,
        client_resolution_inner: inner_resolution,
        client_referrer: document.referrer,
        client_javascript_active: true,
        client_device_type: ua.device.type,
        client_device_manufacturer: ua.device.manufacturer,
        client_device_family: ua.device.family,
        client_browser: ua.browser.name,
        client_os_family: ua.os.family,
        client_os_name: ua.os.name,
        client_os_version: ua.os.version,
    }

    $.post('/callable/clientinfo', info)
});