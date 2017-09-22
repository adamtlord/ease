$(function(){

    $(".datetime-start input, .datetime-start .input").datetimepicker({
        autoclose: true,
        fontAwesome: true,
        format: "mm/dd/yyyy H:ii P",
        linkField: "id_start_date",
        linkFormat: "yyyy-mm-dd hh:ii:ss",
        showMeridian: true,
        startView: 2,
        todayHighlight: true,
        weekStart: 0,
    }).on('changeDate', function(){
        $('#schedule_ride_modal input[name="schedule"]').removeAttr('disabled');
    });
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

});