/* global moment */

$(function() {
    function start() {
        if ($('#id_start_date').val()) {
            return moment($('#id_start_date').val());
        } else {
            return moment().startOf('month');
        }
    }

    function end() {
        if ($('#id_end_date').val()) {
            return moment($('#id_end_date').val());
        } else {
            return moment().endOf('month');
        }
    }

    function cb(start, end) {
        $('#range-picker').val(start.format('MM/DD/YYYY') + ' - ' + end.format('MM/DD/YYYY'));
        $('#id_start_date').val(start.format('YYYY-MM-DD'));
        $('#id_end_date').val(end.format('YYYY-MM-DD'));
    }
    $('#range-picker').daterangepicker({
        startDate: start,
        endDate: end,
        autoApply: true,
        ranges: {
            'Today': [moment(), moment()],
            'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
            'Last 7 Days': [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        }
    }, cb);
    cb(start(), end());
});