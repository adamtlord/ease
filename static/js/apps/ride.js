$(function(){
    $('#id_start, #id_destination').select2({
        theme: 'bootstrap'
    });
    $('input.fieldset-toggle').on('change', function(){
        if($(this).is(":checked")){
            $('fieldset.' + this.name).slideDown('fast');
            $('select[name="' + $(this).attr('rel') + '"]').attr('disabled','disabled');
        }else{
            $('fieldset.' + this.name).slideUp('fast');
            $('select[name="' + $(this).attr('rel') + '"]').removeAttr('disabled');
        }
    });
    $('.datetime input').datetimepicker({
        icons: {
            time: "fa fa-clock-o",
            date: "fa fa-calendar",
            up: "fa fa-arrow-up",
            down: "fa fa-arrow-down"
        }
    }).on("dp.change", function (e) {
        $('#' + this.getAttribute('rel')).val(moment(e.date).format('YYYY-MM-DD HH:MM:SS'));
    });
});