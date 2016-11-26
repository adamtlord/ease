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

});