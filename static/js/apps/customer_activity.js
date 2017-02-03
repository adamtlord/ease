$(function(){

    function toggleOtherSource(val) {
        if (val === 'OTHER') {
            $('#type_other').slideDown();
        } else {
            $('#type_other').slideUp();
        }
    }

    $('#id_type').on('change', function() {
        toggleOtherSource(this.value);
    });

    toggleOtherSource($('#id_type option:selected').val());

    $(".activity-date input").datetimepicker({
        autoclose: true,
        fontAwesome: true,
        format: "mm/dd/yyyy H:ii P",
        linkField: "id_date",
        linkFormat: "yyyy-mm-dd hh:ii:ss",
        showMeridian: true,
        startView: 1,
        todayHighlight: true,
        weekStart: 0,
    });
});