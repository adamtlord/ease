$(function(){

    $(".datetime-start input").datetimepicker({
        format: "mm/dd/yyyy H:ii P",
        showMeridian: true,
        autoclose: true,
        todayHighlight: true,
        weekStart: 1,
        startView: 1,
        linkField: "id_start_date",
        linkFormat: "yyyy-mm-dd hh:ii:ss"
    });

    $(".datetime-end input").datetimepicker({
        format: "mm/dd/yyyy HH:ii P",
        showMeridian: true,
        autoclose: true,
        todayHighlight: true,
        weekStart: 1,
        startView: 1,
        linkField: "id_end_date",
        linkFormat: "yyyy-mm-dd hh:ii:ss"
    });

    $('.input-group-btn').tooltip({
        placement: 'bottom',
        trigger: 'manual'
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