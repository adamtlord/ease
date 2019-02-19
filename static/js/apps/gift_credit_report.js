/* global moment */

$(function() {
    function start() {
        if ($('#id_start_date').val()) {
            return moment($('#id_start_date').val());
        } else {
            return moment("12-01-2016", "MM-DD-YYYY");
        }
    }

    function end() {
        if ($('#id_end_date').val()) {
            return moment($('#id_end_date').val());
        } else {
            return moment();
        }
    }

    function cb(start, end) {
        $('#range-picker').val(start.format('MM/DD/YYYY') + ' - ' + end.format('MM/DD/YYYY'));
        $('#id_start_date').val(start.format('YYYY-MM-DD'));
        $('#id_end_date').val(end.format('YYYY-MM-DD'));
    }
    $('#range-picker').daterangepicker({
        startDate: start(),
        endDate: end(),
        autoApply: true,
        ranges: {
            'All Time': [moment("12-01-2016", "MM-DD-YYYY"), moment()],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'Last 7 Days': [moment().subtract(6, 'days'), moment()]
        }
    }, cb);
    cb(start(), end());
});