$(function(){
    $('#id_first_name, #id_last_name').on('blur', function(){
        $('#id_gift-' + this.attributes.name.value).val(this.value);
    });
});