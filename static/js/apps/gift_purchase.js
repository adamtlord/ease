function copyNamesToGift(){
    $('#id_first_name, #id_last_name').each(function(){
        $('#id_gift-' + this.attributes.name.value).val(this.value);
    });
}
$(function(){
    $('#id_first_name, #id_last_name').on('blur', function(){
        copyNamesToGift();
    });
    copyNamesToGift();
});