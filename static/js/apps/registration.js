$(function(){

    function toggleOtherSource(val){
        if(val === 'OTHER'){
            $('#source_other').slideDown();
        }else {
            $('#source_other').slideUp();
        }
    }

    function toggleSendUpdates(val){
        if(val === '1' || val === '2'){
            $('#lovedone_fields').slideDown();
        }else {
            $('#lovedone_fields').slideUp();
        }
    }

    $('#id_reg-source').on('change', function(){
        toggleOtherSource(this.value);
    });

    $('#id_send_updates').on('change', function(){
        toggleSendUpdates(this.value);
    });

    toggleOtherSource($('#id_reg-source option:selected').val());
    toggleSendUpdates($('#id_send_updates option:selected').val());
});