 $(function(){
    $('#viewRideModal').on('show.bs.modal', function (e) {
        var rideID = $(e.relatedTarget).data('rideid');
        var modal = $(this).find('.modal-content');
        $.get('/concierge/ride/'+rideID+'/detail-modal/', function(response){
            modal.html(response);
        });
    });
});