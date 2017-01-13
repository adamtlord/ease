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
        weekStart: 1,
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