$(function(){
    // Internal Functions
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
    // Event Binding
    $('#id_reg-source').on('change', function(){
        toggleOtherSource(this.value);
    });

    $('#id_send_updates').on('change', function(){
        toggleSendUpdates(this.value);
    });
    // On Load
    toggleOtherSource($('#id_reg-source option:selected').val());
    toggleSendUpdates($('#id_send_updates option:selected').val());
    // Input masking
    $('.phone-mask input').mask('000-000-0000');
    $('.zip-mask input').mask('00000-0000');
});