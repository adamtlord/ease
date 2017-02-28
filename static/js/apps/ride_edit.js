/* global Clipboard, confirm */

$(function(){

    $(".datetime-start input, .datetime-end input").datetimepicker({
        autoclose: true,
        fontAwesome: true,
        format: "mm/dd/yyyy H:ii P",
        linkField: "id_start_date",
        linkFormat: "yyyy-mm-dd hh:ii:ss",
        showMeridian: true,
        startView: 2,
        todayHighlight: true,
        weekStart: 0,
    });

    $('.input-group-btn').tooltip({
        placement: 'bottom',
        trigger: 'manual'
    });

    $('#id_start, #id_destination').select2({
        theme: 'bootstrap'
    });

    $('a.cancel-ride').on('click', function() {
        return confirm('Are you sure you want to cancel and permanently delete this ride?');
    });

    var clipboard = new Clipboard('.copybtn');

    clipboard.on('success', function(e) {
        var el = $(e.trigger).parent();
        el.tooltip('show');
        setTimeout(function(){
            el.tooltip('hide');
        }, 1250);

        e.clearSelection();
    });

});